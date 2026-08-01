# AI YouTube Bangla Dubbing

## Overview
AI YouTube Bangla Dubbing is a Flask-based web application that automatically downloads a YouTube video, converts English speech to text, translates it into natural Bangla, generates Bangla speech, and merges the new audio with the original video.

## Features
- Download YouTube videos
- Speech-to-Text using Faster-Whisper
- English → Bangla translation using OpenRouter (GPT-4o Mini)
- Bangla Text-to-Speech
- Automatic audio/video merging with FFmpeg
- Progress bar during processing
- Download the final dubbed video

## Tech Stack
- Python
- Flask
- Faster-Whisper
- OpenRouter API
- gTTS / Edge-TTS
- FFmpeg
- yt-dlp
- Pydub

## Project Structure
```text
app.py
dub_engine.py
youtube_downloder.py
video_utility.py
templates/
static/
uploads/
outputs/
temp/
requirements.txt
```

## Installation

```bash
git clone <repository>
cd ai_dubber
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key
FLASK_SECRET_KEY=your_random_secret
```

Run:

```bash
python app.py
```

Open:
http://127.0.0.1:5000

## Pipeline

1. Download YouTube video
2. Extract audio
3. Transcribe with Faster-Whisper
4. Translate using GPT
5. Generate Bangla speech
6. Merge audio with FFmpeg
7. Download dubbed video

## Future Improvements
- Speaker cloning
- Multi-language support
- Subtitle generation
- GPU optimization
- Docker deployment

## Author
Horish Das Priyo
