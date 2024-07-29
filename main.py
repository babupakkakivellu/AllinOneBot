from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN
from utils import (
    change_metadata, change_audio_track, merge_mkv_files,
    extract_audio, convert_video_format, split_video,
    compress_video, resize_video, add_subtitles, add_watermark
)
import os
import time

app = Client("video_processor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}
processing_actions = {}

@app.on_message(filters.command("start"))
def start(client, message):
    client.send_message(
        message.chat.id,
        "Welcome to the Video Processing Bot! Please upload a video file to get started.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

@app.on_message(filters.video)
def handle_video(client, message):
    user_id = message.from_user.id
    file_id = message.video.file_id
    file_path = f"downloads/{file_id}.mp4"

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Notify user of download start
    client.send_message(user_id, "Starting file download...")
    
    try:
        # Download file with progress callback
        def progress(current, total):
            percent = int((current / total) * 100)
            client.send_message(user_id, f"Downloading: {percent}% completed")
        
        message.download(file_path, progress=progress)
        user_data[user_id] = {'file': file_path}

        # Notify user after download completion
        client.send_message(
            user_id,
            "File downloaded successfully! Choose an action from the menu.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Process Video", callback_data="process_video")],
                [InlineKeyboardButton("Help", callback_data="help")]
            ])
        )
    except Exception as e:
        client.send_message(user_id, f"Error: {str(e)}")

@app.on_message(filters.document)
def handle_document(client, message):
    user_id = message.from_user.id

    if user_id in processing_actions:
        action = processing_actions[user_id]
        try:
            def progress(current, total):
                percent = int((current / total) * 100)
                client.send_message(user_id, f"Downloading: {percent}% completed")

            # Download the file with progress callback
            downloaded_file_path = message.download(progress=progress)

            if action == "change_audio":
                video_file = user_data[user_id]['file']
                output_file = f"changed_audio_{int(time.time())}.mp4"
                success = change_audio_track(video_file, downloaded_file_path, output_file)
                response = "Audio track changed successfully!" if success else "Failed to change audio track."
            
            elif action == "add_subtitles":
                video_file = user_data[user_id]['file']
                output_file = f"subtitled_{int(time.time())}.mp4"
                success = add_subtitles(video_file, downloaded_file_path, output_file)
                response = "Subtitles added successfully!" if success else "Failed to add subtitles."
            
            elif action == "add_watermark":
                video_file = user_data[user_id]['file']
                output_file = f"watermarked_{int(time.time())}.mp4"
                success = add_watermark(video_file, downloaded_file_path, output_file)
                response = "Watermark added successfully!" if success else "Failed to add watermark."
            
            elif action == "merge_files":
                if 'files' not in user_data[user_id]:
                    user_data[user_id]['files'] = []
                user_data[user_id]['files'].append(downloaded_file_path)
                client.send_message(user_id, "File added to merge list. Send more files if needed, or send the output filename with `-n filename.mkv` to start merging.")
            
            client.send_document(user_id, output_file)
            client.send_message(user_id, response)
            del processing_actions[user_id]
        
        except Exception as e:
            client.send_message(user_id, f"An error occurred: {str(e)}")

@app.on_callback_query()
def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    action = query.data

    if action == "help":
        client.send_message(
            user_id,
            "Here are the available commands:\n"
            "- Upload a video file.\n"
            "- Use the menu to choose an action:\n"
            "  - Change Metadata\n"
            "  - Change Audio Track\n"
            "  - Merge Files\n"
            "  - Extract Audio\n"
            "  - Convert Format\n"
            "  - Split Video\n"
            "  - Compress Video\n"
            "  - Resize Video\n"
            "  - Add Subtitles\n"
            "  - Add Watermark",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back to Menu", callback_data="process_video")]
            ])
        )
    elif action == "process_video":
        if user_id in user_data and 'file' in user_data[user_id]:
            show_processing_menu(client, user_id)
        else:
            client.send_message(user_id, "Please upload a video file first.")
    elif action in ["change_metadata", "change_audio", "merge_files", "extract_audio",
                    "convert_format", "split_video", "compress_video", "resize_video",
                    "add_subtitles", "add_watermark"]:
        processing_actions[user_id] = action
        prompt_for_action(client, user_id, action)

