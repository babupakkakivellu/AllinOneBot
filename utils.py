import subprocess
import random
import os
from PIL import Image

def merge_videos(video_files, output_file):
    input_files = " ".join([f"-i {file}" for file in video_files])
    filter_complex = f"concat=n={len(video_files)}:v=1:a=1 [v] [a]"
    command = f"ffmpeg {input_files} -filter_complex \"{filter_complex}\" -map [v] -map [a] -y {output_file}"
    subprocess.run(command, shell=True, check=True)

def get_video_metadata(file_path):
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = result.stdout.decode().strip().split('\n')
    
    # Parse metadata with error handling
    try:
        width = float(metadata[0]) if metadata[0] != 'N/A' else None
        height = float(metadata[1]) if metadata[1] != 'N/A' else None
        duration = float(metadata[2]) if metadata[2] != 'N/A' else None
    except IndexError:
        width, height, duration = None, None, None

    return width, height, duration

def generate_random_thumbnail(file_path, output_thumbnail):
    command = [
        "ffmpeg",
        "-i", file_path,
        "-ss", "00:00:01.000",  # Capture frame at 1 second
        "-vframes", "1",
        output_thumbnail
    ]
    subprocess.run(command, shell=True, check=True)

def get_random_thumbnail(file_path):
    thumbnail_file = f"thumbnail_{random.randint(1000, 9999)}.jpg"
    generate_random_thumbnail(file_path, thumbnail_file)
    return thumbnail_file
