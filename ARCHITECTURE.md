## Voice/Audio Transcription Pipeline

Audio files can be transcribed (speech-to-text) and fed into the chat workflow by leveraging the browser session.

**How it works:**
- Audio file is uploaded via the browser with user authentication (session cookies reused)
- If the file is not natively supported (e.g., `.mp3`, `.wav`, etc.), it is auto-converted to `.webm`/opus using ffmpeg/ffprobe before upload
- Speech-to-text/transcription uses OpenAI's web interface, returning the text to be sent (or just shown, if using `transcribe`)
- Works identically for both CLI commands and interactive terminal sessions

**Requirements:** ffmpeg and ffprobe must be installed and on the system PATH.

**Flow:**
1. CLI parses `--voice-file`/`transcribe` commands
2. Input file checked/converted to .webm as needed
3. Browser automation uploads the file to ChatGPT (authenticated)
4. Transcript is extracted from the web page
5. Transcript is either sent as a message or shown directly (per user command)

See `chatgpt chat --voice-file ...` and `/voicefile ...` examples in the README and USAGE guides for details.