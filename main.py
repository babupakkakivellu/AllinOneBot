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
import math

app = Client("video_processor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}
processing_actions = {}
progress_messages = {}
previous_messages = {}

def get_progress_bar(current, total):
    percent = int((current / total) * 100)
    bar_length = 20
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '▒' * (bar_length - filled_length)
    return f"[{bar}] {percent}%"

def format_speed(current, elapsed):
    speed = current / elapsed if elapsed > 0 else 0
    size_units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size_unit = size_units[int(math.log(max(speed, 1), 1024))]
    return f"{speed / (1024 ** size_units.index(size_unit)):.2f} {size_unit}/s"

def format_eta(current, total, speed):
    remaining = total - current
    eta = remaining / speed if speed > 0 else 0
    minutes, seconds = divmod(int(eta), 60)
    return f"{minutes}m, {seconds}s"

@app.on_message(filters.command("start"))
def start(app, message):
    app.send_message(
        message.chat.id,
        "Welcome to the Video Processing Bot! Please upload a video file to get started.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

@app.on_message(filters.video)
def handle_video(app, message):
    user_id = message.from_user.id
    file_id = message.video.file_id
    file_path = f"downloads/{file_id}.mp4"

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Notify user of download start
    progress_message = app.send_message(user_id, "⚡ Downloading...")

    def progress(current, total):
        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0
        bar = get_progress_bar(current, total)
        speed_str = format_speed(current, elapsed)
        eta_str = format_eta(current, total, speed)
        progress_msg = (
            f"{bar}\n"
            f"♻️ Processing: {int((current / total) * 100)}%\n"
            f"{current / (1024**2):.1f} MiB of {total / (1024**2):.2f} MiB\n"
            f"Speed: {speed_str}\n"
            f"ETA: {eta_str}"
        )
        # Edit the existing progress message
        if 'message_id' in progress_message:
            app.edit_message_text(user_id, progress_message.message_id, progress_msg)

    start_time = time.time()
    message.download(file_path, progress=progress)

    # Notify user after download completion
    user_data[user_id] = {'file': file_path}

    # Delete previous messages (progress and buttons)
    if user_id in previous_messages:
        for msg_id in previous_messages[user_id]:
            app.delete_messages(user_id, msg_id)
        del previous_messages[user_id]

    app.send_message(
        user_id,
        "File downloaded successfully! Choose an action from the menu.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Process Video", callback_data="process_video")],
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )
    
    # Store message IDs to delete later
    previous_messages[user_id] = [progress_message.message_id]

@app.on_message(filters.document)
def handle_document(app, message):
    user_id = message.from_user.id

    if user_id in processing_actions:
        action = processing_actions[user_id]
        try:
            # Notify user of file download start
            progress_message = app.send_message(user_id, "⚡ Downloading...")

            def progress(current, total):
                elapsed = time.time() - start_time
                speed = current / elapsed if elapsed > 0 else 0
                bar = get_progress_bar(current, total)
                speed_str = format_speed(current, elapsed)
                eta_str = format_eta(current, total, speed)
                progress_msg = (
                    f"{bar}\n"
                    f"♻️ Processing: {int((current / total) * 100)}%\n"
                    f"{current / (1024**2):.1f} MiB of {total / (1024**2):.2f} MiB\n"
                    f"Speed: {speed_str}\n"
                    f"ETA: {eta_str}"
                )
                # Edit the existing progress message
                if 'message_id' in progress_message:
                    app.edit_message_text(user_id, progress_message.message_id, progress_msg)

            start_time = time.time()
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
                app.send_message(user_id, "File added to merge list. Send more files if needed, or send the output filename with `-n filename.mkv` to start merging.")
            
            # Delete previous messages (progress and buttons)
            if user_id in previous_messages:
                for msg_id in previous_messages[user_id]:
                    app.delete_messages(user_id, msg_id)
                del previous_messages[user_id]

            app.send_document(user_id, output_file)
            app.send_message(user_id, response)

            del processing_actions[user_id]
        
        except Exception as e:
            app.send_message(user_id, f"An error occurred: {str(e)}")

@app.on_callback_query()
def callback_handler(app, query: CallbackQuery):
    user_id = query.from_user.id
    action = query.data

    if action == "help":
        app.send_message(
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
            show_processing_menu(app, user_id)
        else:
            app.send_message(user_id, "Please upload a video file first.")
    elif action in ["change_metadata", "change_audio", "merge_files", "extract_audio",
                    "convert_format", "split_video", "compress_video", "resize_video",
                    "add_subtitles", "add_watermark"]:
        processing_actions[user_id] = action
        prompt_for_action(app, user_id, action)

def show_processing_menu(app, user_id):
    app.send_message(
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
        ])
    )

def prompt_for_action(app, user_id, action):
    prompts = {
        "change_metadata": "Send the metadata you want to change (e.g., Title, Artist).",
        "change_audio": "Upload the audio track you want to add.",
        "merge_files": "Upload additional files for merging. Once done, send the output filename with `-n filename.mkv`.",
        "extract_audio": "Send the desired output audio file name (e.g., `output.mp3`).",
        "convert_format": "Send the desired output format (e.g., `mp4`).",
        "split_video": "Send the start time and duration in the format `start_time duration`. Example: `00:00:00 00:00:30`.",
        "compress_video": "Send the desired bitrate (e.g., `1M`).",
        "resize_video": "Send the new width and height in the format `width height`. Example: `1280 720`.",
        "add_subtitles": "Send the subtitles file to add.",
        "add_watermark": "Send the watermark file to add."
    }
    app.send_message(user_id, prompts[action])

if __name__ == "__main__":
    app.run()
