import os
import subprocess

def extract_audio(video_path, output_audio_path):
    if not os.path.exists(video_path):
        raise FileExistsError(f"Video not Found:{video_path}")
    command=[
        "ffmpeg",
        "-y",
        "-i",video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar","16000",
        "-ac","1",
        output_audio_path
    ]
    subprocess.run(command,check=True)
    return output_audio_path

def merge_video(video_path, dubbed_audio_path, output_video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    if not os.path.exists(dubbed_audio_path):
        raise FileNotFoundError(f"Dubbed audio not found: {dubbed_audio_path}")
    
    command=["ffmpeg",
            "-y",       # Overwrite output if it exists
            "-i",video_path,   # Original video
            "-i",dubbed_audio_path,    # Bangla audio

            "-map", "0:v",     # Take video from original
            "-map", "1:a",     # Take audio from dubbed audio
            "-map", "0:s?",    # Take subtitles from original if they exist

            "-c:v", "copy",    # Don't re-encode video
            "-c:a", "aac",     # Encode audio to AAC
            "-shortest",       # Stop when shortest stream ends

            output_video_path
    ]
    subprocess.run(command,check=True)
    return output_video_path