from flask import Flask, jsonify, render_template, request, send_file, flash, redirect
import os, asyncio
import uuid
from threading import Thread
from dotenv import load_dotenv
from youtube_downloder import download_video
from dub_engine import create_dub
from video_utility import extract_audio, merge_video

load_dotenv()  # Load environment variables from .env file
app=Flask(__name__)
app.secret_key=os.getenv("FLASK_SECRET_KEY")

UPLOAD_FOLDER="uploads"
OUTPUT_FOLDER="outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress = {
    "current": 0,
    "total": 0,
    "message": "Waiting...",
    "percent": 0,
    "finished": False,
    "filename": ""
}


def update_progress(current, total, message=""):

    print("UPDATE:", current, total, message)

    progress["current"] = current
    progress["total"] = total

    if message:
        progress["message"] = message
    else:
        progress["message"] = f"Processing segment {current}/{total}"

    if total > 0:
        progress["percent"] = 30 + int((current / total) * 60)

def run_dubbing(url, video_path, audio_path, bangla_audio, output_video):

    global progress

    try:

        # Download
        progress["percent"] = 5
        progress["message"] = "Downloading video..."
        download_video(url, video_path)

        # Extract audio
        progress["percent"] = 20
        progress["message"] = "Extracting audio..."
        extract_audio(video_path, audio_path)

        # Dub
        progress["percent"] = 30
        progress["message"] = "Creating Bangla dub..."
        progress["current"] = 0
        progress["total"] = "Preparing..."

        asyncio.run(
            create_dub(
                video_audio=audio_path,
                output_audio=bangla_audio,
                progress_callback=update_progress
                )

        )
        

        # Merge
        progress["percent"] = 92
        progress["message"] = "Merging video..."

        merge_video(
            video_path,
            bangla_audio,
            output_video
        )


        # Complete
        progress["percent"] = 100
        progress["current"] = progress["total"]
        progress["message"] = "Finished"
        progress["finished"] = True
        progress["filename"] = os.path.basename(output_video)


    finally:
        print("Cleaning up temporary files...")
     
        for f in [video_path, audio_path, bangla_audio]:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"Deleted filesL {f}")
                else:
                    print(f"Not found:{f}")
            except Exception as e:
                print(f"could not delete {f}: {e}")



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dub", methods=["POST"])
def dub():
    url=request.form.get("url")
    if not url:
        flash("please enter a youtube url: ")
        return redirect("/")
    
    global progress
    progress = {
        "current": 0,
        "total": 0,
        "percent": 0,
        "message": "Waiting...",
        "finished": False,
        "filename": ""
    }
    
    job_id=str(uuid.uuid4()) #/kaj ki

    video_path=os.path.join(UPLOAD_FOLDER,f"{job_id}.mp4")
    audio_path=os.path.join(UPLOAD_FOLDER, f"{job_id}.wav")
    bangla_audio=os.path.join(OUTPUT_FOLDER, f"{job_id}_bn.wav")
    output_video=os.path.join(OUTPUT_FOLDER,f"{job_id}.mp4")

    Thread (
        target=run_dubbing,
        args=(url,video_path, audio_path, bangla_audio, output_video)
    ).start()
    return render_template("progress.html")

@app.route("/progress")
def get_progress():
    return jsonify(progress)

@app.route("/result/<filename>")
def result(filename):
    path=os.path.join(OUTPUT_FOLDER,filename)

    if not os.path.exists(path):
        return"file not found:",404
    response=send_file(path, as_attachment=True)
    @response.call_on_close
    def cleanup():
        try:
            os.remove(path)
            print(f"Deleted file: {path}")
        except Exception as e:
            print(e)
    return response

if __name__=="__main__":
    app.run(debug=True, port=5001)
