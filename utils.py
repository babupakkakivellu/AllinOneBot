# utils.py

import os
import subprocess
import re
from typing import Dict

def ensure_directory(directory: str):
    """Ensure the directory exists, create it if not."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_command(command_text: list) -> Dict[str, str]:
    """Parse the command flags and options."""
    options = {
        'metadata': None,
        'audio': None,
        'new_filename': None,
        'thumbnail_file_id': None,
        'task': 'Processing'
    }

    # Parsing logic
    if '-m' in command_text:
        m_index = command_text.index('-m')
        if m_index + 1 < len(command_text):
            options['metadata'] = command_text[m_index + 1]

    if '-a' in command_text:
        a_index = command_text.index('-a')
        if a_index + 1 < len(command_text):
            options['audio'] = command_text[a_index + 1]

    if '-n' in command_text:
        n_index = command_text.index('-n')
        if n_index + 1 < len(command_text):
            options['new_filename'] = command_text[n_index + 1]

    if '-tn' in command_text:
        tn_index = command_text.index('-tn')
        if tn_index + 1 < len(command_text):
            options['thumbnail_file_id'] = command_text[tn_index + 1]

    return options

def construct_ffmpeg_command(input_file: str, output_file: str, options: Dict[str, str]) -> str:
    """Construct the FFmpeg command based on the options provided."""
    cmd = ['ffmpeg', '-i', input_file]

    # Metadata change
    if options['metadata']:
        cmd.append(f'-metadata:s:v={options["metadata"]}')  # First video stream
        cmd.append(f'-metadata:s:a={options["metadata"]}')  # First audio stream
        cmd.append(f'-metadata:s:s={options["metadata"]}')  # First subtitle stream

    # Audio track change
    if options['audio']:
        audio_tracks = options['audio'].split('-')
        for idx, track in enumerate(audio_tracks):
            cmd.append(f'-map 0:a:{track} -metadata:s:a:{idx}="Audio Track {idx + 1}"')

    # Output file
    cmd.extend([output_file])

    return ' '.join(cmd)

def parse_duration(line: str) -> float:
    """Parse the duration from FFmpeg output."""
    match = re.search(r'Duration: (\d+:\d+:\d+.\d+)', line)
    if match:
        h, m, s = match.group(1).split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100
    return 0

def parse_time(line: str) -> float:
    """Parse the current time from FFmpeg output."""
    match = re.search(r'time=(\d+:\d+:\d+.\d+)', line)
    if match:
        h, m, s = match.group(1).split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100
    return 0
