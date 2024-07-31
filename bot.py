import os
import asyncio
import re
import subprocess
from pyrogram import Client, filters
from concurrent.futures import ThreadPoolExecutor
import tempfile
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize the Pyrogram Client
app = Client("merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# A dictionary to store user file lists and batch information
user_files = {}
user_batches = {}
user_merge_count = {}

# Use a thread pool for running blocking operations
executor = ThreadPoolExecutor(max_workers=4)

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Hi! Send me files to collect them. Use /merge -i N to combine N files from the batch you reply to.")

@app.on_message(filters.command("help"))
async def help(_, message):
    await message.reply_text("Send me files, and use /merge -i N to combine N files from the batch you reply to.")

@app.on_message(filters.document)
async def receive_files(client, message):
    user_id = message.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []
        user_batches[user_id] = []

    # Download the file asynchronously
    file_path = await message.download()
    user_files[user_id].append(file_path)

    # Identify the batch and store it
    if message.reply_to_message and message.reply_to_message.document:
        batch_id = message.reply_to_message.message_id
        if batch_id not in user_batches[user_id]:
            user_batches[user_id].append(batch_id)

    # Send feedback message
    await message.reply_text(f"File received! Total files: {len(user_files[user_id])}. Use /merge -i N to combine them.")

@app.on_message(filters.command("merge"))
async def merge_files_command(client, message):
    user_id = message.from_user.id

    # Extract the number of files to merge and the batch ID
    command_parts = message.text.split()
    if len(command_parts) < 3 or command_parts[1] != "-i":
        await message.reply_text("Usage: /merge -i N where N is the number of files to merge.")
        return

    try:
        num_files = int(command_parts[2])
        if user_id not in user_batches:
            await message.reply_text("No batch information available.")
            return

        batch_id = message.reply_to_message.message_id if message.reply_to_message else None
        if not batch_id or batch_id not in user_batches[user_id]:
            await message.reply_text("You must reply to the first file in the batch to specify which batch to merge.")
            return

        # Filter files that belong to the specified batch
        files_to_merge = [f for i, f in enumerate(user_files[user_id]) if i+1 <= num_files]
        if len(files_to_merge) < num_files:
            await message.reply_text(f"You need to send at least {num_files} files to merge them.")
            return

        output_files = files_to_merge

        # Create a temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            input_txt_path = f.name
            for file_path in output_files:
                f.write(f"file '{os.path.abspath(file_path)}'\n")

        output_file = f"merged_{user_id}.mkv"

        # FFmpeg command to merge files
        ffmpeg_command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_txt_path,
            "-c", "copy", output_file
        ]

        # Function to capture FFmpeg progress
        def ffmpeg_progress_callback(process):
            output = ""
            while True:
                line = process.stdout.readline().decode("utf-8")
                if not line and process.poll() is not None:
                    break
                if line:
                    output += line
                    # Look for progress information in FFmpeg output
                    match = re.search(r'(\d+(\.\d+)?)%.*?(\d+(\.\d+)?)kB/s', line)
                    if match:
                        percent = match.group(1)
                        speed = match.group(3)
                        asyncio.run_coroutine_threadsafe(
                            update_progress_message(message, f"Merging progress: {percent}% at {speed} KB/s"),
                            asyncio.get_event_loop()
                        ).result()

        # Run FFmpeg as a subprocess and capture progress
        process = subprocess.Popen(
            ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        await asyncio.get_event_loop().run_in_executor(
            executor, ffmpeg_progress_callback, process
        )
        process.wait()

        # Send the merged file to the user
        await message.reply_document(document=output_file)

    except (IndexError, ValueError):
        await message.reply_text("Invalid number of files specified. Usage: /merge -i N where N is the number of files to merge.")
    except subprocess.CalledProcessError as e:
        await message.reply_text(f"An error occurred during merging: {e}")
    finally:
        # Clean up
        for file in user_files[user_id]:
            os.remove(file)
        if os.path.exists(input_txt_path):
            os.remove(input_txt_path)
        if os.path.exists(output_file):
            os.remove(output_file)
        user_files[user_id] = []
        user_batches[user_id] = []

async def update_progress_message(message, text):
    # Send a new message with the progress update
    await message.reply_text(text)

# Run the bot
app.run()
