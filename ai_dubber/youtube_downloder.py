import yt_dlp
import os

def download_video(url, outlput_path):
    os.mkdir(os.path.dirname(outlput_path),exist_ok=True)

    ydl_opts={
        "format":"bestvideo+bestaudio/best",
        "merge_output_format":"mp4",
        "outtmpl":outlput_path,
        "quiet":False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return outlput_path