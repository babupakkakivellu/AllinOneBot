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
processing_actions = {}

def build_main_menu():
    return InlineKeyboardMarkup([
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
    message.reply("Welcome to the Video Processing Bot! Please upload your video file to get started.")

@app.on_message(filters.video)
def handle_video(client, message):
    user_id = message.from_user.id
    file_path = message.video.file_name
    file_name = message.video.file_id + ".mp4"  # Unique file name
    file_path = f"downloads/{file_name}"

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    message.download(file_path)

    if user_id not in user_files:
        user_files[user_id] = []

    user_files[user_id].append(file_path)
    
    message.reply("File uploaded successfully! Choose what you want to do next:", reply_markup=build_main_menu())

@app.on_callback_query()
def handle_callback_query(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if user_id not in user_files or len(user_files[user_id]) == 0:
        client.send_message(user_id, "No file available for processing. Please upload a file first.")
        return

    if data == "change_metadata":
        client.send_message(user_id, "Send the new metadata in the format `key=value`. Example: `title=New Title`.")
        processing_actions[user_id] = "change_metadata"

    elif data == "change_audio":
        client.send_message(user_id, "Send the new audio track file to replace the existing one.")
        processing_actions[user_id] = "change_audio"

    elif data == "merge_files":
        client.send_message(user_id, "Upload additional files you want to merge. Type `-n filename.mkv` for the output filename once done.")
        processing_actions[user_id] = "merge_files"

    elif data == "extract_audio":
        client.send_message(user_id, "Send the audio extraction file name. Example: `output.mp3`.")
        processing_actions[user_id] = "extract_audio"

    elif data == "convert_format":
        client.send_message(user_id, "Send the desired output format (e.g., mp4, mkv). Example: `output.mp4`.")
        processing_actions[user_id] = "convert_format"

    elif data == "split_video":
        client.send_message(user_id, "Send the start time and duration in the format `start_time duration`. Example: `00:00:00 00:00:30`.")
        processing_actions[user_id] = "split_video"

    elif data == "compress_video":
        client.send_message(user_id, "Send the desired bitrate. Example: `1M`.")
        processing_actions[user_id] = "compress_video"

    elif data == "resize_video":
        client.send_message(user_id, "Send the new width and height in the format `width height`. Example: `1280 720`.")
        processing_actions[user_id] = "resize_video"

    elif data == "add_subtitles":
        client.send_message(user_id, "Send the subtitles file to add.")
        processing_actions[user_id] = "add_subtitles"

    elif data == "add_watermark":
        client.send_message(user_id, "Send the watermark file to add.")
        processing_actions[user_id] = "add_watermark"

@app.on_message(filters.text)
def handle_text(client, message):
    user_id = message.from_user.id

    if user_id in processing_actions:
        action = processing_actions[user_id]
        if action == "change_metadata":
            output_file = user_files[user_id][0]  # Assuming one file for metadata change
            metadata = message.text
            progress_message = client.send_message(user_id, "Changing metadata. Please wait...")
            success = change_metadata(output_file, output_file, metadata)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Metadata changed successfully!")
            else:
                client.send_message(user_id, "Failed to change metadata.")
            del processing_actions[user_id]

        elif action == "extract_audio":
            output_file = message.text
            video_file = user_files[user_id][0]
            progress_message = client.send_message(user_id, "Extracting audio. Please wait...")
            success = extract_audio(video_file, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Audio extracted successfully!")
            else:
                client.send_message(user_id, "Failed to extract audio.")
            del processing_actions[user_id]

        elif action == "convert_format":
            output_format = message.text
            video_file = user_files[user_id][0]
            output_file = f"converted_{int(time.time())}.{output_format}"
            progress_message = client.send_message(user_id, "Converting format. Please wait...")
            success = convert_video_format(video_file, output_format, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Format converted successfully!")
            else:
                client.send_message(user_id, "Failed to convert format.")
            del processing_actions[user_id]

        elif action == "split_video":
            start_time, duration = message.text.split()
            video_file = user_files[user_id][0]
            output_file = f"split_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Splitting video. Please wait...")
            success = split_video(video_file, start_time, duration, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Video split successfully!")
            else:
                client.send_message(user_id, "Failed to split video.")
            del processing_actions[user_id]

        elif action == "compress_video":
            bitrate = message.text
            video_file = user_files[user_id][0]
            output_file = f"compressed_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Compressing video. Please wait...")
            success = compress_video(video_file, bitrate, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Video compressed successfully!")
            else:
                client.send_message(user_id, "Failed to compress video.")
            del processing_actions[user_id]

        elif action == "resize_video":
            width, height = message.text.split()
            video_file = user_files[user_id][0]
            output_file = f"resized_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Resizing video. Please wait...")
            success = resize_video(video_file, width, height, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Video resized successfully!")
            else:
                client.send_message(user_id, "Failed to resize video.")
            del processing_actions[user_id]

        elif action == "add_subtitles":
            subtitles_file = message.document.file_name
            video_file = user_files[user_id][0]
            output_file = f"subtitled_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Adding subtitles. Please wait...")
            success = add_subtitles(video_file, subtitles_file, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Subtitles added successfully!")
            else:
                client.send_message(user_id, "Failed to add subtitles.")
            del processing_actions[user_id]

        elif action == "add_watermark":
            watermark_file = message.document.file_name
            video_file = user_files[user_id][0]
            output_file = f"watermarked_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Adding watermark. Please wait...")
            success = add_watermark(video_file, watermark_file, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Watermark added successfully!")
            else:
                client.send_message(user_id, "Failed to add watermark.")
            del processing_actions[user_id]

@app.on_message(filters.document)
def handle_document(client, message):
    user_id = message.from_user.id

    if user_id in processing_actions:
        action = processing_actions[user_id]
        file_path = message.download()

        if action == "change_audio":
            video_file = user_files[user_id][0]
            output_file = f"audio_changed_{int(time.time())}.mp4"
            progress_message = client.send_message(user_id, "Changing audio track. Please wait...")
            success = change_audio_track(video_file, file_path, output_file)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Audio track changed successfully!")
            else:
                client.send_message(user_id, "Failed to change audio track.")
            del processing_actions[user_id]

        elif action == "merge_files":
            if 'merge_files' not in processing_actions:
                processing_actions[user_id] = {'files': [], 'output_file': None}
            processing_actions[user_id]['files'].append(file_path)
            client.send_message(user_id, "File added for merging. Upload more files or type `-n filename.mkv` for the output filename.")

@app.on_message(filters.text)
def handle_merge_command(client, message):
    user_id = message.from_user.id

    if user_id in processing_actions and 'merge_files' in processing_actions[user_id]:
        if '-n ' in message.text:
            output_file = message.text.split('-n ')[1].strip()
            if not output_file.endswith('.mkv'):
                output_file += '.mkv'
            
            processing_actions[user_id]['output_file'] = output_file
            progress_message = client.send_message(user_id, "Merging files. Please wait...")

            def progress_callback(progress):
                client.edit_message_text(user_id, progress_message.message_id, f"Merging files: {progress}% completed.")

            success = merge_mkv_files(processing_actions[user_id]['files'], output_file, progress_callback)
            if success:
                client.send_document(user_id, output_file)
                client.send_message(user_id, "Files merged successfully!")
            else:
                client.send_message(user_id, "Failed to merge files.")
            
            del processing_actions[user_id]

if __name__ == "__main__":
    app.run()
