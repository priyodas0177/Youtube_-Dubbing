from dub_engine import create_dub
from video_utility import merge_video

create_dub(
    video_audio="input.wav",
    output_audio="bangla.wav"
)

merge_video(
    video_path="video.mp4",
    dubbed_audio_path="bangla.wav",
    output_video_path="dubbing_video.mp4"
)
print("finished ")