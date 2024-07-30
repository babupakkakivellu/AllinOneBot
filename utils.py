import os
import subprocess
import asyncio
from pyrogram import Client, types

DOWNLOAD_DIR = 'downloads'

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

async def download_media_with_progress(client: Client, file_id: str, message: types.Message):
    ensure_download_dir()
    
    file_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")
    
    async with client.download_media(file_id, file_path) as progress:
        total_size = progress.total
        downloaded = 0
        
        async for chunk in progress:
            downloaded += len(chunk)
            progress_percentage = (downloaded / total_size) * 100
            await message.edit_text(f"Downloading: {progress_percentage:.2f}% completed")
    
    return file_path

def merge_videos(video_files, output_file):
    command = [
        'ffmpeg', 
        *[f'-i {file}' for file in video_files], 
        '-filter_complex', 
        f'concat=n={len(video_files)}:v=1:a=1 [v] [a]', 
        '-map', '[v]', 
        '-map', '[a]', 
        '-y', 
        output_file
    ]
    try:
        subprocess.run(' '.join(command), shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while merging videos: {e}")
        raise

def get_video_metadata(file_path):
    command = [
        'ffprobe', 
        '-v', 'error', 
        '-select_streams', 'v:0', 
        '-show_entries', 'stream=width,height,duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    metadata = result.stdout.strip().split('\n')

    width = metadata[0] if len(metadata) > 0 else 'N/A'
    height = metadata[1] if len(metadata) > 1 else 'N/A'
    duration = metadata[2] if len(metadata) > 2 else 'N/A'

    try:
        return int(width), int(height), float(duration)
    except ValueError as e:
        print(f"Error parsing video metadata: {e}")
        return 0, 0, 0

def get_random_thumbnail(video_file):
    thumbnail_file = video_file.replace('.mp4', '.jpg')
    command = [
        'ffmpeg', 
        '-i', video_file, 
        '-ss', '00:00:01.000', 
        '-vframes', '1', 
        thumbnail_file
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while generating thumbnail: {e}")
        return None
    
    return thumbnail_file
