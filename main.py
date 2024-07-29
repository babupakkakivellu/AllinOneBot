import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN
from utils import process_file

app = Client("video_processor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}

@app.on_message(filters.command("start"))
def start(app, message):
    app.send_message(
        message.chat.id,
        "Welcome! Please upload a file to start processing.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

@app.on_message(filters.video | filters.document)
def handle_file(app, message):
    user_id = message.from_user.id
    file_id = message.video.file_id if message.video else message.document.file_id
    file_path = f"downloads/{file_id}"

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    progress_message = app.send_message(user_id, "⚡ Downloading...")

    def progress(current, total):
        percent = int((current / total) * 100)
        bar_length = 10
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '▒' * (bar_length - filled_length)

        speed = current / (time.time() - start_time) if current > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        eta_minutes, eta_seconds = divmod(eta, 60)

        progress_msg = (
            f"⚡ ⚡ Downloading... ɪɴ ᴘʀᴏɢʀᴇss\n\n"
            f"🕛 ᴛɪᴍᴇ ʟᴇғᴛ: {int(eta_minutes)}m, {int(eta_seconds)}s\n\n"
            f"♻️ᴘʀᴏɢʀᴇss: {percent}%\n"
            f"[{bar}]"
        )
        try:
            app.edit_message_text(user_id, progress_message.message_id, progress_msg)
        except Exception as e:
            print(f"Failed to update progress message: {e}")

    start_time = time.time()
    message.download(file_path, progress=progress)
    user_data[user_id] = {'file': file_path}
    app.send_message(
        user_id,
        "File downloaded! Choose an action.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Process File", callback_data="process_file")],
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

@app.on_callback_query()
def callback_handler(app, query: CallbackQuery):
    user_id = query.from_user.id
    action = query.data

    if action == "help":
        app.send_message(
            user_id,
            "Upload a file and then choose an action to process it.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back to Menu", callback_data="process_file")]
            ])
        )
    elif action == "process_file":
        if user_id in user_data and 'file' in user_data[user_id]:
            show_processing_menu(app, user_id)
        else:
            app.send_message(user_id, "Please upload a file first.")

def show_processing_menu(app, user_id):
    app.send_message(
        user_id,
        "Choose an action:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Change Metadata", callback_data="change_metadata")],
            [InlineKeyboardButton("Add Subtitles", callback_data="add_subtitles")],
            [InlineKeyboardButton("Add Watermark", callback_data="add_watermark")],
            [InlineKeyboardButton("Extract Audio", callback_data="extract_audio")],
            [InlineKeyboardButton("Convert Format", callback_data="convert_format")],
            [InlineKeyboardButton("Split Video", callback_data="split_video")],
            [InlineKeyboardButton("Compress Video", callback_data="compress_video")],
            [InlineKeyboardButton("Resize Video", callback_data="resize_video")],
        ])
    )

if __name__ == "__main__":
    app.run()
