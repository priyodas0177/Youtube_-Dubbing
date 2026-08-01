import os, time, re, uuid, json, threading
import asyncio
from faster_whisper import WhisperModel
import edge_tts
from pydub import AudioSegment
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# client = OpenAI(
#     base_url="https://models.inference.ai.azure.com",
#     api_key=GITHUB_TOKEN,
#     timeout=60,
#     max_retries=2
# )

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
    timeout=90,
    max_retries=2
)


# Use 'cpu' or 'cuda' explicitly. 'auto' can sometimes spend time autodetecting.
whisper = WhisperModel("small", device="cpu", compute_type="int8")

SHORTEN_WORKERS=1
SHORTEN_SEMAPHORE=None

TTS_WORKERS = 3
TTS_SEMAPHORE = None

progress_lock = None
completed_segments = 0

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
                voice="bn-BD-NabanitaNeural",
                rate="-5%",
                pitch="+0Hz"
            )

            await asyncio.wait_for(
                communicate.save(output_file),
                timeout=30
            )

            return

        except Exception as e:
            print(f"TTS attempt {attempt+1} failed: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)

            else:
                raise



SHORTEN_PROMPT = """

    You are an expert Bengali dubbing editor.

    Your task is to rewrite a Bangla sentence so it fits a limited speaking time for AI dubbing.

    Rules:

    1. Preserve the original meaning.
    2. Never remove important information.
    3. Prefer shorter words over longer ones.
    4. Remove unnecessary filler words.
    5. Use natural conversational Bangladeshi Bangla.
    6. Avoid formal, written, or literary expressions.
    7. Keep proper nouns, names, numbers, and technical terms unchanged.
    8. The sentence should comfortably fit approximately {duration:.1f} seconds of speech.
    9. Return ONLY the rewritten Bangla sentence.
"""

# We make the translator helper helper function
def shorten_translation(bangla, original_duration, retries=3):

    prompt = SHORTEN_PROMPT.format(
        duration=original_duration
    )

    for attempt in range(retries):

        try:

   
            response = client.chat.completions.create(

                model="openai/gpt-oss-120b",
                

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

                temperature=0.15,
                top_p=0.85,
                max_tokens=4096
            )

            result = response.choices[0].message.content

            if result:
                result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
                if result:
                    return result


        except Exception as e:

            print(
                f"Shorten attempt {attempt + 1} failed: {e}"
            )

            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))


    print("Shortening failed, using original Bangla.")
    return bangla


def merge_segments(segments, max_duration=8):

    merged = []

    current_text = ""
    start_time = None
    end_time = None


    for seg in segments:

        if start_time is None:
            start_time = seg.start

        current_text += " " + seg.text.strip()

        end_time = seg.end


        duration = end_time - start_time


        if duration >= max_duration:

            merged.append({
                "text": current_text.strip(),
                "start": start_time,
                "end": end_time
            })

            current_text = ""
            start_time = None
            end_time = None


    # remaining segment
    if current_text:

        merged.append({
            "text": current_text.strip(),
            "start": start_time,
            "end": end_time
        })


    return merged

