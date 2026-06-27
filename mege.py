from faster_whisper import WhisperModel
from openai import OpenAI
from gtts import gTTS
from pydub import AudioSegment
import os

# ==========================
# CONFIG
# ==========================


client = OpenAI(  
    api_key="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",
    base_url="https://openrouter.ai/api/v1" 
)

video_audio = "audio.wav"
output_audio = "dub.wav"

# ==========================
# CHECK INPUT AUDIO
# ==========================

if not os.path.exists(video_audio):
    raise FileNotFoundError(f"{video_audio} not found")

print("Loading original audio...")

original_audio = AudioSegment.from_file(video_audio)

print("Original duration:", len(original_audio), "ms")
print("Original dBFS:", original_audio.dBFS)

# ==========================
# WHISPER
# ==========================

print("Loading Whisper...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Transcribing...")

segments, info = model.transcribe(
    video_audio,
    beam_size=5
)

segments = list(segments)

print("Detected segments:", len(segments))

# ==========================
# EMPTY OUTPUT
# ==========================

final_output = AudioSegment.silent(
    duration=len(original_audio)
)

added_segments = 0

# ==========================
# PROCESS SEGMENTS
# ==========================

for i, segment in enumerate(segments):

    start_time = int(segment.start * 1000)
    end_time = int(segment.end * 1000)

    text = segment.text.strip()

    if not text:
        continue

    print("\n--------------------")
    print(f"Segment {i}")
    print(text)

    # ======================
    # TRANSLATE
    # ======================

    try:

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content":
                    (
                        "Translate to natural Bangla. "
                        "Return only Bangla text."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        translated = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        print("Translation error:", e)
        translated = text

    print("Bangla:", translated)

    # ======================
    # TTS
    # ======================

    tts_file = f"tts_{i}.mp3"

    try:

        tts = gTTS(
            text=translated,
            lang="bn",
            slow=False
        )

        tts.save(tts_file)

    except Exception as e:

        print("TTS error:", e)
        continue

    if not os.path.exists(tts_file):
        print("TTS file missing")
        continue

    if os.path.getsize(tts_file) == 0:
        print("TTS file empty")
        continue

    # ======================
    # LOAD TTS AUDIO
    # ======================

    try:

        dub_audio = AudioSegment.from_file(tts_file)

    except Exception as e:

        print("Load audio error:", e)
        continue

    print("TTS duration:", len(dub_audio))

    if len(dub_audio) == 0:
        print("Generated audio is empty")
        continue

    # increase volume slightly
    dub_audio = dub_audio + 8

    original_duration = end_time - start_time

    # trim only
    dub_audio = dub_audio[:original_duration]

    final_output = final_output.overlay(
        dub_audio,
        position=start_time
    )

    added_segments += 1

    os.remove(tts_file)

# ==========================
# EXPORT
# ==========================

print("\nAdded segments:", added_segments)

print("Final audio dBFS:", final_output.dBFS)

final_output.export(
    output_audio,
    format="wav"
)

print("Saved:", output_audio)

# ==========================
# VERIFY OUTPUT
# ==========================

check_audio = AudioSegment.from_file(output_audio)

print("Output duration:", len(check_audio))
print("Output dBFS:", check_audio.dBFS)

print("\nDONE")