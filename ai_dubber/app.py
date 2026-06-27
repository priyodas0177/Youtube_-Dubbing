from flask import Flask, render_template, request, send_file, flash, redirect
import os
import uuid
import subprocess

from youtube_downloder import download_video
from dub_engine import create_dub
from video_utility import extract_audio, merge_video

app=Flask(__name__)
