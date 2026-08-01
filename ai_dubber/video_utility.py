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

    command = [
        "ffmpeg",
        "-y",

        "-i", video_path,
        "-i", dubbed_audio_path,

        "-map", "0:v",
        "-map", "1:a",

        "-map", "0:s?",

        "-c:v", "copy",

        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",

        "-shortest",

        output_video_path
    ]

    subprocess.run(command, check=True)

    return output_video_path