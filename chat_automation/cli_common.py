#!/usr/bin/env python3
"""
Shared CLI utilities for chat automation CLIs
"""

import os
import sys
import threading
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple


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
