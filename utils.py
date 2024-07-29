# utils.py

import os

def parse_command(command_text):
    """Parse the command text and return the options."""
    # Initialize default values
    options = {
        "metadata_title": "Default Title",
        "input_order": None,
        "new_filename": None
    }

    # Parse the options
    if "-m" in command_text:
        options["metadata_title"] = command_text[command_text.index("-m") + 1]
    
    if "-i" in command_text:
        options["input_order"] = command_text[command_text.index("-i") + 1]
    
    if "-n" in command_text:
        options["new_filename"] = command_text[command_text.index("-n") + 1]

    return options

def construct_ffmpeg_command(video_path, output_path, options):
    """Construct the FFmpeg command based on the options provided."""
    command = f"ffmpeg -i {video_path}"

    if options["input_order"]:
        command += f" -map {options['input_order']}"
    
    command += f" -metadata title='{options['metadata_title']}' {output_path}"

    return command

def ensure_directory(directory):
    """Ensure that a directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
