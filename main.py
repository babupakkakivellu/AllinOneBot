# main.py

from pyrogram import Client, filters
import subprocess
import os
import config

# Create a new Client using configuration from config.py
app = Client(
    "shell_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

def find_file(filename, search_path='/'):
    """
    Search for a file in the given directory and subdirectories.
    """
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None

# Define a handler for executing shell commands
@app.on_message(filters.command("exec") & filters.private)
def shell_command(client, message):
    # Extract the command from the message
    command = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
    if command:
        try:
            # Execute the shell command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            # Send the result back to the user
            response = result.stdout if result.stdout else "No output"
            message.reply_text(response)
        except Exception as e:
            message.reply_text(f"Error: {str(e)}")
    else:
        message.reply_text("Please provide a command to execute.")

# Define a handler for uploading files using the filename
@app.on_message(filters.command("up") & filters.private)
def upload_file(client, message):
    # Extract the filename from the message
    filename = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
    if filename:
        file_path = find_file(filename)
        if file_path:
            try:
                # Send the file back to the user
                client.send_document(chat_id=message.chat.id, document=file_path)
            except Exception as e:
                message.reply_text(f"Error: {str(e)}")
        else:
            message.reply_text("File not found. Please check the filename and try again.")
    else:
        message.reply_text("Please provide the filename you want to upload.")

# Run the bot
if __name__ == "__main__":
    app.run()
