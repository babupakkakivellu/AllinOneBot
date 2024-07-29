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

async def update_progress_message(message: Message, text: str):
    """Edit the progress message to update its text."""
    await message.edit(text)

async def download_progress(current, total, message: Message, start_time, progress_message: Message):
    """Show progress for downloading a file, updating every 2 seconds."""
    elapsed_time = time.time() - start_time
    if elapsed_time > 2:
        progress = (current / total) * 100
        await update_progress_message(progress_message, f"Downloading: {progress:.2f}% completed")
        start_time = time.time()

async def upload_progress(current, total, message: Message, start_time, progress_message: Message):
    """Show progress for uploading a file, updating every 2 seconds."""
    elapsed_time = time.time() - start_time
    if elapsed_time > 2:
        progress = (current / total) * 100
        await update_progress_message(progress_message, f"Uploading: {progress:.2f}% completed")
        start_time = time.time()

async def ffmpeg_progress(video_path, output_path, options, progress_message: Message):
    """Run FFmpeg with progress output and send updates."""
    command = construct_ffmpeg_command(video_path, output_path, options)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    total_duration = None
    start_time = time.time()
    while True:
        line = process.stderr.readline()
        if not line:
            break
        if "Duration" in line:
            total_duration = parse_duration(line)
        elif "time=" in line:
            current_time = parse_time(line)
            if total_duration:
                progress = (current_time / total_duration) * 100
                elapsed_time = time.time() - start_time
                if elapsed_time > 2:
                    await update_progress_message(progress_message, f"Processing: {progress:.2f}% completed")
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

        # Send initial message
        progress_message = await message.reply("Starting video processing...")

        # Download the original video
        start_time = time.time()
        video_path = await message.reply_to_message.download(
            file_name=DOWNLOAD_DIR,
            progress=download_progress,
            progress_args=(message, start_time, progress_message)
        )

        # Define the output path
        if not options["new_filename"]:
            # If no new filename is provided, create a default one
            original_filename = message.reply_to_message.video.file_name
            options["new_filename"] = f"processed_{original_filename}"
        
        output_path = os.path.join(DOWNLOAD_DIR, options["new_filename"])

        # Run FFmpeg command with progress
        await ffmpeg_progress(video_path, output_path, options, progress_message)

        # Send the processed video back to the user
        start_time = time.time()
        await message.reply_video(
            video=output_path,
            progress=upload_progress,
            progress_args=(message, start_time, progress_message)
        )

        # Clean up the downloaded and processed files
        os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)
    else:
        await message.reply("Please reply to a video with your command.")

# Start the bot
app.run()