def show_processing_menu(client, user_id):
    client.send_message(
        user_id,
        "Choose an action:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Change Metadata", callback_data="change_metadata")],
            [InlineKeyboardButton("Change Audio Track", callback_data="change_audio")],
            [InlineKeyboardButton("Merge Files", callback_data="merge_files")],
            [InlineKeyboardButton("Extract Audio", callback_data="extract_audio")],
            [InlineKeyboardButton("Convert Format", callback_data="convert_format")],
            [InlineKeyboardButton("Split Video", callback_data="split_video")],
            [InlineKeyboardButton("Compress Video", callback_data="compress_video")],
            [InlineKeyboardButton("Resize Video", callback_data="resize_video")],
            [InlineKeyboardButton("Add Subtitles", callback_data="add_subtitles")],
            [InlineKeyboardButton("Add Watermark", callback_data="add_watermark")],
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

def prompt_for_action(client, user_id, action):
    prompts = {
        "change_metadata": "Send the metadata in `key=value` format. Example: `title=New Title`.",
        "change_audio": "Send the audio track file to replace the existing one.",
        "merge_files": "Upload additional files for merging. Once done, send the output filename with `-n filename.mkv`.",
        "extract_audio": "Send the desired output audio file name (e.g., `output.mp3`).",
        "convert_format": "Send the desired output format (e.g., `mp4`).",
        "split_video": "Send the start time and duration in the format `start_time duration`. Example: `00:00:00 00:00:30`.",
        "compress_video": "Send the desired bitrate (e.g., `1M`).",
        "resize_video": "Send the new width and height in the format `width height`. Example: `1280 720`.",
        "add_subtitles": "Send the subtitles file to add.",
        "add_watermark": "Send the watermark file to add."
    }
    client.send_message(user_id, prompts[action])

def handle_text_action(client, user_id, action, text):
    try:
        if action == "change_metadata":
            output_file = user_data[user_id]['file']
            success = change_metadata(output_file, output_file, text)
            response = "Metadata changed successfully!" if success else "Failed to change metadata."
        
        elif action == "extract_audio":
            output_file = text
            video_file = user_data[user_id]['file']
            success = extract_audio(video_file, output_file)
            response = "Audio extracted successfully!" if success else "Failed to extract audio."
        
        elif action == "convert_format":
            output_format = text
            video_file = user_data[user_id]['file']
            output_file = f"converted_{int(time.time())}.{output_format}"
            success = convert_video_format(video_file, output_format, output_file)
            response = "Format converted successfully!" if success else "Failed to convert format."
        
        elif action == "split_video":
            start_time, duration = text.split()
            video_file = user_data[user_id]['file']
            output_file = f"split_{int(time.time())}.mp4"
            success = split_video(video_file, start_time, duration, output_file)
            response = "Video split successfully!" if success else "Failed to split video."
        
        elif action == "compress_video":
            bitrate = text
            video_file = user_data[user_id]['file']
            output_file = f"compressed_{int(time.time())}.mp4"
            success = compress_video(video_file, bitrate, output_file)
            response = "Video compressed successfully!" if success else "Failed to compress video."
        
        elif action == "resize_video":
            width, height = text.split()
            video_file = user_data[user_id]['file']
            output_file = f"resized_{int(time.time())}.mp4"
            success = resize_video(video_file, width, height, output_file)
            response = "Video resized successfully!" if success else "Failed to resize video."
        
        client.send_document(user_id, output_file)
        client.send_message(user_id, response)

    except Exception as e:
        client.send_message(user_id, f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app.run()
    
