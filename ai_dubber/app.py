from flask import Flask, render_template, request, send_file, flash, redirect
import os
import uuid
import subprocess

from youtube_downloder import download_video
from dub_engine import create_dub
from video_utility import extract_audio, merge_video

app=Flask(__name__)
app.secret_key=""

UPLOAD_FOLDER="uploads"
OUTPUT_FOLDER="outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dub", methods=["POST"])
def db():
    url=request.form.get("url")
    if not url:
        flash("please enter a youtube url: ")
        return redirect("/")
    
    job_id=str(uuid.uuid4()) #/kaj ki

    video_path=os.path.join(UPLOAD_FOLDER,f"{job_id}.mp4")
    audio_path=os.path.join(UPLOAD_FOLDER, f"{job_id}.wav")
    bangla_audio=os.path.join(OUTPUT_FOLDER, f"{job_id}_bn.wav")
    output_video=os.path.join(OUTPUT_FOLDER,f"{job_id}.mp4")

    try:
        print("Downloading...")
        download_video(url,video_path)

        print("Extracting Audio...")
        extract_audio(video_path,audio_path)

        print("Create bangla dub...")
        create_dub(
            video_audio=audio_path,
            output_audio=bangla_audio
        )

        print("Merging...")
        merge_video(video_path,bangla_audio,output_video)
        return render_template("result.html", filename=os.path.basename(output_video))
    except Exception as e:
        flash(str(e))
        return redirect("/")
    

@app.route("/download/<filename>")
def download(filename):
    path=os.path.join(OUTPUT_FOLDER,filename)
    return send_file(path, as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)
