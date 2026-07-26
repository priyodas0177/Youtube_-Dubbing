import os, time, re 
import asyncio
from faster_whisper import WhisperModel
import edge_tts
from pydub import AudioSegment
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# Use 'cpu' or 'cuda' explicitly. 'auto' can sometimes spend time autodetecting.
whisper = WhisperModel("small", device="auto", compute_type="int8")

TTS_WORKERS = 8
TTS_SEMAPHORE = asyncio.Semaphore(TTS_WORKERS)

def speed_change(sound, speed=1.0):
    altered = sound._spawn(
        sound.raw_data,
        overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return altered.set_frame_rate(sound.frame_rate)


async def edge_tts_generate(text, output_file, retries=3):
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice="bn-BD-NabanitaNeural"
            )

            await communicate.save(output_file)
            return

        except Exception as e:
            print(f"TTS attempt {attempt + 1} failed: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise

MODELS = [
    #"deepseek-ai/deepseek-v4-flash",
    "qwen/qwen3-next-80b-a3b-instruct"
]

SHORTEN_PROMPT = """
You are a professional Bengali dubbing editor.

Rewrite the following Bangla sentence for AI voice dubbing.

Rules:
1. Preserve the exact meaning.
2. Keep all important information.
3. Make it shorter and natural for spoken Bangla.
4. Use everyday Bangladeshi Bangla.
5. Avoid formal or bookish language.
6. The result should fit approximately {duration:.1f} seconds.
7. Return only the rewritten Bangla sentence.
"""

# We make the translator helper helper function
def shorten_translation(bangla, original_duration, retries=2):

    prompt = SHORTEN_PROMPT.format(
        duration=original_duration
    )

    for attempt in range(retries):

        try:

            response = client.chat.completions.create(

                model="qwen/qwen3-next-80b-a3b-instruct",

                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": bangla
                    }
                ],

                temperature=0.3,
                top_p=0.7,
                max_tokens=1024
            )

            result = response.choices[0].message.content

            if result:
                return result.strip()


        except Exception as e:

            print(
                f"Shorten attempt {attempt + 1} failed: {e}"
            )

            if attempt < retries - 1:
                time.sleep(2 ** attempt)


    print("Shortening failed, using original Bangla.")
    return bangla

def translate_batch(texts):

    prompt = "Translate each English sentence into natural spoken Bangla.\n\n"

    for i, text in enumerate(texts):
        prompt += f"{i+1}. {text}\n"


    response = client.chat.completions.create(

        model="qwen/qwen3-next-80b-a3b-instruct",

        messages=[
            {
                "role":"system",
                "content":
                """
You are a professional Bengali dubbing translator.

Rules:
1. Preserve meaning.
2. Natural Bangladeshi spoken Bangla.
3. Do not merge sentences.
4. Keep numbering.
5. Return only translations.
"""
            },
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.3,
        top_p=0.7,
        max_tokens=4096
    )


    output = response.choices[0].message.content.strip()

    translations=[]

    for line in output.split("\n"):

        line = line.strip()

        match = re.match(
            r"^\d+[\.\)]\s*(.*)",
            line
        )

        if match:
            translations.append(
                match.group(1).strip()
            )

    print(
        "English count:",
        len(texts)
    )

    print(
        "Bangla count:",
        len(translations)
    )
    return translations

async def process_single_segment(
    i,
    seg,
    bangla,
    temp_dir,
    progress_callback,
    total_segments
):

    try:

        start = int(seg.start * 1000)
        end = int(seg.end * 1000)

        duration = end - start
        original_duration = max(duration / 1000, 0.1)

        if not bangla.strip():
            return None

        tts_file = os.path.join(
            temp_dir,
            f"segment_{i:04d}.mp3"
        )

        # ---------- First TTS ----------

        async with TTS_SEMAPHORE:
            await edge_tts_generate(
                bangla,
                tts_file
            )

        audio = AudioSegment.from_file(tts_file)

        tts_duration = len(audio) / 1000

        ratio = tts_duration / original_duration

        # ---------- Duration Fix ----------

        attempt = 0

        while ratio > 1.2 and attempt < 1:

            bangla = await asyncio.to_thread(
                shorten_translation,
                bangla,
                original_duration
            )

            async with TTS_SEMAPHORE:
                await edge_tts_generate(
                    bangla,
                    tts_file
                )

            audio = AudioSegment.from_file(
                tts_file
            )

            tts_duration = len(audio) / 1000

            ratio = tts_duration / original_duration

            attempt += 1

        # ---------- Speed Fix ----------

        target_ms = duration

        if len(audio) > target_ms:

            speed = len(audio) / target_ms

            speed = min(speed, 1.20)

            audio = speed_change(
                audio,
                speed=speed
            )

        if len(audio) < target_ms:

            audio += AudioSegment.silent(
                target_ms - len(audio)
            )

        audio = audio[:target_ms]

        audio.export(
            tts_file,
            format="mp3"
        )

        if progress_callback:
            progress_callback(
                i + 1,
                total_segments
            )

        return {

            "index": i,

            "start": start,

            "tts_file": tts_file

        }

    except Exception as e:

        print(f"Segment {i} failed: {e}")

        return None



async def create_dub_async(video_audio, output_audio, beam_size=2, progress_callback=None):
    # 1. Transcribe (Heavy local CPU/GPU bound task)
    segments, info = whisper.transcribe(
        video_audio,
        beam_size=beam_size,
        vad_filter=True,
        condition_on_previous_text=True,
        language="en"
    )
    segments = list(segments)
    total_segments = len(segments)
    print(f"Total segments: {total_segments}")

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    # 2. Parallel translation & TTS generation (Huge speedup here!)
    # We create async tasks for all segments and run them concurrently
    tasks=[]
    BATCH_SIZE = 30

    for batch_start in range(0, total_segments, BATCH_SIZE):

        batch = segments[batch_start:batch_start+BATCH_SIZE]

        english = [
            s.text.strip()
            for s in batch
        ]

        bangla = await asyncio.to_thread(
            translate_batch,
            english
        )

        for offset, seg in enumerate(batch):

            tasks.append(
                asyncio.create_task(
                    process_single_segment(
                        batch_start + offset,
                        seg,
                        bangla[offset] if offset < len(bangla) else english[offset],
                        temp_dir,
                        progress_callback,
                        total_segments
                    )
                )
            )

    
    print("Translating and generating voices in parallel...")
    processed_segments = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    # Filter out empty/skipped segments
    processed_segments = [
        p for p in processed_segments
        if isinstance(p, dict)
        ]

    # 3. Process audio files (Pydub is fast and local, so we do this sequentially)
    original = AudioSegment.from_file(video_audio)

    final = AudioSegment.silent(
        duration=len(original)
    )

    processed_segments.sort(
        key=lambda x: x["index"]
    )

    for item in processed_segments:

        audio = AudioSegment.from_file(
            item["tts_file"]
        )

        final = final.overlay(
            audio,
            position=item["start"]
        )

        try:
            os.remove(item["tts_file"])
        except OSError:
            pass

    final.export(
        output_audio,
        format="wav"
    )

    return output_audio


# Wrapper to run the async dubbing entrypoint from synchronous scripts
def create_dub(*args, **kwargs):
    return asyncio.run(create_dub_async(*args, **kwargs))