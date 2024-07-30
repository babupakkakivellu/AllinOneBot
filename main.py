import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import api_id, api_hash, bot_token
from utils import merge_videos, get_video_metadata, get_random_thumbnail

app = Client("ffmpeg_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

user_settings = {}
pending_files = {}

# Function to show download progress
async def download_media_with_progress(client, message, file_id, file_name, chat_id):
    file_size = message.video.file_size
    downloaded = 0
    progress_message = await client.send_message(chat_id, "Starting download...")

    async def progress_callback(current, total):
        nonlocal downloaded
        downloaded = current
        percent = (current / total) * 100
        await progress_message.edit(f"Downloading: {percent:.2f}%")

    downloaded_file = await client.download_media(
        file_id, file_name=file_name, progress=progress_callback
    )
    await progress_message.delete()  # Delete the progress message after download
    return downloaded_file

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Merge Videos", callback_data="merge_videos")]
    ])
    welcome_text = (
        "Welcome to the FFmpeg Bot!\n\n"
        "You can use the following commands:\n"
        "/merge - Merge multiple videos.\n"
        "Send videos one by one, and I will ask for the output filename once all are received.\n"
        "Type /done when finished sending files."
    )
    await message.reply(welcome_text, reply_markup=keyboard)

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    help_text = (
        "Here is how you can use the bot:\n\n"
        "/start - Get a welcome message and instructions.\n"
        "/merge - Start merging videos.\n"
        "Send videos one by one and type /done when finished.\n"
        "Provide a filename for the merged video.\n"
        "You can also use inline buttons for quick actions."
    )
    await message.reply(help_text)

@app.on_message(filters.command("settings") & filters.private)
async def settings_command(client, message: Message):
    user_id = message.from_user.id
    settings = user_settings.get(user_id, {"upload_format": "video", "caption_font": "default", "thumbnail": None})
    settings_text = (
        f"Current settings:\n"
        f"Upload format: {settings['upload_format']}\n"
        f"Caption font: {settings['caption_font']}\n\n"
        "To change settings, send /set_format <format> or /set_font <font>."
    )
    await message.reply(settings_text)

@app.on_message(filters.command("set_format") & filters.private)
async def set_format(client, message: Message):
    user_id = message.from_user.id
    format = message.text.split(maxsplit=1)[1].strip()
    user_settings[user_id] = user_settings.get(user_id, {"upload_format": "video", "caption_font": "default", "thumbnail": None})
    user_settings[user_id]["upload_format"] = format
    await message.reply(f"Upload format set to {format}.")

@app.on_message(filters.command("set_font") & filters.private)
async def set_font(client, message: Message):
    user_id = message.from_user.id
    font = message.text.split(maxsplit=1)[1].strip()
    user_settings[user_id] = user_settings.get(user_id, {"upload_format": "video", "caption_font": "default", "thumbnail": None})
    user_settings[user_id]["caption_font"] = font
    await message.reply(f"Caption font set to {font}.")

@app.on_message(filters.command("set_thumbnail") & filters.private)
async def set_thumbnail(client, message: Message):
    user_id = message.from_user.id
    if message.reply_to_message and message.reply_to_message.photo:
        thumbnail_file = await client.download_media(message.reply_to_message.photo.file_id)
        user_settings[user_id]["thumbnail"] = thumbnail_file
        await message.reply("Thumbnail set successfully.")
    else:
        await message.reply("Please reply to an image message with this command to set a thumbnail.")

@app.on_message(filters.video & filters.private)
async def receive_videos(client, message: Message):
    user_id = message.from_user.id

    if user_id not in pending_files:
        pending_files[user_id] = {
            "operation": "merge_videos",
            "videos": [],
            "expected_count": None
        }

    video_count = len(pending_files[user_id]["videos"]) + 1
    file_name = f"video_{video_count}.mkv"
    video_file = await download_media_with_progress(client, message, message.video.file_id, file_name, message.chat.id)
    pending_files[user_id]["videos"].append(video_file)

    await message.reply(f"{video_count} file{'s' if video_count > 1 else ''} received. Send more files or type /done when finished.")

@app.on_message(filters.text & filters.private)
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    if message.text.strip().lower() == "/done" and user_id in pending_files:
        if pending_files[user_id]["operation"] == "merge_videos":
            if len(pending_files[user_id]["videos"]) > 1:
                await message.reply("Please provide the output filename (e.g., merged_video.mkv):")
            else:
                await message.reply("You need to send at least two files to merge.")
        return

    if user_id in pending_files and "operation" in pending_files[user_id]:
        if pending_files[user_id]["operation"] == "merge_videos":
            filename = message.text.strip()
            if not filename or not filename.lower().endswith(".mkv"):
                await message.reply("Invalid filename. Please provide a filename ending with .mkv.")
                return

            video_files = pending_files[user_id]["videos"]
            output_file = filename

            await message.reply("Merging videos, please wait...")

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, merge_videos, video_files, output_file)

            settings = user_settings.get(user_id, {"upload_format": "video", "caption_font": "default", "thumbnail": None})
            caption = "Videos merged successfully!"

            # Get metadata for video
            duration, width, height = get_video_metadata(output_file)
            thumb = settings.get("thumbnail")
            if not thumb:
                thumb = get_random_thumbnail(output_file)

            # Upload progress message
            upload_msg = await message.reply("Uploading video, please wait...")
            pending_files[user_id]["upload_message"] = upload_msg.id

            async def update_upload_progress(current, total):
                percent = (current / total) * 100
                await upload_msg.edit(f"Uploading: {percent:.2f}% complete")

            # Upload video or document based on user setting
            if settings["upload_format"] == "video":
                await client.send_video(
                    chat_id=message.chat.id,
                    video=output_file,
                    caption=caption,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    supports_streaming=True,
                    progress=update_upload_progress
                )
            else:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=output_file,
                    caption=caption,
                    progress=update_upload_progress
                )

            # Clean up
            for file in video_files:
                os.remove(file)
            os.remove(output_file)
            
            del pending_files[user_id]
            if settings["thumbnail"]:
                user_settings[user_id]["thumbnail"] = None

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    if callback_query.data == "help":
        await help_command(client, callback_query.message)
    elif callback_query.data == "merge_videos":
        await callback_query.message.reply("Please send the videos you want to merge. Type /done when finished.")

# Run the bot
app.run()
