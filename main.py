# main.py

import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR
from utils import parse_command, construct_ffmpeg_command, ensure_directory

# Initialize the bot
app = Client("ffmpeg_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to keep track of tasks
tasks = {}

# Ensure download directory exists
ensure_directory(DOWNLOAD_DIR)

async def update_progress_message(message: Message, text: str, task_id: str):
    """Edit the progress message to update its text and add a cancel button."""
    cancel_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Cancel Task", callback_data=f"cancel_{task_id}")]]
    )
    await message.edit(text, reply_markup=cancel_button)

async def download_progress(current, total, message: Message, start_time, progress_message: Message, task: str, task_id: str):
    """Show progress for downloading a file, updating every 2 seconds."""
    elapsed_time = time.time() - start_time
    if elapsed_time > 2:
        progress = (current / total) * 100
        await update_progress_message(progress_message, f"{task} Downloading: {progress:.2f}% completed", task_id)
        start_time = time.time()

async def upload_progress(current, total, message: Message, start_time, progress_message: Message, task: str, task_id: str):
    """Show progress for uploading a file, updating every 2 seconds."""
    elapsed_time = time.time() - start_time
    if elapsed_time > 2:
        progress = (current / total) * 100
        await update_progress_message(progress_message, f"{task} Uploading: {progress:.2f}% completed", task_id)
        start_time = time.time()

async def ffmpeg_progress(video_path, output_path, options, progress_message: Message, task_id: str):
    """Run FFmpeg with progress output and send updates."""
    command = construct_ffmpeg_command(video_path, output_path, options)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    tasks[task_id] = process

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
                    await update_progress_message(progress_message, f"{options['task']}: {progress:.2f}% completed", task_id)
                    start_time = time.time()

        # Check if the task is canceled
        if task_id not in tasks:
            process.terminate()
            await progress_message.edit("Task canceled.")
            return

    process.wait()

    # Remove task from dictionary once completed
    if task_id in tasks:
        del tasks[task_id]

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
    """Process the command to transform a video or document."""
    if message.reply_to_message:
        # Parse the command
        command_text = message.text.split()
        options = parse_command(command_text)

        # Determine the task name based on flags
        if '-m' in command_text:
            options['task'] = "Audio Removal"
        elif '-i' in command_text:
            options['task'] = "Audio Track Change"
        else:
            options['task'] = "Processing"

        # Check for the -n flag to set new filename
        if '-n' in command_text:
            n_index = command_text.index('-n')
            if n_index + 1 < len(command_text):
                options['new_filename'] = command_text[n_index + 1]
            else:
                options['new_filename'] = None
        else:
            options['new_filename'] = None

        # Generate a unique task ID
        task_id = f"{message.chat.id}_{message.id}"

        # Send initial message with cancel button
        progress_message = await message.reply("Starting processing...",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel Task", callback_data=f"cancel_{task_id}")]]
            )
        )

        # Download the original file
        start_time = time.time()
        file_type = message.reply_to_message.video if message.reply_to_message.video else message.reply_to_message.document
        video_path = await message.reply_to_message.download(
            file_name=DOWNLOAD_DIR,
            progress=download_progress,
            progress_args=(message, start_time, progress_message, options['task'], task_id)
        )

        # Define the output path
        if not options["new_filename"]:
            # If no new filename is provided, create a default one
            original_filename = file_type.file_name if file_type else "processed_file"
            options["new_filename"] = f"processed_{original_filename}"
        
        output_path = os.path.join(DOWNLOAD_DIR, options["new_filename"])

        # Run FFmpeg command with progress
        await ffmpeg_progress(video_path, output_path, options, progress_message, task_id)

        # Determine if the file is a video or document and send the processed file
        if file_type and file_type.file_id and file_type.file_name.lower().endswith(('.mp4', '.avi', '.mov')):
            await message.reply_video(
                video=output_path,
                progress=upload_progress,
                progress_args=(message, start_time, progress_message, options['task'], task_id)
            )
        else:
            await message.reply_document(
                document=output_path,
                progress=upload_progress,
                progress_args=(message, start_time, progress_message, options['task'], task_id)
            )

        # Delete the progress message after upload
        await progress_message.delete()

        # Clean up the downloaded and processed files
        os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@app.on_callback_query(filters.regex(r"cancel_"))
async def cancel_task(client, callback_query):
    """Cancel the ongoing task."""
    task_id = callback_query.data.split("_")[1]
    if task_id in tasks:
        tasks[task_id].terminate()
        del tasks[task_id]
        await callback_query.message.edit("Task canceled.")

if __name__ == "__main__":
    app.run()
