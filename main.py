import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import api_id, api_hash, bot_token
from utils import merge_videos, get_video_metadata, download_media_with_progress

# Initialize the bot
app = Client("ffmpeg_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# In-memory user settings and files storage
user_settings = {}
pending_files = {}

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
        f"Caption font: {settings['caption_font']}\n"
        f"Thumbnail: {settings['thumbnail'] or 'None'}\n\n"
        "To change settings, send /set_format <format>, /set_font <font>, or /set_thumbnail <thumbnail>."
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
    thumbnail = message.text.split(maxsplit=1)[1].strip()
    user_settings[user_id] = user_settings.get(user_id, {"upload_format": "video", "caption_font": "default", "thumbnail": None})
    user_settings[user_id]["thumbnail"] = thumbnail
    await message.reply(f"Thumbnail set to {thumbnail}.")

@app.on_message(filters.video & filters.private)
async def receive_videos(client, message: Message):
    user_id = message.from_user.id
    video_file = await download_media_with_progress(client, message.video.file_id, message)

    if user_id not in pending_files:
        pending_files[user_id] = {
            "operation": "merge_videos",
            "videos": [],
            "expected_count": None
        }

    pending_files[user_id]["videos"].append(video_file)

    if pending_files[user_id]["expected_count"] is not None:
        if len(pending_files[user_id]["videos"]) < pending_files[user_id]["expected_count"]:
            remaining_files = pending_files[user_id]["expected_count"] - len(pending_files[user_id]["videos"])
            await message.reply(f"File received. You need to send {remaining_files} more files.")
        else:
            await message.reply("All files received. Please provide the output filename (e.g., merged_video.mkv):")
    else:
        await message.reply("File received. Send more files or type /done when finished.")

@app.on_message(filters.text & filters.private)
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    if user_id in pending_files and "operation" in pending_files[user_id]:
        if pending_files[user_id]["operation"] == "merge_videos":
            if message.text.strip().lower() == "/done":
                if len(pending_files[user_id]["videos"]) > 1:
                    await message.reply("Please provide the output filename (e.g., merged_video.mkv):")
                else:
                    await message.reply("You need to send at least two files to merge.")
            else:
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
                thumb = settings.get("thumbnail")

                if settings["upload_format"] == "video":
                    await client.send_video(
                        message.chat.id,
                        video=output_file,
                        caption=caption,
                        duration=None,  # To be set based on merged video
                        width=None,     # To be set based on merged video
                        height=None,    # To be set based on merged video
                        thumb=thumb,
                        supports_streaming=True
                    )
                else:
                    await client.send_document(
                        message.chat.id,
                        document=output_file,
                        caption=caption
                    )

                for file in video_files:
                    os.remove(file)
                os.remove(output_file)
                
                del pending_files[user_id]

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    if callback_query.data == "help":
        await help_command(client, callback_query.message)
    elif callback_query.data == "merge_videos":
        await callback_query.message.reply("Please send the videos you want to merge. Type /done when finished.")

# Run the bot
app.run()
