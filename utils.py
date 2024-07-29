import subprocess
import os

def change_metadata(input_file, output_file, metadata):
    """Change metadata of a video file."""
    metadata_args = []
    for key, value in metadata.items():
        metadata_args.append(f"-metadata {key}={value}")
    
    command = [
        'ffmpeg', '-i', input_file, *metadata_args, '-codec', 'copy', output_file
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def change_audio_track(input_file, output_file, audio_index=None, remove_audio=False):
    """Change or remove audio track from a video file."""
    if remove_audio:
        command = ['ffmpeg', '-i', input_file, '-an', output_file]
    else:
        command = ['ffmpeg', '-i', input_file]
        if audio_index is not None:
            command += ['-map', f'0:a:{audio_index}']
        command += ['-c:v', 'copy', '-c:a', 'aac', output_file]
    
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def merge_mkv_files(input_files, output_file):
    """Merge multiple MKV files into one."""
    list_file = 'files.txt'
    with open(list_file, 'w') as f:
        for file in input_files:
            f.write(f"file '{file}'\n")
    
    command = ['mkvmerge', '-o', output_file, '@' + list_file]
    result = subprocess.run(command, capture_output=True, text=True)
    
    os.remove(list_file)
    return result.returncode == 0

def extract_audio(input_file, output_file):
    """Extract audio from a video file."""
    command = ['ffmpeg', '-i', input_file, '-q:a', '0', '-map', 'a', output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def convert_video_format(input_file, output_file):
    """Convert video file to a different format."""
    command = ['ffmpeg', '-i', input_file, output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def split_video(input_file, start_time, duration, output_file):
    """Split a video file into segments."""
    command = ['ffmpeg', '-i', input_file, '-ss', start_time, '-t', duration, '-c', 'copy', output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def compress_video(input_file, bitrate, output_file):
    """Compress a video file to a specified bitrate."""
    command = ['ffmpeg', '-i', input_file, '-b:v', bitrate, output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def resize_video(input_file, width, height, output_file):
    """Resize a video file to specified dimensions."""
    command = ['ffmpeg', '-i', input_file, '-vf', f'scale={width}:{height}', output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def add_subtitles(input_file, subtitle_file, output_file):
    """Add subtitles to a video file."""
    command = ['ffmpeg', '-i', input_file, '-vf', f'subtitles={subtitle_file}', output_file]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def add_watermark(input_file, output_file, watermark_file, position="10:10"):
    """Add a watermark to a video file."""
    command = [
        'ffmpeg', '-i', input_file, '-i', watermark_file, '-filter_complex',
        f"overlay={position}", output_file
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0

def extract_progress_from_line(line):
    """Extract progress percentage from FFmpeg output."""
    import re
    match = re.search(r'frame=\s*\d+\s*fps=\s*\d+\s*q=\s*\d+\s*Lq=\s*\d+\s*size=\s*\d+\s*time=(\d+):(\d+):(\d+)\.(\d+)', line)
    if match:
        hours, minutes, seconds, milliseconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 100
    return 0
