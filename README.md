
# AI Video Dubbing System

An AI-powered video dubbing application that automatically converts English videos into Bangla dubbed videos using Artificial Intelligence.

## 🚀 Features

### 🎬 Video Processing

- Download video files and process locally
- Extract audio from video
- Merge generated Bangla audio with original video
- Preserve original video quality
- Automatic temporary file cleanup

### 📝 Speech Recognition

- Uses Whisper AI for speech-to-text conversion
- Generates timestamp-based segments

### 🌐 AI Translation

- Converts English speech into natural Bangladeshi Bangla
- Uses Large Language Models (LLMs)
- Batch translation support for faster processing
- Optimized for conversational dubbing style

### 🔊 AI Voice Generation

- Generates Bangla speech using Text-to-Speech
- Processes each translated segment individually
- Checks generated audio duration
- Adjusts audio timing to match original speech

### ⚡ Performance Optimization

- Batch AI translation for faster processing
- Optimized Whisper inference using CPU acceleration
- Audio duration checking and adjustment
- Real-time progress tracking
- Automatic temporary file cleanup

### 🌐 Web Interface

- Flask-based web application
- Upload video
- Real-time processing progress
- Download completed dubbed video

---

# 🏗️ System Architecture

```
                User Uploads Video
                         |
                         ↓
                Flask Web Application
                         |
                         ↓
                Extract Audio (FFmpeg)
                         |
                         ↓
                Speech Recognition
               (Faster Whisper AI)
                         |
                         ↓
               English Speech Segments
                  + Timestamps
                         |
                         ↓
               AI Translation Engine
               (LLM API - NVIDIA)
                         |
                         ↓
              Natural Bangla Translation
                         |
                         ↓
             Bangla Text To Speech
                      (EDGE TTS)
                         |
                         ↓
           Audio Duration Analysis & Adjustment

        ┌─────────────────────────────┐
        │ Compare Original Segment    │
        │ Duration vs Bangla Audio    │
        │                             │
        │ If Bangla > Original:       │
        │   → Shorten translation     │
        │   → Speed adjust audio      │
        │                             │
        │ If Bangla < Original:       │
        │   → Adjust timing           │
        └─────────────────────────────┘
                         |
                         ↓
              Combine All Dubbed Segments
                         |
                         ↓
              Merge Audio + Video
                    (FFmpeg)
                         |
                         ↓
              Final Bangla Dubbed Video
```

---

# 🛠️ Technologies Used

## Programming Language

- Python 3.11+

## Backend

- Flask

## AI Models

### Speech Recognition

- Faster Whisper

### Translation

- Large Language Models through NVIDIA API

Example models:

- gpt-oss-120b
- Llama 3.3 70B
- Other compatible LLM models

### Text To Speech

- Google Text-to-Speech (EDGE TTS)

## Video Processing

- FFmpeg
- Pydub

## Database

- MySQL (optional)

---

# ▶️ Running The Application

Start Flask server:

```bash
python app.py
```

Open browser:

```
http://127.0.0.1:5000
```

---

# 🔄 Processing Pipeline

1. Upload video
2. Extract audio
3. Detect speech segments
4. Convert speech → text
5. Translate English → Bangla
6. Generate Bangla voice
7. Adjust audio duration
8. Combine audio with video
9. Generate final dubbed video

---

# 📊 Progress Tracking

The application provides real-time progress:

Example:

```
10% Downloading video...

30% Transcribing audio...

50% Translating segments 45/120

75% Creating Bangla voice...

90% Merging video...

100% Completed!
```

---

# 🎯 Current Limitations

- Voice cloning is not implemented yet
- edge_tts voice quality is limited
- Lip synchronization is not included
- Long videos require more processing time
- Translation quality depends on selected AI model

---

# 🚀 Future Improvements

## Voice & Audio

- Add AI voice cloning
- Speaker identification
- Emotion-aware dubbing

## Video Synchronization

- Add lip-sync technology
- Automatic mouth movement matching

## AI Improvements

- Better translation models
- Context-aware subtitle translation
- Character-specific voices

## Deployment

- Cloud deployment
- GPU acceleration
- User authentication
- Video history database

---

# 🧠 AI Pipeline Goals

The goal of this project is to build an automated AI dubbing platform capable of converting online educational videos, documentaries, and entertainment content into Bangla language while maintaining natural speech timing and quality.

---

# 👨‍💻 Developer

**Horish Das Priyo**

Computer Science Student
AI & Software Development Enthusiast

---

# 📜 License

This project is for educational and research purposes.