def _translate_batch_once(texts, start_index):
    

    print(f"[{time.strftime('%H:%M:%S')}] START request {start_index+1}-{start_index+len(texts)}")
    print("Thread:", threading.current_thread().name)

    
    # print(
    #     f"START TRANSLATION {start_index+1}-{start_index+len(texts)}"
    # )

    prompt = """
                You are an expert Bengali dubbing translator.

                Your job is to translate English subtitle segments into natural spoken Bangladeshi Bangla suitable for AI voice dubbing.

                STRICT RULES:

                1. Translate EVERY segment.
                2. Output EXACTLY one Bangla translation for each input segment.
                3. Never merge, split, reorder, or skip segments.
                4. Preserve the original meaning, tone, and emotion.
                5. Write natural spoken Bangladeshi Bangla, not literal textbook Bangla.
                6. Keep the translation concise so its speaking duration is close to the original English.
                7. Never add information that is not present in the source.
                8. Keep names of people, companies, products, organizations, websites, software, programming languages, APIs, and AI models unchanged.
                9. Keep technical terms such as GPT, ChatGPT, Gemini, Claude, API, OpenRouter, Python, JavaScript, NVIDIA, SpaceX, Tesla, Google, Microsoft, Apple, AI, CPU, GPU, Windows, Linux, macOS, YouTube, Facebook, Instagram, Twitter, X, etc. unchanged unless they already have a widely accepted Bangla pronunciation.
                10. Return VALID JSON ONLY.
                11. Do NOT wrap the JSON inside Markdown code fences.
                12. Do NOT explain anything.
                13. Do NOT use numbered keys.
                14. If a sentence is too long, rewrite it naturally using fewer words while preserving the original meaning.
                15. If a proper noun or financial term is unclear, copy it unchanged instead of guessing or translating it.
                16. Never translate stock tickers or financial indexes.

                Return EXACTLY this JSON format:

                {
                "translations": [
                    "translation 1",
                    "translation 2",
                    "translation 3"
                ]
                }
            """

    for i, text in enumerate(texts, start=1):
        prompt += f"""
    SEGMENT_{i}:
    {text}

    """

    print("Before NVIDIA request")
    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            response_format={
                "type":"json_object"
            },

            messages=[
                {
                    "role":"system",
                    "content":prompt
                },
                {
                    "role":"user",
                    "content":"Translate now."
                }
            ],

            temperature=0.15,
            top_p=0.85,
            max_tokens=4096,

            timeout=90
        )
        print("After NVIDIA request")
        print(f"[{time.strftime('%H:%M:%S')}] END request {start_index+1}-{start_index+len(texts)}")

        output = response.choices[0].message.content.strip()
        print(output)

        # remove markdown wrapper
        # output = re.sub(
        #     r"```json|```",
        #     "",
        #     output
        # ).strip()

        # parse JSON
        try:

            data = json.loads(output)

        except Exception as e:

            print("JSON ERROR")
            print(e)

            # extract JSON object if model added explanation
            match = re.search(
                r"\{.*\}",
                output,
                re.DOTALL
            )

            if match:

                try:
                    data = json.loads(match.group())

                except Exception as e:
                    print("JSON extraction failed")
                    print(e)
                    return []

            else:

                print(output)
                return []


        translations = []


        # Case 1:
        # {
        #   "translations":[
        #        "...",
        #        "..."
        #   ]
        # }

        if isinstance(data, dict):

            if "translations" in data:

                translations = data["translations"]


            else:

                # Case 2:
                # {
                # "1":"...",
                # "2":"..."
                # }

                for i in range(1, len(texts)+1):

                    value = data.get(str(i))

                    if value:
                        translations.append(value)



        # Case 3:
        # [
        #   "...",
        #   "..."
        # ]

        elif isinstance(data, list):

            translations = data



        # validate count

        if len(translations) != len(texts):

            print(
                "COUNT ERROR",
                len(translations),
                len(texts)
            )

            print(data)

            return []



        return [
            str(x).strip()
            for x in translations
        ]
                
    except Exception as e:

        print("TRANSLATION ERROR")
        print(type(e).__name__)
        print(e)

        return []


def retry_batch_translation(texts, start_index, retries=0):
    """
    Retries the raw API call + parse (NOT translate_batch, to avoid recursive
    retry-of-retry blowup). Falls back to the original English text if every
    attempt fails, so the pipeline never crashes.
    """
    for attempt in range(retries):
        print(f"Retry attempt ❌ {attempt+1} for batch {start_index+1}-{start_index+len(texts)}")

        translations = _translate_batch_once(texts, start_index)

        if len(translations) == len(texts):
            return translations

        print(f"Retry attempt ❌ {attempt+1} still mismatched: expected {len(texts)}, got {len(translations)}")
        time.sleep(1)

    print(f"Giving up after retries — falling back to English for batch {start_index+1}-{start_index+len(texts)}")
    return list(texts)  # last resort, guaranteed correct length


def translate_batch(texts, start_index):
    translations = _translate_batch_once(texts, start_index)

    if len(translations) != len(texts):
        print(
            f"Translation mismatch: expected {len(texts)}, got {len(translations)} (after sequential parse)"
        )
        translations = retry_batch_translation(texts, start_index)

    print(f"Segments {start_index+1}-{start_index+len(texts)}")
    print("English count:", len(texts))
    print("Bangla count:", len(translations))

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
        print(f"Starting segment {i+1}/{total_segments}")

        start = int(seg["start"] * 1000)
        end = int(seg["end"] * 1000)

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

        while ratio > 1.40 and attempt < 1:

            async with SHORTEN_SEMAPHORE:
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

            speed = min(speed, 1.25)


            audio = speed_change(
                audio,
                speed=speed
            )

        if len(audio) < target_ms:

            audio += AudioSegment.silent(
                target_ms - len(audio)
            )

        #audio = audio[:target_ms]

        if len(audio) > target_ms:
            audio = audio[:target_ms+200]

        audio.export(
            tts_file,
            format="mp3"
        )

        global completed_segments

        async with progress_lock:
            completed_segments += 1
            print(
                f"FINISHED SEGMENT {completed_segments}/{total_segments}"
            )

            if progress_callback:
                progress_callback(
                    completed_segments,
                    total_segments,
                    f"Creating Bangla dub: segment {completed_segments}/{total_segments}"
                )

        return {

            "index": i,

            "start": start,

            "tts_file": tts_file

        }

    except Exception as e:

        print(f"Segment {i} failed: {e}")

        return None

