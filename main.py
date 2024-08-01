# main.py

from pyrogram import Client, filters
import os
import subprocess
import zipfile
import config  # Import the config module

# Initialize the Pyrogram client using the configurations from config.py
app = Client("shell_bot", api_id=config.api_id, api_hash=config.api_hash, bot_token=config.bot_token)

# Base directory where files and folders are located
BASE_DIR = "/path/to/base_directory"  # Set this to the base directory for your files

# Helper function to check if a user is allowed
def is_user_allowed(user_id):
    return user_id in config.allowed_users

# Helper function to zip a directory
def zip_directory(directory_path):
    zip_file = f"{directory_path}.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, directory_path))
    return zip_file

# Function to send a message or a file if the message is too long
def send_message_or_file(client, chat_id, text, file_name="output.txt"):
    if len(text) > 4096:  # Telegram's message limit
        with open(file_name, "w") as f:
            f.write(text)
        client.send_document(chat_id, file_name)
        os.remove(file_name)  # Clean up the file after sending
    else:
        client.send_message(chat_id, text)

# Function to send a file as a video
def send_video(client, chat_id, file_path):
    client.send_video(chat_id, video=file_path)

# Command to execute shell commands
@app.on_message(filters.command("shell"))
def shell_command(client, message):
    if not is_user_allowed(message.from_user.id):
        message.reply_text("You are not authorized to use this command.")
        return

    try:
        command = message.text.split(maxsplit=1)[1]  # Get the command from the message
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        send_message_or_file(client, message.chat.id, f"Output:\n{output}")
    except Exception as e:
        message.reply_text(f"Error: {str(e)}")

# Command to upload a file or directory as a video or zip file
@app.on_message(filters.command("upload"))
def upload_item(client, message):
    if not is_user_allowed(message.from_user.id):
        message.reply_text("You are not authorized to use this command.")
        return

    try:
        item_name = message.text.split(maxsplit=1)[1]  # Get the file or folder name
        item_path = os.path.join(BASE_DIR, item_name)  # Create the full path

        if os.path.isfile(item_path):
            if item_path.lower().endswith(('.mkv', '.mp4')):
                # Send the file as a video
                send_video(client, message.chat.id, item_path)
            else:
                # If it's not a video, zip it before sending
                zip_file = zip_directory(item_path)
                message.reply_document(zip_file)
                os.remove(zip_file)  # Clean up the zip file after sending
        elif os.path.isdir(item_path):
            # Zip the directory and send as a document
            zip_file = zip_directory(item_path)
            message.reply_document(zip_file)
            os.remove(zip_file)  # Clean up the zip file after sending
        else:
            message.reply_text("Invalid file or directory name.")
    except Exception as e:
        message.reply_text(f"Error: {str(e)}")

# Command to download a file to a directory
@app.on_message(filters.command("download") & filters.reply)
def download_file(client, message):
    if not is_user_allowed(message.from_user.id):
        message.reply_text("You are not authorized to use this command.")
        return

    try:
        if not message.reply_to_message.document:
            message.reply_text("Please reply to a document to download.")
            return

        directory_name = message.text.split(maxsplit=1)[1]  # Get the target directory name
        directory_path = os.path.join(BASE_DIR, directory_name)
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)

        file_id = message.reply_to_message.document.file_id
        file_name = message.reply_to_message.document.file_name
        download_path = os.path.join(directory_path, file_name)
        client.download_media(file_id, file_name=download_path)
        message.reply_text(f"Downloaded to {download_path}")
    except Exception as e:
        message.reply_text(f"Error: {str(e)}")

# Command to clean (delete) a file or folder
@app.on_message(filters.command("clean"))
def clean_item(client, message):
    if not is_user_allowed(message.from_user.id):
        message.reply_text("You are not authorized to use this command.")
        return

    try:
        item_name = message.text.split(maxsplit=1)[1]  # Get the file or folder name
        item_path = os.path.join(BASE_DIR, item_name)  # Create the full path

        if os.path.isfile(item_path):
            os.remove(item_path)
            message.reply_text(f"File '{item_name}' deleted successfully.")
        elif os.path.isdir(item_path):
            os.rmdir(item_path)  # Use os.rmdir() to delete an empty directory
            message.reply_text(f"Directory '{item_name}' deleted successfully.")
        else:
            message.reply_text("Invalid file or directory name.")
    except Exception as e:
        message.reply_text(f"Error: {str(e)}")

# Start the bot
app.run()
