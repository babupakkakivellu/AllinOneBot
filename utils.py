import os
import subprocess
from pyrogram import Client, types
from config import VIDEO_DIR
from tqdm import tqdm
import time

async def download_video(client: Client, file_id: str) -> str:
    """Download video from Telegram and return the file path with progress."""
    file_path = os.path.join(VIDEO_DIR, f"{file_id}.mkv")
    media = await client.get_messages(chat_id=file_id.chat.id, message_ids=file_id.message_id)
    file_size = media.video.file_size

    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Downloading", ncols=100) as progress_bar:
        async for chunk in client.download_media(file_id, file_name=file_path, in_memory=False):
            progress_bar.update(len(chunk))

    return file_path

def merge_videos(video_paths: list, output_path: str):
    """Merge a list of video paths into a single MKV file using mkvmerge."""
    command = ["mkvmerge", "-o", output_path] + video_paths
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Merged videos successfully: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error merging videos: {e.stderr}")
        raise

async def upload_video(client: Client, chat_id: int, video_path: str):
    """Upload video to Telegram with progress."""
    file_size = os.path.getsize(video_path)
    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Uploading", ncols=100) as progress_bar:
        async for _ in client.send_video(chat_id=chat_id, video=video_path, progress=progress_bar_callback, progress_args=(progress_bar,)):
            pass

def progress_bar_callback(current, total, progress_bar):
    """Callback function to update tqdm progress bar."""
    progress_bar.total = total
    progress_bar.n = current
    progress_bar.refresh()
    time.sleep(0.1)  # To prevent spamming the progress bar updates
