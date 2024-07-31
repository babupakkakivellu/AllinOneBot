import os
import asyncio
import subprocess
import tempfile
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN

# Initialize the Pyrogram Client
app = Client("merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user files
user_files = {}

# Run FFmpeg commands in a separate thread to avoid blocking the event loop
async def run_ffmpeg_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, error = await asyncio.get_event_loop().run_in_executor(
        None, process.communicate
    )
    return process.returncode, output.decode(), error.decode()

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Send me files, then use /merge -i N where N is the number of files to merge.")

@app.on_message(filters.command("help"))
async def help(_, message):
    await message.reply_text("Send files to me, then use /merge -i N to combine N files.")

@app.on_message(filters.document)
async def receive_files(_, message):
    user_id = message.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []

    # Download the file asynchronously
    file_path = await message.download()
    user_files[user_id].append(file_path)

    # Notify the user
    await message.reply_text(f"File received! Total files: {len(user_files[user_id])}. Use /merge -i N to combine the first N files.")

@app.on_message(filters.command("merge"))
async def merge_files_command(_, message):
    user_id = message.from_user.id

    # Ensure the command format is correct
    command_parts = message.text.split()
    if len(command_parts) < 3 or command_parts[1] != "-i":
        await message.reply_text("Usage: /merge -i N where N is the number of files to merge.")
        return

    try:
        num_files = int(command_parts[2])
        if user_id not in user_files or len(user_files[user_id]) < num_files:
            await message.reply_text(f"You need to upload at least {num_files} files before merging.")
            return

        # Select files to merge
        files_to_merge = user_files[user_id][:num_files]

        # Create a temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            input_txt_path = f.name
            for file_path in files_to_merge:
                f.write(f"file '{os.path.abspath(file_path)}'\n")

        output_file = f"merged_{user_id}.mkv"

        # FFmpeg command to merge files
        ffmpeg_command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_txt_path,
            "-c", "copy", output_file
        ]

        # Run FFmpeg command
        returncode, output, error = await run_ffmpeg_command(ffmpeg_command)

        if returncode != 0:
            await message.reply_text(f"An error occurred during merging: {error}")
        else:
            # Send the merged file to the user
            await message.reply_document(document=output_file)

    except (IndexError, ValueError):
        await message.reply_text("Invalid number of files specified. Usage: /merge -i N where N is the number of files to merge.")
    finally:
        # Clean up
        for file in user_files[user_id]:
            os.remove(file)
        if os.path.exists(input_txt_path):
            os.remove(input_txt_path)
        if os.path.exists(output_file):
            os.remove(output_file)
        user_files[user_id] = []

# Run the bot
app.run()
