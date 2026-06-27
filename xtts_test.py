from faster_whisper import WhisperModel
from openai import OpenAI
from TTS.api import TTS
from pydub import AudioSegment
import os

# ==========================
# CONFIG
# ==========================

API_KEY = "YOUR_OPENROUTER_API_KEY"

AUDIO_INPUT = "audio.wav"
OUTPUT_AUDIO = "dub.wav"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ==========================
# LOAD XTTS MODEL (IMPORTANT)
# ==========================

print("Loading XTTS v2...")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# OPTIONAL: voice cloning file (recommended)
# speaker_wav = "speaker.wav"
speaker_wav = None

# ==========================
# WHISPER MODEL
# ==========================

print("Loading Whisper...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    AUDIO_INPUT,
    beam_size=5
)

segments = list(segments)

# ==========================
# ORIGINAL AUDIO
# ==========================

original_audio = AudioSegment.from_file(AUDIO_INPUT)

final_output = AudioSegment.silent(duration=len(original_audio))

# ==========================
# PROCESS SEGMENTS
# ==========================

for i, segment in enumerate(segments):

    start_time = int(segment.start * 1000)
    end_time = int(segment.end * 1000)
    duration = end_time - start_time

    text = segment.text.strip()

    if not text:
        continue

    print("\n------------------")
    print(f"Segment {i}")
    print(text)

    # ==========================
    # TRANSLATION (OPENROUTER)
    # ==========================

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate to natural spoken Bangla for dubbing. "
                        "Keep sentence short and natural."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        translated = response.choices[0].message.content.strip()

    except Exception as e:
        print("Translation error:", e)
        translated = text

    print("Bangla:", translated)

    # ==========================
    # XTTS GENERATION (NO ROBOTIC SOUND)
    # ==========================

    tts_file = f"tts_{i}.wav"

    try:
        if speaker_wav:
            tts.tts_to_file(
                text=translated,
                speaker_wav=speaker_wav,
                language="bn",
                file_path=tts_file
            )
        else:
            tts.tts_to_file(
                text=translated,
                language="bn",
                file_path=tts_file
            )

    except Exception as e:
        print("TTS error:", e)
        continue

    # ==========================
    # LOAD AUDIO
    # ==========================

    dub_audio = AudioSegment.from_file(tts_file)

    # ==========================
    # TIMING FIX (NO SPEED DISTORTION)
    # ==========================

    if len(dub_audio) < duration:
        dub_audio += AudioSegment.silent(duration - len(dub_audio))
    else:
        dub_audio = dub_audio[:duration]

    # ==========================
    # OVERLAY
    # ==========================

    final_output = final_output.overlay(
        dub_audio,
        position=start_time
    )

    os.remove(tts_file)

# ==========================
# EXPORT
# ==========================

print("\nExporting...")

final_output.export(
    OUTPUT_AUDIO,
    format="wav"
)

print("DONE:", OUTPUT_AUDIO)