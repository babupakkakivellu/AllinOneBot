from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN
from utils import (
    change_metadata, change_audio_track, merge_mkv_files,
    extract_audio, convert_video_format, split_video,
    compress_video, resize_video, add_subtitles, add_watermark
)
import os
import time

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_files = {}
merge_requests = {}

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
        client.send_message(user_id, "Upload the video file you want to process. After uploading, choose an action from the menu.")
        user_files[user_id] = []  # Initialize file list for operations

    elif data == "merge_files":
        client.send_message(user_id, "Upload the video files you want to merge. After uploading all files, click 'Confirm Merge' to start merging.")
        merge_requests[user_id] = []  # Initialize file list for merging

    elif data == "confirm_merge":
        if user_id in merge_requests and merge_requests[user_id]:
            client.send_message(user_id, "Please provide the output filename with the `-n output_filename.mkv` format.")
        else:
            client.send_message(user_id, "No files to merge. Please upload files first.")

    elif data == "cancel_merge":
        if user_id in merge_requests:
            del merge_requests[user_id]
        client.send_message(user_id, "Merge operation canceled. You can start again by uploading files.")

    # Handle other callback actions similarly...

@app.on_message(filters.video)
def handle_video(client, message):
    user_id = message.from_user.id
    file_path = message.video.file_name
    video = message.download(file_path)

    if user_id in merge_requests:
        merge_requests[user_id].append(video)
        message.reply("Video file uploaded successfully! You can upload more files or click 'Confirm Merge' to start merging.",
                      reply_markup=InlineKeyboardMarkup([
                          [InlineKeyboardButton("✅ Confirm Merge", callback_data="confirm_merge")],
                          [InlineKeyboardButton("❌ Cancel", callback_data="cancel_merge")]
                      ]))
    else:
        if user_id not in user_files:
            user_files[user_id] = []
        user_files[user_id].append(video)
        message.reply("Video file uploaded successfully! Choose the next action from the menu.")

@app.on_message(filters.text & filters.reply)
def process_text_commands(client, message):
    user_id = message.from_user.id

    if user_id in merge_requests:
        output_file = parse_filename_argument(message.text)
        if not output_file:
            output_file = f"merged_{int(time.time())}.mkv"
        
        progress_message = client.send_message(user_id, "Merging files. Please wait...")
        
        def progress_callback(progress):
            client.edit_message_text(user_id, progress_message.message_id, f"Merging files: {progress}% completed.")
        
        success = merge_mkv_files(merge_requests[user_id], output_file, progress_callback)
        if success:
            client.send_document(user_id, output_file)
            client.send_message(user_id, f"Merging completed! Your file is available as {output_file}.")
        else:
            client.send_message(user_id, "Failed to merge files. Please try again.")
        
        del merge_requests[user_id]  # Clear the merge request after processing

    # Handle other commands similarly...
    if user_id in user_files:
        if 'compress' in message.text:
            output_file = parse_filename_argument(message.text)
            if not output_file:
                output_file = f"compressed_{int(time.time())}.mp4"
            
            bitrate = '1M'  # Example bitrate
            progress_message = client.send_message(user_id, "Compressing video. Please wait...")
            
            def progress_callback(progress):
                client.edit_message_text(user_id, progress_message.message_id, f"Compressing video: {progress}% completed.")
            
            success = compress_video(user_files[user_id][0], bitrate, output_file, progress_callback)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, f"Compression completed! Your file is available as {output_file}.")
            else:
                client.send_message(user_id, "Failed to compress the video. Please try again.")
            
            del user_files[user_id]  # Clear the files after processing

def parse_filename_argument(text):
    parts = text.split(' -n ')
    return parts[1].strip() if len(parts) > 1 else None

if __name__ == "__main__":
    app.run()
