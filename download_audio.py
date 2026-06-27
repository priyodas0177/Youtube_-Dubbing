from yt_dlp import YoutubeDL

url = "https://www.youtube.com/watch?v=or8AcS6y1xg&t=74s"

ydl_opts = {
    # 1. Select the best audio-only format available
    "format": "bestaudio/best",
    
    # 2. Name the output file (yt-dlp will automatically append .wav)
    "outtmpl": "video1.%(ext)s",
    "noplaylist": True,
    
    # 3. Use post-processors to extract audio and convert it to wav
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "wav",       # Force conversion to WAV
        "preferredquality": "192",     # Optional: sets audio quality
    }],
}

with YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])