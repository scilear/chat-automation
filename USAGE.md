## Audio and Speech-to-Text

Transcribe audio files to text and (optionally) submit the transcript as a chat message—all via your browser session. Useful for recording spoken notes, uploading lectures, or dictation!

### Requirements
- `ffmpeg` and `ffprobe` **must be installed** and available on your path
- Most formats supported: `.webm`, `.mp3`, `.wav`, `.m4a`, `.aac`, `.mp4`, others via ffmpeg conversion

### CLI Examples
**Transcribe *and* send the text as a ChatGPT message:**
```bash
chatgpt chat --voice-file path/to/your_audio.m4a
```

**Transcribe only, without sending (just output the transcript):**
```bash
chatgpt transcribe path/to/audio.mp3 --output transcript.txt
```

### Interactive Mode
You can use these commands during an interactive terminal session:
```text
/voicefile path/to/file.wav        # Transcribe & send
/transcribe path/to/file.mp3       # Transcribe only (show transcript, don't send)
```
*You can also paste these commands while the CLI session is running!*

### Notes
- If your file extension isn’t `.webm`, it will be converted (may take a few seconds; see CLI output for errors).
- Browser session is required (reuses cookies/authentication).
- If ffmpeg is missing, you'll see an error—install it with `apt`, `brew`, or your package manager.

### Troubleshooting
- **Audio not recognized or supported?** Try converting to WAV or MP3 first.
- **ffmpeg missing?** Install with `apt install ffmpeg` (Linux), `brew install ffmpeg` (macOS), or from https://ffmpeg.org/download.html
- **Permission errors or browser not launching?** Browser automation is required; check headless configuration and browser version.

---