async def create_dub(video_audio, output_audio, beam_size=2, progress_callback=None):
    # 1. Transcribe (Heavy local CPU/GPU bound task)
    global TTS_SEMAPHORE
    TTS_SEMAPHORE = asyncio.Semaphore(TTS_WORKERS)

    global SHORTEN_SEMAPHORE
    SHORTEN_SEMAPHORE = asyncio.Semaphore(SHORTEN_WORKERS)

    global progress_lock
    progress_lock = asyncio.Lock()

    segments, info = whisper.transcribe(
        video_audio,
        beam_size=beam_size,
        vad_filter=False,
        condition_on_previous_text=True,
        language="en",   
    )
    segments = list(segments)

    segments = merge_segments(
        segments,
        max_duration=8
    )

    total_segments = len(segments)

    global completed_segments
    completed_segments = 0

    print(f"Total segments: {total_segments}")
    if progress_callback:
        progress_callback(
            0,
            total_segments,
            f"Creating Bangla dub: 0/{total_segments}"
        )

    temp_dir = os.path.join("temp", str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    # 2. Parallel translation & TTS generation (Huge speedup here!)
    # We create async tasks for all segments and run them concurrently
    tasks = []

    BATCH_SIZE = 10
    translation_results = []

    for batch_start in range(0, total_segments, BATCH_SIZE):

        batch = segments[batch_start:batch_start + BATCH_SIZE]

        english = [s["text"].strip() for s in batch]

        result = await asyncio.to_thread(
            translate_batch,
            english,
            batch_start
        )

        translation_results.append(result)

    

    # Flatten translation batches

    all_translations = []
    for batch in translation_results:

        if len(batch) == 0:
            raise ValueError("One translation batch returned no results.")

        all_translations.extend(batch)

    # Validate translation count
    if len(all_translations) != total_segments:
        raise ValueError(
            f"Final translation mismatch. Expected {total_segments}, got {len(all_translations)}"
        )

    print("\n===== CHECK FOR ENGLISH TRANSLATIONS =====")

    for i, text in enumerate(all_translations):
        TECH_WORDS = [
                "AI",
                "GPT",
                "Gemini",
                "Claude",
                "DeepSeek",
                "DeepSeq",
                "OpenRouter",
                "API",
                "JSON",
                "URL",
                "SDK",
                "Mistral"
            ]


        def contains_real_english(text):

            temp = text

            for word in TECH_WORDS:
                temp = temp.replace(word, "")

            # remove english letters
            english_chars = re.findall(r"[A-Za-z]+", temp)

            return len(english_chars) > 2

        if contains_real_english(text):
            print("⚠️ ENGLISH FOUND")
            print(text)

    print("=========================================\n")


    print("\nCHECK TRANSLATION ALIGNMENT")

    for i in range(total_segments):

        #not needed
        print(f"{i+1}: {segments[i]['text'].strip()}")
        print(f" -> {all_translations[i]}")
        #not needed

    # Check empty translations
    for i, text in enumerate(all_translations):

        if not text.strip():
            print(f"EMPTY TRANSLATION: {i+1}")
            return None
        
    # Create TTS tasks
    for i, seg in enumerate(segments):

        print(f"Creating task for segment {i+1}/{total_segments}")

        tasks.append(
            asyncio.create_task(
                process_single_segment(
                    i,
                    seg,
                    all_translations[i],
                    temp_dir,
                    progress_callback,
                    total_segments
                )
            )
        )

    print("Generating TTS in parallel...")

    processed_segments = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    # Remove failed segments
    processed_segments = [
        p for p in processed_segments
        if isinstance(p, dict)
    ]

    if not processed_segments:
        raise RuntimeError("No TTS segments were generate...")

    # Merge audio
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

    print("FINAL AUDIO PATH:", output_audio)
    print("FINAL AUDIO EXISTS:", os.path.exists(output_audio))

    return output_audio
