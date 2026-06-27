import os
from faster_whisper import WhisperModel
from openai import OpenAI
from gtts import gTTS
from pydub import AudioSegment
from pydub import AudioSegment


# here copy and past key 
API_KEY=("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")

client=OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

whisper=WhisperModel("small", device="cpu",compute_type="int8")


def speed_change(sound, speed=1.0):
    altered = sound._spawn(
        sound.raw_data,
        overrides={
            "frame_rate": int(sound.frame_rate* speed)
        }
    )
    return altered.set_frame_rate(sound.frame_rate)


def create_dub(video_audio, output_audio, beam_size=5):
    segments,_=whisper.transcribe(
        video_audio,
        beam_size=beam_size) #audio divide into segments
    segments=list(segments)

    original=AudioSegment.from_file(video_audio) #load original audio
    final=AudioSegment.silent(duration=len(original)) #create empty audio We'll place Bangla speech onto this timeline.

    temp_dir="temp"
    os.makedirs(temp_dir,exist_ok=True)

    for i, seg in enumerate(segments):
        start=int(seg.start*1000)
        end=int(seg.end*1000)
        duration=end-start

        text=seg.text.strip()
        if not text:
            continue

        try:
            res=client.chat.completions.create( #send request to OpenAI API for translation
                model="openai/gpt-4o-mini",
                messages=[   #First GPT call → Translate English → Natural Bangla.
                    {
                    "role":"system",
                    "content":"""
You are a professional Bengali dubbing translator.
Translate the following English text into natural spoken Bangla.
               
Rules:
1. Preserve the exact meaning.
2. Write as people naturally speak in Bangladesh.
3. Avoid literal word-for-word translation.
4. Use short, conversational sentences.
5. Keep the original emotion and tone.
6. Make it suitable for voice narration and dubbing.
7. Do not use overly formal or bookish Bangla.
8. Do not add or remove information unless necessary for natural speech.
9. Return only the Bangla translation.
                    """
                    },
                    {"role":"user","content":text}
                ]
                #Hello everyone welcome to my channel -> gpt return সবাইকে আমার চ্যানেলে স্বাগতম।
            )
            bangla=res.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Translation failed {e}")
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
        max_attempts=3

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
        if len(audio)>target_ms:
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



        


