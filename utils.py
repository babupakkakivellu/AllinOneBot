import subprocess
import os
import random

def merge_videos(video_files, output_file, thumbnail_file=None):
    input_files = '|'.join(video_files)
    command = [
        'ffmpeg',
        '-y',  # Overwrite output files without asking
        '-i', f'concat:{input_files}',
        '-c', 'copy',
        output_file
    ]
    
    # Run the FFmpeg command to merge videos
    subprocess.run(command, check=True)

    # Generate a random thumbnail if not provided
    if not thumbnail_file:
        return generate_thumbnail(output_file)

def generate_thumbnail(video_file):
    thumbnail_time = random.uniform(0.1, get_video_duration(video_file) - 0.1)
    thumbnail_file = f"{os.path.splitext(video_file)[0]}_thumb.jpg"
    command = [
        'ffmpeg',
        '-y',  # Overwrite output files without asking
        '-ss', str(thumbnail_time),
        '-i', video_file,
        '-vframes', '1',
        '-q:v', '2',  # Quality setting for thumbnail
        thumbnail_file
    ]

    # Run the FFmpeg command to generate a thumbnail
    subprocess.run(command, check=True)

    return thumbnail_file

def get_video_duration(video_file):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        video_file
    ]

    # Get the duration of the video
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return float(result.stdout)

def get_video_metadata(video_file):
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration',
        '-of', 'csv=s=x:p=0',
        video_file
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    width, height, duration = map(float, result.stdout.decode().strip().split('x'))
    return duration, width, height
