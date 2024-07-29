import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import subprocess
from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR
from utils import (
    parse_command, 
    construct_ffmpeg_command, 
    ensure_directory, 
    parse_duration,    # Ensure these are imported from utils if they are in utils.py
    parse_time
)

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

    # Ask user for caption
    caption_message = await progress_message.reply("Please send the caption for the output file.")

    # Define a function to handle the caption reply
    @app.on_message(filters.text & filters.reply_to_message(caption_message))
    async def handle_caption_reply(client, message: Message):
        caption = message.text
        await progress_message.delete()

        # Determine if a thumbnail was provided
        thumbnail_file_id = options.get('thumbnail_file_id')

        # Send the processed file with the caption and optional thumbnail
        if output_path.lower().endswith(('.mp4', '.avi', '.mkv')):
            if thumbnail_file_id:
                await message.reply_video(output_path, caption=caption, thumb=thumbnail_file_id)
            else:
                await message.reply_video(output_path, caption=caption)
        else:
            if thumbnail_file_id:
                await message.reply_document(output_path, caption=caption, thumb=thumbnail_file_id)
            else:
                await message.reply_document(output_path, caption=caption)

        # Clean up the downloaded and processed files
        os.remove(video_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@app.on_message(filters.command("r"))
async def process_command(client, message):
    """Process the command to transform a video or document."""
    if message.reply_to_message:
        # Parse the command
        command_text = message.text.split()
        options = parse_command(command_text)

        # Determine the task name based on flags
        if '-m' in command_text:
            options['task'] = "Metadata Change"
        elif '-a' in command_text:
            options['task'] = "Audio Track Change"
        else:
            options['task'] = "Processing"

        # Handle renaming
        if '-rn' in command_text:
            rn_index = command_text.index('-rn')
            if rn_index + 1 < len(command_text):
                new_filename = command_text[rn_index + 1]
                message.reply_to_message.file_name = new_filename

        # Handle thumbnail
        if '-tn' in command_text:
            tn_index = command_text.index('-tn')
            if tn_index + 1 < len(command_text):
                thumbnail_file_id = command_text[tn_index + 1]
                options['thumbnail_file_id'] = thumbnail_file_id

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
            original_filename = message.reply_to_message.file_name if message.reply_to_message else "processed_file"
            options["new_filename"] = f"processed_{original_filename}"
        
        output_path = os.path.join(DOWNLOAD_DIR, options["new_filename"])

        # Run FFmpeg command with progress
        await ffmpeg_progress(video_path, output_path, options, progress_message, task_id)

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    """Handle cancel button callback."""
    task_id = callback_query.data.split('_')[1]
    if task_id in tasks:
        tasks[task_id].terminate()
        del tasks[task_id]
        await callback_query.message.edit("Task canceled.")

# Run the bot
app.run()
