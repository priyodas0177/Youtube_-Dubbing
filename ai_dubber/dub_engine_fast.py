import os #Used for working with files and folders.
from faster_whisper import WhisperModel #Speech to Text converter
from openai import OpenAI #Text Translation
from gtts import gTTS #Google Text-to-Speech.
from pydub import AudioSegment #used for audio manipulation and processing (merge audio,cut audio, add silence, change speed).



# here copy and past key 
API_KEY=("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")
client=OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

whisper=WhisperModel("small", device="cpu",compute_type="int8")


def speed_change(sound, speed=1.0):
    altered = sound._spawn( #spawn is create a new audio segment
        sound.raw_data,
        overrides={
            "frame_rate": int(sound.frame_rate* speed)
        }
    )
    return altered.set_frame_rate(sound.frame_rate)

def translate_batch(texts, batch_size=20):
    translated = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        print(f"Translating batch {start+1} - {start+len(batch)}")

        numbered = "\n".join(
            f"{i+1}. {t}" for i, t in enumerate(batch)
        )

        try:
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """
You are a professional Bengali dubbing translator.

Translate every numbered sentence into natural Bangla.

Rules:
- Keep the numbering exactly the same.
- Do not skip any number.
- Do not merge sentences.
- Return only numbered Bangla translations.
"""
                    },
                    {
                        "role": "user",
                        "content": numbered
                    }
                ]
            )

            output = response.choices[0].message.content.strip()

            lines = output.split("\n")

            for line in lines:
                if "." in line:
                    translated.append(line.split(".", 1)[1].strip())

        except Exception as e:
            print(e)
            translated.extend(batch)

    return translated





def create_dub(video_audio, output_audio, beam_size=5):
    segments, info =whisper.transcribe( #audio divide into segments
        video_audio,
        beam_size=beam_size,
        vad_filter=False,
        condition_on_previous_text=True,
        language="en"
    )
    segments=list(segments)
    texts=[]
    for seg in segments:
        texts.append(seg.text.strip())

    bangla_texts=translate_batch(texts)
    print(f"total segments: {len(segments)}")
    print(f"translations: {len(bangla_texts)}")

    for i, seg in enumerate(segments):
        print(
            f"{i+1}: {seg.start:.2f} -> {seg.end:.2f} "
            f"({seg.end-seg.start:.2f}s) | {repr(seg.text)}"
        )

    original=AudioSegment.from_file(video_audio) #load original audio
    final=AudioSegment.silent(duration=len(original)) #create empty audio We'll place Bangla speech onto this timeline.

    temp_dir="temp" #Stores temporary MP3 files.
    os.makedirs(temp_dir,exist_ok=True)

    for i, seg in enumerate(segments):
        start=int(seg.start*1000)
        end=int(seg.end*1000)
        duration=end-start

        text=seg.text.strip() #remove extra spaces from text
        if not text:
            continue

        if i< len(bangla_texts):
            bangla=bangla_texts[i]
        else:
            bangla=text

        tts_file=f"{temp_dir}/segment_{i}.mp3" #create tts files

        gtts=gTTS( #genarate bangla voice 
            text=bangla,
            lang="bn",
            slow=False
        )
        gtts.save(tts_file)

        audio=AudioSegment.from_file(tts_file)
        original_duration=max(duration/1000, 0.1)
        tts_duration=len(audio)/1000

        ratio=tts_duration/original_duration


# If Bangla becomes much longer,
# ask GPT to shorten it while preserving meaning.
        attempt=0
        max_attempts=0

        while ratio>1.2 and attempt < max_attempts:
            try:
                short_res=client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[
                        {"role":"system",
                         "content":f"""
You are a professional Bengali dubbing editor.

Rewrite the following Bangla sentence for AI voice dubbing.
Rules:
1. Preserve the exact meaning.
2. Keep all important information.
3. Remove unnecessary filler words.
4. Use shorter, natural spoken Bangla.
5. Make it sound like a real Bangladeshi speaker.
6. Avoid formal or bookish language.
7. Keep the same emotion and tone. 
8. Must fit approximately {original_duration:.1f} seconds."""},
                    {"role":"user","content":bangla}
                    ]
                )
                shorter_bangla=(short_res.choices[0].message.content.strip())

                gtts=gTTS(
                    text=shorter_bangla,
                    lang="bn",
                    slow=False
                )
                gtts.save(tts_file)

                audio=AudioSegment.from_file(tts_file)

                tts_duration=len(audio)/1000
                ratio=tts_duration/original_duration
                bangla=shorter_bangla

            except Exception as e:
                print(f"Shortening failed {e}")
                break
            attempt+=1

        target_ms=duration
        if len(audio)>target_ms: #if original audio is 3s and generate bangala is 4s then going to if block
            speed_factor=len(audio)/target_ms
            speed_factor=min(speed_factor,1.20)

            audio=speed_change(audio,speed=speed_factor)

        if len(audio)<target_ms:
            audio+=AudioSegment.silent(target_ms-len(audio))

        audio=audio[:target_ms]

        final=final.overlay(audio,position=start)
        os.remove(tts_file)

    final.export(output_audio,format="wav")
    return output_audio



        


