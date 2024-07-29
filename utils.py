# utils.py

import os
import subprocess
import re
from config import DOWNLOAD_DIR

def ensure_directory(directory: str):
    """Ensure the directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_command(command_text):
    """Parse command flags from the input text."""
    options = {
        'task': 'Processing',  # Default task name
        'new_filename': None,
        'audio_swap': None
    }
    
    # Map flags to options
    if '-m' in command_text:
        options['task'] = "Audio Removal"
    elif '-i' in command_text:
        options['task'] = "Audio Track Change"
        if '-a' in command_text:
            a_index = command_text.index('-a')
            if a_index + 1 < len(command_text):
                options['audio_swap'] = command_text[a_index + 1]
    
    # Check for new filename
    if '-n' in command_text:
        n_index = command_text.index('-n')
        if n_index + 1 < len(command_text):
            options['new_filename'] = command_text[n_index + 1]
        else:
            options['new_filename'] = None
    
    return options

def construct_ffmpeg_command(input_file, output_file, options):
    """Construct FFmpeg command based on the given options."""
    command = ["ffmpeg", "-i", input_file]
    
    if options['task'] == "Audio Removal":
        command.extend(["-an"])
    
    elif options['task'] == "Audio Track Change" and options['audio_swap']:
        audio_map = parse_audio_swap(options['audio_swap'])
        command.extend(audio_map)
    
    command.extend(["-c:v", "copy", "-c:a", "copy"])
    
    if options['new_filename']:
        command.append(output_file)
    else:
        command.append(output_file)
    
    return command

def parse_audio_swap(swap_string):
    """Generate FFmpeg map options for swapping audio tracks."""
    # Parse the swap string (e.g., '3-1-2')
    tracks = swap_string.split('-')
    audio_map = []

    # Generate FFmpeg map commands for each track swap
    for index, track in enumerate(tracks):
        audio_map.extend(["-map", f"0:a:{int(track) - 1}"])
    
    return audio_map

def parse_duration(line):
    """Parse total duration from FFmpeg output."""
    match = re.search(r"Duration: (\d+):(\d+):(\d+).(\d+)", line)
    if match:
        hours, minutes, seconds, _ = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return None

def parse_time(line):
    """Parse current time from FFmpeg output."""
    match = re.search(r"time=(\d+):(\d+):(\d+).(\d+)", line)
    if match:
        hours, minutes, seconds, _ = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return 0

async def send_progress_message(message, text, task_id):
    """Send or update a progress message with a cancel button."""
    cancel_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Cancel Task", callback_data=f"cancel_{task_id}")]]
    )
    await message.edit(text, reply_markup=cancel_button)
