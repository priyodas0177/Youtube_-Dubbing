from yt_dlp import YoutubeDL

url = "https://www.youtube.com/watch?v=or8AcS6y1xg&t=74s"

ydl_opts = {
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
    "outtmpl": "video1.%(ext)s",
    "noplaylist": True,
    "merge_output_format": "mp4",  # merges video+audio into mp4
}
with YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])