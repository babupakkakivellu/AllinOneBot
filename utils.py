import subprocess
import os
import random

def merge_videos(video_files, output_file):
    # Quote the output filename to handle special characters and spaces
    quoted_output_file = f'"{output_file}"'
    
    # Create the ffmpeg command
    input_files = " ".join([f"-i \"{file}\"" for file in video_files])
    command = (
        f"ffmpeg {input_files} "
        f"-filter_complex \"concat=n={len(video_files)}:v=1:a=1 [v] [a]\" "
        f"-map [v] -map [a] -y {quoted_output_file}"
    )
    
    # Run the command
    subprocess.run(command, shell=True, check=True)

def get_video_metadata(video_file):
    # Use ffprobe to get video metadata
    command = [
        'ffprobe', '-v', 'error', '-show_entries',
        'stream=width,height,duration', '-of',
        'default=noprint_wrappers=1:nokey=1', video_file
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode().strip().split('\n')
    
    # Extract width, height, and duration
    if len(output) >= 3:
        width, height, duration = output[0], output[1], output[2]
        return int(width), int(height), float(duration)
    else:
        return 0, 0, 0.0

def get_random_thumbnail(video_file):
    # Generate a random thumbnail using ffmpeg
    output_thumbnail = f"thumb_{random.randint(1000, 9999)}.jpg"
    command = [
        'ffmpeg', '-i', video_file, '-ss', '00:00:01.000', '-vframes', '1', '-q:v', '2', output_thumbnail
    ]
    
    subprocess.run(command, shell=True, check=True)
    return output_thumbnail
