import os
import subprocess
import asyncio
from pyrogram import Client

DOWNLOAD_DIR = 'downloads'

def ensure_download_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

async def download_media_with_progress(client: Client, file_id: str, chat_id: int):
    ensure_download_dir()
    
    file_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")
    
    # Ensure chat_id is an integer
    if not isinstance(chat_id, int):
        raise ValueError(f"Invalid chat_id: {chat_id}. Must be an integer.")
    
    # Send initial message for download progress
    progress_msg = await client.send_message(chat_id, "Downloading: 0% completed")

    # Initialize download variables
    file_size = None
    downloaded_size = 0
    last_update_time = asyncio.get_event_loop().time()

    # Download file
    try:
        async for chunk in client.download_media(file_id, file_path, progress=download_progress):
            downloaded_size += len(chunk)
            
            # Update progress every 4 seconds
            current_time = asyncio.get_event_loop().time()
            if current_time - last_update_time >= 4:
                last_update_time = current_time
                progress_percentage = (downloaded_size / file_size) * 100 if file_size else 0
                await progress_msg.edit(f"Downloading: {progress_percentage:.2f}% completed")
                
    except Exception as e:
        await progress_msg.edit("Download failed")
        print(f"Error during download: {e}")
        return None

    # Finalize progress message
    await progress_msg.edit("Download completed")
    return file_path

async def download_progress(downloaded, total):
    # This function is invoked periodically to update progress
    progress_percentage = (downloaded / total) * 100
    await progress_msg.edit(f"Downloading: {progress_percentage:.2f}% completed")

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
