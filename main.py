import os
import tempfile
import logging
import subprocess
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from utils import run_ffmpeg_command, send_progress_update, get_video_dimensions, DEFAULT_SETTINGS, user_files, user_file_names, user_thumbnails, user_settings, progress_messages

# Setup logging
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.DEBUG,  # Changed to DEBUG to capture more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Client("merge_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(_, message):
    try:
        await message.reply_text(
            "Send me files, and use /list to view your files. Use /merge N to combine the first N files. Use /thumbnail to set a thumbnail. Use /settings to configure output format, font style, and other preferences."
        )
    except Exception as e:
        logger.error(f"Error in /start command: {e}", exc_info=True)

@app.on_message(filters.command("help"))
async def help(_, message):
    try:
        await message.reply_text(
            "Send files to me, use /list to view your files, /merge N to combine the first N files, /thumbnail to set a thumbnail, and /settings to configure output format, font style, and other preferences."
        )
    except Exception as e:
        logger.error(f"Error in /help command: {e}", exc_info=True)

@app.on_message(filters.document)
async def receive_files(_, message):
    user_id = message.from_user.id
    if user_id not in user_files:
        user_files[user_id] = []
        user_file_names[user_id] = []
        user_settings[user_id] = DEFAULT_SETTINGS.copy()

    try:
        # Download the file asynchronously
        file_path = await message.download()
        file_name = message.document.file_name
        user_files[user_id].append(file_path)
        user_file_names[user_id].append(file_name)

        # Notify the user
        await message.reply_text(
            f"File received: {file_name}! Total files: {len(user_files[user_id])}. Please send the desired output filename."
        )
    except Exception as e:
        logger.error(f"Error receiving file from user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred while processing your file.")

@app.on_message(filters.text & ~filters.command(["start", "help", "settings", "merge"]))
async def receive_filename(_, message):
    user_id = message.from_user.id
    if user_id not in user_files or not user_files[user_id]:
        await message.reply_text("Please send some files first.")
        return

    try:
        user_settings[user_id]["output_filename"] = message.text.strip()
        await message.reply_text(
            f"Output filename set to {message.text.strip()}. Use /list to view your files and /merge N to combine the first N files."
        )
    except Exception as e:
        logger.error(f"Error setting output filename for user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred while setting the output filename.")

@app.on_message(filters.photo)
async def receive_thumbnail(_, message):
    user_id = message.from_user.id

    try:
        # Download the thumbnail asynchronously
        thumb_path = await message.download()
        user_thumbnails[user_id] = thumb_path

        # Notify the user
        await message.reply_text("Thumbnail received! It will be used for your next merged video.")
    except Exception as e:
        logger.error(f"Error receiving thumbnail from user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred while processing your thumbnail.")

@app.on_message(filters.command("list"))
async def list_files(_, message):
    user_id = message.from_user.id
    if user_id not in user_files or not user_files[user_id]:
        await message.reply_text("You haven't uploaded any files yet.")
        return

    try:
        file_list = "\n".join(f"{i+1}: {file_name}" for i, file_name in enumerate(user_file_names[user_id]))
        await message.reply_text(f"Your files:\n{file_list}")
    except Exception as e:
        logger.error(f"Error listing files for user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred while listing your files.")

@app.on_message(filters.command("merge"))
async def merge_files_command(_, message):
    user_id = message.from_user.id

    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.reply_text("Usage: /merge N where N is the number of files to merge.")
        return

    try:
        num_files = int(command_parts[1])
        if user_id not in user_files or len(user_files[user_id]) < num_files:
            await message.reply_text(f"You need to upload at least {num_files} files before merging.")
            return

        files_to_merge = user_files[user_id][:num_files]
        settings = user_settings.get(user_id, DEFAULT_SETTINGS)
        output_format = settings["output_format"]
        send_as = settings["send_as"]
        output_filename = settings.get("output_filename", f"merged_{user_id}")

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            input_txt_path = f.name
            for file_path in files_to_merge:
                f.write(f"file '{os.path.abspath(file_path)}'\n")

        output_file = f"{output_filename}.{output_format}"
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            input_txt_path,
            "-c",
            "copy",
            output_file,
        ]

        async def handle_progress(output):
            if "frame=" in output and "time=" in output:
                await send_progress_update(message, output)

        returncode = await run_ffmpeg_command(ffmpeg_command, handle_progress)

        if returncode != 0:
            await message.reply_text("An error occurred during merging.")
        else:
            # Get video dimensions
            dimensions = get_video_dimensions(output_file)
            width, height = dimensions if dimensions else ("unknown", "unknown")

            font_style = settings["font_style"]
            if font_style == "bold":
                caption = f"*{output_filename}* ({width}x{height})"
            elif font_style == "italic":
                caption = f"_{output_filename}_ ({width}x{height})"
            elif font_style == "code":
                caption = f"`{output_filename}` ({width}x{height})"
            elif font_style == "mono":
                caption = f"```{output_filename}``` ({width}x{height})"
            else:
                caption = f"{output_filename} ({width}x{height})"

            thumbnail = user_thumbnails.get(user_id)

            if send_as == "video":
                await message.reply_video(video=output_file, caption=caption, thumb=thumbnail)
            elif send_as == "document":
                await message.reply_document(document=output_file, caption=caption, thumb=thumbnail)

    except ValueError:
        await message.reply_text("Invalid number of files specified. Usage: /merge N where N is the number of files to merge.")
    except Exception as e:
        logger.error(f"Error during merging for user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred during the merging process.")
    finally:
        if os.path.exists(input_txt_path):
            os.remove(input_txt_path)
        for file in files_to_merge:
            if os.path.exists(file):
                os.remove(file)
        if user_id in progress_messages:
            await app.delete_messages(message.chat.id, progress_messages[user_id].message_id)
            del progress_messages[user_id]
        if user_id in user_thumbnails:
            os.remove(user_thumbnails[user_id])
            del user_thumbnails[user_id]
        if user_id in user_file_names:
            del user_file_names[user_id]

@app.on_message(filters.command("settings"))
async def settings(_, message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) < 2:
        await message.reply_text(
            "Usage: /settings option value\nAvailable options: output_format, font_style, send_as"
        )
        return

    option = command_parts[1].lower()
    value = command_parts[2].lower() if len(command_parts) > 2 else None

    try:
        if option == "output_format":
            if value in ["mkv", "mp4"]:
                user_settings.setdefault(user_id, DEFAULT_SETTINGS.copy())[
                    "output_format"
                ] = value
                await message.reply_text(f"Output format set to {value}.")
            else:
                await message.reply_text("Invalid format. Available formats: mkv, mp4.")
        elif option == "font_style":
            if value in ["normal", "bold", "italic", "code", "mono"]:
                user_settings.setdefault(user_id, DEFAULT_SETTINGS.copy())[
                    "font_style"
                ] = value
                await message.reply_text(f"Font style set to {value}.")
            else:
                await message.reply_text(
                    "Invalid font style. Available styles: normal, bold, italic, code, mono."
                )
        elif option == "send_as":
            if value in ["video", "document"]:
                user_settings.setdefault(user_id, DEFAULT_SETTINGS.copy())[
                    "send_as"
                ] = value
                await message.reply_text(f"Send as set to {value}.")
            else:
                await message.reply_text("Invalid option. Available options: video, document.")
        else:
            await message.reply_text(
                "Invalid option. Available options: output_format, font_style, send_as."
            )
    except Exception as e:
        logger.error(f"Error in /settings command for user {user_id}: {e}", exc_info=True)
        await message.reply_text("An error occurred while updating settings.")

app.run()
