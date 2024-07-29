from pyrogram import Client
from mutagen import File
from pydub import AudioSegment
import os
from pyrogram.types import Message

def progress(current, total, message: Message):
    progress_percentage = current * 100 // total
    message.edit_text(f"Processing: {progress_percentage}%")

def modify_file(client: Client, message: Message, thumbnail=None):
    file_id = message.document or message.video
    file = client.download_file(file_id, progress=lambda current, total: progress(current, total, message))
    file_name = file.name

    # Check if the file has a command
    if message.caption and message.caption.startswith('/p'):
        options = message.caption.split(' ')[1:]
        metadata = None
        audio_index = None
        new_name = None

        for option in options:
            if option.startswith('-m'):
                metadata = option[3:]
            elif option.startswith('-ai'):
                audio_index = option[4:]
            elif option.startswith('-n'):
                new_name = option[3:]

        if metadata or audio_index or new_name:
            if file_name.endswith(('.mp3', '.mp4', '.mkv')):  # Check file extensions
                if metadata:
                    # Modify metadata using mutagen
                    metadata = File(file)
                    metadata['title'] = metadata
                    metadata.save()

                if audio_index:
                    # Modify audio index using pydub
                    audio = AudioSegment.from_file(file)
                    audio.set_tags(tags={'tracknumber': audio_index})
                    audio.export(file, format='mp3')

                if new_name:
                    # Rename the file
                    os.rename(file, new_name)

                if thumbnail:
                    # Send the output file with the thumbnail
                    client.send_document(chat_id=message.chat.id, document=file, thumb=thumbnail)
                else:
                    # Send the output file without a thumbnail
                    client.send_document(chat_id=message.chat.id, document=file)
            else:
                message.reply_text('Unsupported file format. Please use mp3, mp4, or mkv files.')
        else:
            message.reply_text('No options provided. Please use /p -m <metadata> -ai <audio_index> -n <new_name>')
    else:
        message.reply_text('No command provided. Please use /p with options.')
