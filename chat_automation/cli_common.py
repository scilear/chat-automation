#!/usr/bin/env python3
"""
Shared CLI utilities for chat automation CLIs
"""

import os
import re
import sys
import threading
import time
import tempfile
import subprocess
import shlex
from pathlib import Path
from typing import List, Optional, Tuple


class Spinner:
    """Simple async-friendly spinner animation"""
    
    def __init__(self, message: str = "Waiting"):
        self.message = message
        self._running = False
        self._thread = None
    
    def _spin(self):
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        idx = 0
        while self._running:
            frame = chars[idx % len(chars)]
            sys.stdout.write(f"\r{frame} {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self
    
    def stop(self, final_msg: str = None):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.2)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()
        if final_msg:
            print(final_msg)


class VoiceRecorder:
    """Record audio and transcribe with faster-whisper (local, free)"""
    
    def __init__(self):
        self.recording_process = None
        self.audio_file = None
        self.model = None
    
    def _load_model(self):
        if self.model is None:
            from faster_whisper import WhisperModel
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
        return self.model
    
    def start_recording(self) -> bool:
        self.audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self.recording_process = subprocess.Popen(
            ["arecord", "-f", "cd", "-t", "wav", self.audio_file.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    
    def stop_recording(self) -> Tuple[str, float]:
        """Stop recording and transcribe. Returns (text, transcribe_time_seconds)"""
        import time as time_module
        
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
            self.recording_process = None
        
        if not self.audio_file:
            return "", 0
        
        audio_path = self.audio_file.name
        self.audio_file = None
        
        try:
            model = self._load_model()
            
            start_time = time_module.time()
            segments, info = model.transcribe(audio_path, beam_size=5)
            transcribe_time = time_module.time() - start_time
            
            os.unlink(audio_path)
            
            text = " ".join(segment.text for segment in segments).strip()
            return text, transcribe_time
            
        except Exception as e:
            print(f"[red]Transcription error: {e}[/red]")
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            return "", 0
    
    def cancel_recording(self):
        if self.recording_process:
            self.recording_process.terminate()
            self.recording_process.wait()
            self.recording_process = None
        if self.audio_file:
            try:
                os.unlink(self.audio_file.name)
            except:
                pass
            self.audio_file = None


def ffmpeg_available() -> bool:
    """Return True if ffmpeg is installed and callable."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def probe_duration_ms(filepath: str) -> Optional[float]:
    """Probe media duration in milliseconds using ffprobe."""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return None
        raw = (proc.stdout or "").strip()
        if not raw:
            return None
        seconds = float(raw)
        if seconds <= 0:
            return None
        return seconds * 1000.0
    except Exception:
        return None


def ensure_webm_opus(input_path: str) -> Tuple[str, Optional[float], bool]:
    """Convert input audio to webm/opus.

    Returns:
        (audio_path, duration_ms, converted)
    """
    path = Path(input_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    if path.suffix.lower() == ".webm":
        duration_ms = probe_duration_ms(str(path))
        return str(path), duration_ms, False

    if not ffmpeg_available():
        raise RuntimeError("ffmpeg is required to convert audio to webm/opus")

    tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    tmp.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "48000",
        "-c:a",
        "libopus",
        "-b:a",
        "64k",
        tmp.name,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        stderr = (proc.stderr or "").strip()
        quoted_cmd = " ".join(shlex.quote(part) for part in cmd)
        raise RuntimeError(f"ffmpeg conversion failed\nCommand: {quoted_cmd}\n{stderr}")

    duration_ms = probe_duration_ms(tmp.name)
    return tmp.name, duration_ms, True


def _detect_silence_midpoints_seconds(
    filepath: str,
    min_silence_seconds: float = 0.5,
    noise_db: int = -35,
) -> List[float]:
    """Detect silence midpoints using ffmpeg silencedetect filter."""
    cmd = [
        "ffmpeg",
        "-i",
        filepath,
        "-af",
        f"silencedetect=noise={noise_db}dB:d={min_silence_seconds}",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stderr = proc.stderr or ""

    start_pattern = re.compile(r"silence_start:\s*([0-9.]+)")
    end_pattern = re.compile(r"silence_end:\s*([0-9.]+)")

    midpoints: List[float] = []
    current_start: Optional[float] = None

    for line in stderr.splitlines():
        start_match = start_pattern.search(line)
        if start_match:
            try:
                current_start = float(start_match.group(1))
            except ValueError:
                current_start = None
            continue

        end_match = end_pattern.search(line)
        if not end_match:
            continue

        try:
            end_time = float(end_match.group(1))
        except ValueError:
            current_start = None
            continue

        start_time = current_start
        if start_time is None:
            start_time = max(0.0, end_time - min_silence_seconds)

        if end_time > start_time:
            midpoints.append((start_time + end_time) / 2.0)

        current_start = None

    return midpoints


def _build_chunk_ranges_seconds(
    duration_seconds: float,
    split_points: List[float],
    max_chunk_seconds: float,
    min_chunk_seconds: float = 45.0,
    lookahead_seconds: float = 25.0,
) -> List[Tuple[float, float]]:
    """Build chunk ranges, preferring to cut on detected silence."""
    if duration_seconds <= max_chunk_seconds:
        return [(0.0, duration_seconds)]

    points = sorted(
        {
            point
            for point in split_points
            if 0.0 < point < duration_seconds
        }
    )

    ranges: List[Tuple[float, float]] = []
    cursor = 0.0

    while duration_seconds - cursor > max_chunk_seconds:
        target = cursor + max_chunk_seconds
        earliest = cursor + min_chunk_seconds

        before = [point for point in points if earliest <= point <= target]
        if before:
            split_at = before[-1]
        else:
            after = [
                point
                for point in points
                if target < point <= min(duration_seconds, target + lookahead_seconds)
            ]
            split_at = after[0] if after else target

        if split_at <= cursor:
            split_at = target

        ranges.append((cursor, split_at))
        cursor = split_at

    if duration_seconds > cursor:
        ranges.append((cursor, duration_seconds))

    if len(ranges) >= 2:
        last_start, last_end = ranges[-1]
        prev_start, prev_end = ranges[-2]
        last_len = last_end - last_start
        prev_len = prev_end - prev_start
        if last_len < 20.0 and (prev_len + last_len) <= (max_chunk_seconds + lookahead_seconds):
            ranges[-2] = (prev_start, last_end)
            ranges.pop()

    return ranges


def prepare_webm_transcription_chunks(
    input_path: str,
    max_chunk_seconds: float = 180.0,
) -> Tuple[List[Tuple[str, Optional[float]]], List[str]]:
    """Prepare webm transcription chunks, splitting long files near silences.

    Returns:
        (chunks, temporary_paths)
        - chunks: list of (filepath, duration_ms)
        - temporary_paths: files that caller should delete when done
    """
    webm_path, duration_ms, converted = ensure_webm_opus(input_path)
    temporary_paths: List[str] = [webm_path] if converted else []

    if not duration_ms or duration_ms <= max_chunk_seconds * 1000.0:
        return [(webm_path, duration_ms)], temporary_paths

    if not ffmpeg_available():
        raise RuntimeError("ffmpeg is required to split long audio files")

    duration_seconds = duration_ms / 1000.0
    silence_points = _detect_silence_midpoints_seconds(webm_path)
    ranges = _build_chunk_ranges_seconds(
        duration_seconds=duration_seconds,
        split_points=silence_points,
        max_chunk_seconds=max_chunk_seconds,
    )

    if len(ranges) <= 1:
        return [(webm_path, duration_ms)], temporary_paths

    chunks: List[Tuple[str, Optional[float]]] = []
    generated_paths: List[str] = []

    try:
        for start_sec, end_sec in ranges:
            part_duration = max(0.1, end_sec - start_sec)
            tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
            tmp.close()

            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{start_sec:.3f}",
                "-i",
                webm_path,
                "-t",
                f"{part_duration:.3f}",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "48000",
                "-c:a",
                "libopus",
                "-b:a",
                "64k",
                tmp.name,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                quoted_cmd = " ".join(shlex.quote(part) for part in cmd)
                raise RuntimeError(f"ffmpeg split failed\nCommand: {quoted_cmd}\n{stderr}")

            generated_paths.append(tmp.name)
            part_duration_ms = probe_duration_ms(tmp.name)
            chunks.append((tmp.name, part_duration_ms))
    except Exception:
        for path in generated_paths:
            try:
                os.unlink(path)
            except Exception:
                pass
        raise

    temporary_paths.extend(generated_paths)
    return chunks, temporary_paths


def parse_persona(message: str) -> Tuple[str, str]:
    """Extract persona name from message if present (/persona_name syntax)
    
    Returns: (persona_name or "", remaining_message)
    """
    if message.startswith("/"):
        parts = message.split(None, 1)
        if len(parts) >= 1:
            persona_name = parts[0][1:]  # Remove leading /
            remaining = parts[1] if len(parts) > 1 else ""
            return persona_name, remaining
    return "", message


def load_persona(persona_name: str, personas_dir: Path = None) -> str:
    """Load persona content from personas/{persona_name}.md"""
    if not persona_name:
        return ""
    if personas_dir is None:
        personas_dir = Path(__file__).parent / "personas"
    persona_file = personas_dir / f"{persona_name}.md"
    if persona_file.exists():
        return persona_file.read_text().strip()
    return ""


def list_personas(personas_dir: Path = None) -> list:
    """List all available personas"""
    if personas_dir is None:
        personas_dir = Path(__file__).parent / "personas"
    
    personas = []
    if personas_dir.exists():
        for f in personas_dir.glob("*.md"):
            content = f.read_text().strip()
            first_line = content.split("\n")[0][:60]
            personas.append({
                "name": f.stem,
                "preview": first_line + "..." if len(first_line) == 60 else first_line
            })
    return sorted(personas, key=lambda x: x["name"])
