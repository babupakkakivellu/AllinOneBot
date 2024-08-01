# main.py

from pyrogram import Client, filters
import subprocess
import os
import config

# Create a new Client using configuration from config.py
app = Client(
    "shell_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

def find_file(filename, search_path='/'):
    """
    Search for a file in the given directory and subdirectories.
    """
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

def get_video_metadata(file_path):
    """
    Use ffmpeg to get video metadata, including width, height, duration, and filename.
    Generate a thumbnail for the video.
    """
    try:
        # Run ffprobe to get video metadata
        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "default=noprint_wrappers=1",
            file_path
        ]
        metadata = subprocess.check_output(ffprobe_cmd).decode().splitlines()
        width, height = (int(metadata[0].split('=')[1]), int(metadata[1].split('=')[1]))

        # Run ffprobe to get video duration
        ffprobe_duration_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        duration = float(subprocess.check_output(ffprobe_duration_cmd).decode().strip())

        # Generate thumbnail
        thumbnail_path = file_path + ".jpg"
        ffmpeg_cmd = [
            "ffmpeg", "-i", file_path, "-ss", "00:00:01.000", "-vframes", "1",
            "-vf", f"scale=320:-1", thumbnail_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        return width, height, duration, os.path.basename(file_path), thumbnail_path
    except Exception as e:
        raise RuntimeError(f"Failed to get video metadata or generate thumbnail: {e}")

# Define a handler for executing shell commands
@app.on_message(filters.command("exec") & filters.private)
def shell_command(client, message):
    # Extract the command from the message
    command = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
    if command:
        try:
            # Execute the shell command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            # Send the result back to the user
            response = result.stdout if result.stdout else "No output"
            message.reply_text(response)
        except Exception as e:
            message.reply_text(f"Error: {str(e)}")
    else:
        message.reply_text("Please provide a command to execute.")

# Define a handler for uploading files using the filename
@app.on_message(filters.command("up") & filters.private)
def upload_file(client, message):
    # Extract the filename from the message
    filename = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
    if filename:
        file_path = find_file(filename)
        if file_path:
            try:
                # Check file extension and upload accordingly
                if file_path.lower().endswith('.mkv'):
                    # Get video metadata and generate thumbnail
                    width, height, duration, basename, thumbnail_path = get_video_metadata(file_path)

                    # Format duration into HH:MM:SS
                    duration_formatted = str(subprocess.check_output([
                        "ffmpeg", "-i", file_path, "-f", "null", "-"
                    ], stderr=subprocess.STDOUT).decode().split("Duration: ")[1].split(",")[0].strip())

                    # Upload as a video with thumbnail, width, height, duration, and filename
                    client.send_video(
                        chat_id=message.chat.id,
                        video=file_path,
                        width=width,
                        height=height,
                        thumb=thumbnail_path,
                        caption=f"Filename: {basename}\nDuration: {duration_formatted}"
                    )

                    # Remove the generated thumbnail after sending
                    os.remove(thumbnail_path)
                else:
                    # Upload as a document
                    client.send_document(chat_id=message.chat.id, document=file_path)
            except Exception as e:
                message.reply_text(f"Error: {str(e)}")
        else:
            message.reply_text("File not found. Please check the filename and try again.")
    else:
        message.reply_text("Please provide the filename you want to upload.")

# Run the bot
if __name__ == "__main__":
    app.run()
