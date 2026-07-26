import os
import yt_dlp

def download_video(url, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_path,
        "quiet": False,
        
        # 1. Clear out stale signature caches that trigger bot detection
        "rm_cachedir": True,  
        
        # 2. Tell yt-dlp to read your browser cookies to pass the bot check.
        # Options: 'chrome', 'firefox', 'safari', 'edge', 'opera', 'brave'
        "cookiesfrombrowser": ("chrome",),  # 👈 Make sure you are logged into YouTube on this browser!
        
        # 3. Use standard player clients (avoiding broken mobile clients)
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "-android_sdkless"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return output_path