# main.py

import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm
import subprocess
from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR
from utils import parse_command, construct_ffmpeg_command, ensure_directory

# Initialize the bot
app = Client("ffmpeg_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure download directory exists
ensure_directory(DOWNLOAD_DIR)

async def download_progress(current, total, message: Message, start_time, progress_bar):
    """Show progress for downloading a file, updating every 2 seconds."""
    if time.time() - start_time > 2:
        progress_bar.n = current
        progress_bar.refresh()
        start_time = time.time()

async def upload_progress(current, total, message: Message, start_time, progress_bar):
    """Show progress for uploading a file, updating every 2 seconds."""
    if time.time() - start_time > 2:
        progress_bar.n = current
        progress_bar.refresh()
        start_time = time.time()

def ffmpeg_progress(video_path, output_path, options):
    """Run FFmpeg with progress output."""
    command = construct_ffmpeg_command(video_path, output_path, options)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Parse FFmpeg progress
    total_duration = None
    start_time = time.time()
    with tqdm(total=100, desc="Processing") as pbar:
        for line in process.stderr:
            if "Duration" in line:
                total_duration = parse_duration(line)
            elif "time=" in line:
                current_time = parse_time(line)
                if total_duration:
                    progress = (current_time / total_duration) * 100
                    if time.time() - start_time > 2:
                        pbar.n = int(progress)
                        pbar.refresh()
                        start_time = time.time()
        process.wait()

def parse_duration(line):
    """Parse total duration from FFmpeg output."""
    import re
    match = re.search(r"Duration: (\d+):(\d+):(\d+).(\d+)", line)
    if match:
        hours, minutes, seconds, _ = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return None

def parse_time(line):
    """Parse current time from FFmpeg output."""
    import re
    match = re.search(r"time=(\d+):(\d+):(\d+).(\d+)", line)
    if match:
        hours, minutes, seconds, _ = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return 0

@app.on_message(filters.command("r"))
async def process_command(client, message):
    """Process the command to transform a video."""
    if message.reply_to_message and message.reply_to_message.video:
        # Parse the command
        command_text = message.text.split()
        options = parse_command(command_text)

        # Download the original video
        start_time = time.time()
        with tqdm(total=message.reply_to_message.video.file_size, unit='B', unit_scale=True, desc="Downloading") as progress_bar:
            video_path = await message.reply_to_message.download(
                file_name=DOWNLOAD_DIR,
                progress=download_progress,
                progress_args=(message, start_time, progress_bar)
            )

        # Define the output path
        if not options["new_filename"]:
            # If no new filename is provided, create a default one
            original_filename = message.reply_to_message.video.file_name
            options["new_filename"] = f"processed_{original_filename}"
        
        output_path = os.path.join(DOWNLOAD_DIR, options["new_filename"])

        # Run FFmpeg command with progress
        ffmpeg_progress(video_path, output_path, options)

        # Send the processed video back to the user
        start_time = time.time()
        with tqdm(total=os.path.getsize(output_path), unit='B', unit_scale=True, desc="Uploading") as progress_bar:
            await message.reply_video(
                video=output_path,
                progress=upload_progress,
                progress_args=(message, start_time, progress_bar)
            )

        # Clean up the downloaded and processed files
        os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)
    else:
        await message.reply("Please reply to a video with your command.")

# Start the bot
app.run()
