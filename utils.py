import subprocess
import tempfile
from pyrogram import Client

DEFAULT_SETTINGS = {
    "output_format": "mp4",
    "font_style": "normal",
    "send_as": "video",
}

user_files = {}
user_file_names = {}
user_thumbnails = {}
user_settings = {}
progress_messages = {}

async def run_ffmpeg_command(command, handle_progress):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    async for line in process.stdout:
        if line:
            await handle_progress(line)
    returncode = process.wait()
    return returncode

async def send_progress_update(message, output):
    progress_msg = output.split("time=")[-1].split(" ")[0]
    if message.from_user.id not in progress_messages:
        progress_messages[message.from_user.id] = await message.reply_text(f"Progress: {progress_msg}")
    else:
        await message.edit_text(f"Progress: {progress_msg}")

def get_video_dimensions(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        output = subprocess.check_output(cmd).decode().strip().split("\n")
        if len(output) == 2:
            width, height = output
            return (width, height)
    except Exception as e:
        logger.error(f"Error getting video dimensions: {e}")
    return (None, None)
