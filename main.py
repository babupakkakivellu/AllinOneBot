from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN
from utils import (
    change_metadata, change_audio_track, merge_mkv_files,
    extract_audio, convert_video_format, split_video,
    compress_video, resize_video, add_subtitles, add_watermark
)
import os

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}
user_subtitles = {}
user_watermarks = {}
merge_requests = {}  # To keep track of users in merging process

def build_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Upload Video", callback_data="upload_video")],
        [InlineKeyboardButton("🛠 Change Metadata", callback_data="change_metadata")],
        [InlineKeyboardButton("🔊 Change Audio Track", callback_data="change_audio")],
        [InlineKeyboardButton("🔄 Merge Files", callback_data="merge_files")],
        [InlineKeyboardButton("🎵 Extract Audio", callback_data="extract_audio")],
        [InlineKeyboardButton("🔄 Convert Format", callback_data="convert_format")],
        [InlineKeyboardButton("✂️ Split Video", callback_data="split_video")],
        [InlineKeyboardButton("📉 Compress Video", callback_data="compress_video")],
        [InlineKeyboardButton("📏 Resize Video", callback_data="resize_video")],
        [InlineKeyboardButton("📝 Add Subtitles", callback_data="add_subtitles")],
        [InlineKeyboardButton("🌊 Add Watermark", callback_data="add_watermark")],
    ])

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply("Welcome to the Video Processing Bot! Choose an option below:", reply_markup=build_start_keyboard())

@app.on_callback_query()
def handle_callback_query(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "upload_video":
        client.send_message(user_id, "Please upload the video file you want to process.")
    elif data == "change_metadata":
        client.send_message(user_id, "Send the metadata in key:value format and the output filename using `-n output_filename.mkv`.")
    elif data == "change_audio":
        client.send_message(user_id, "Send the audio track index to keep (or type 'remove' to remove all audio) and the output filename using `-n output_filename.mkv`.")
    elif data == "merge_files":
        client.send_message(user_id, "Upload the files you want to merge. After uploading all files, click the button to start merging.")
        merge_requests[user_id] = []  # Initialize file list for merging
    elif data == "extract_audio":
        client.send_message(user_id, "Send the output filename using `-n output_filename.mp3`.")
    elif data == "convert_format":
        client.send_message(user_id, "Send the desired format (e.g., mp4) and output filename using `-n output_filename.format`.")
    elif data == "split_video":
        client.send_message(user_id, "Send the start time and duration (e.g., 00:00:10,00:00:30) and output filename using `-n output_filename.mkv`.")
    elif data == "compress_video":
        client.send_message(user_id, "Send the desired bitrate (e.g., 1M) and output filename using `-n output_filename.mkv`.")
    elif data == "resize_video":
        client.send_message(user_id, "Send the new width and height (e.g., 1280x720) and output filename using `-n output_filename.mkv`.")
    elif data == "add_subtitles":
        client.send_message(user_id, "Upload the subtitle file first, then send the video file, and specify the output filename using `-n output_filename.mkv`.")
    elif data == "add_watermark":
        client.send_message(user_id, "Upload the watermark image first, then send the video file, and specify the position and output filename using `-n output_filename.mkv`.")

    # Handle merge confirmation
    elif data == "confirm_merge":
        if user_id in merge_requests and merge_requests[user_id]:
            input_files = merge_requests[user_id]
            message.reply("Enter the output filename using `-n output_filename.mkv`.")
        else:
            message.reply("No files to merge. Please upload files first.")
    elif data == "cancel_merge":
        if user_id in merge_requests:
            del merge_requests[user_id]
        message.reply("Merge operation canceled. You can start again by uploading files.")

@app.on_message(filters.video)
def handle_video(client, message):
    user_id = message.from_user.id
    file_path = message.video.file_name

    # Download the video file
    video = message.download(file_path)

    if user_id in merge_requests:
        merge_requests[user_id].append(video)
        message.reply("Video file uploaded successfully! Send more files or click the button below to start merging.",
                      reply_markup=InlineKeyboardMarkup([
                          [InlineKeyboardButton("✅ Confirm Merge", callback_data="confirm_merge")],
                          [InlineKeyboardButton("❌ Cancel", callback_data="cancel_merge")]
                      ]))
    else:
        if user_id not in user_files:
            user_files[user_id] = []
        user_files[user_id].append(video)
        message.reply("Video file uploaded successfully!")

@app.on_message(filters.document.mime_type("text/plain"))
def handle_document(client, message):
    user_id = message.from_user.id
    file_path = message.document.file_name

    # Download the subtitle file
    subtitle = message.download(file_path)

    user_subtitles[user_id] = subtitle
    message.reply("Subtitle file uploaded successfully!")

@app.on_message(filters.photo)
def handle_photo(client, message):
    user_id = message.from_user.id
    file_path = f"{message.photo.file_id}.png"

    # Download the watermark photo
    photo = message.download(file_path)

    user_watermarks[user_id] = photo
    message.reply("Watermark image uploaded successfully!")

@app.on_message(filters.text & filters.reply)
def process_text_commands(client, message):
    user_id = message.from_user.id
    if user_id not in user_files:
        message.reply("No file available. Please upload a file first.")
        return

    input_file = user_files[user_id][-1]
    text = message.text

    if message.reply_to_message and message.reply_to_message.video:
        input_file = message.reply_to_message.download()

    # Parse output filename from the text
    def parse_filename_argument(text):
        parts = text.split(' -n ')
        return parts[1].strip() if len(parts) > 1 else None

    # Handle different commands
    if message.reply_to_message.text.startswith("Change Metadata"):
        output_file = parse_filename_argument(text)
        metadata = {k: v for k, v in (item.split(':') for item in text.split(',') if ':' in item)}
        if not output_file:
            output_file = f"output_{os.path.basename(input_file)}"
        progress_message = client.send_message(user_id, "Starting metadata change...")
        success = process_task_with_progress(lambda: change_metadata(input_file, output_file, metadata), user_id, progress_message.message_id)
        if success:
            client.send_message(user_id, f"Metadata changed successfully! File saved as {output_file}.")
        else:
            client.send_message(user_id, "Failed to change metadata.")

    elif message.reply_to_message.text.startswith("Change Audio Track"):
        if "remove" in text.lower():
            task = lambda: change_audio_track(input_file, output_file, remove_audio=True)
        else:
            try:
                audio_index = int(text.strip().split()[0])
                task = lambda: change_audio_track(input_file, output_file, audio_index=audio_index)
            except ValueError:
                message.reply("Invalid audio index. Please enter a valid index or 'remove'.")
                return

        output_file = parse_filename_argument(text)
        if not output_file:
            output_file = f"output_{os.path.basename(input_file)}"
        progress_message = client.send_message(user_id, "Starting audio change...")
        success = process_task_with_progress(task, user_id, progress_message.message_id)
        if success:
            client.send_message(user_id, f"Audio track changed successfully! File saved as {output_file}.")
        else:
            client.send_message(user_id, "Failed to change audio track.")

    # Similar updates for other commands...

@app.on_message(filters.command("status"))
def status(client, message):
    user_id = message.from_user.id
    message.reply("Available commands:\n"
                  "/upload - Upload a video file\n"
                  "/change_metadata - Change video metadata\n"
                  "/change_audio - Change or remove audio track\n"
                  "/merge_files - Merge multiple files\n"
                  "/extract_audio - Extract audio from a video\n"
                  "/convert_format - Convert video format\n"
                  "/split_video - Split a video into segments\n"
                  "/compress_video - Compress a video file\n"
                  "/resize_video - Resize a video\n"
                  "/add_subtitles - Add subtitles to a video\n"
                  "/add_watermark - Add a watermark to a video")

if __name__ == "__main__":
    app.run()
