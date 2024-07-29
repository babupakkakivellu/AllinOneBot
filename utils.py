import subprocess
import os
import re

def run_ffmpeg_command(command, progress_callback=None):
    """Run an FFmpeg command and report progress."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    total_duration = 1  # Default to 1 to avoid division by zero
    for line in process.stderr:
        if progress_callback:
            # Example for extracting time information, adjust based on actual output
            match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', line)
            if match:
                hours, minutes, seconds, milliseconds = map(int, match.groups())
                current_time = hours * 3600 + minutes * 60 + seconds + milliseconds / 100
                progress = (current_time / total_duration) * 100
                progress_callback(int(progress))
    
    process.wait()
    return process.returncode == 0

def merge_mkv_files(input_files, output_file, progress_callback=None):
    """Merge multiple MKV files into one using FFmpeg and report progress."""
    # Create a file list for FFmpeg concat demuxer
    list_file = 'files.txt'
    with open(list_file, 'w') as f:
        for file in input_files:
            f.write(f"file '{file}'\n")
    
    # Use FFmpeg concat demuxer to merge files
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    result = run_ffmpeg_command(command, progress_callback_wrapper)
    os.remove(list_file)
    return result

def compress_video(input_file, bitrate, output_file, progress_callback=None):
    """Compress a video file and report progress."""
    command = ['ffmpeg', '-i', input_file, '-b:v', bitrate, output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def change_metadata(input_file, output_file, metadata, progress_callback=None):
    """Change metadata of a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-metadata', metadata, output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def change_audio_track(input_file, audio_file, output_file, progress_callback=None):
    """Change the audio track of a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-i', audio_file, '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def extract_audio(input_file, output_file, progress_callback=None):
    """Extract audio from a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-q:a', '0', '-map', 'a', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def convert_video_format(input_file, output_format, output_file, progress_callback=None):
    """Convert a video file to a different format using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def split_video(input_file, start_time, duration, output_file, progress_callback=None):
    """Split a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-ss', start_time, '-t', duration, output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def resize_video(input_file, width, height, output_file, progress_callback=None):
    """Resize a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-vf', f'scale={width}:{height}', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def add_subtitles(input_file, subtitles_file, output_file, progress_callback=None):
    """Add subtitles to a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-vf', f'subtitles={subtitles_file}', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)

def add_watermark(input_file, watermark_file, output_file, progress_callback=None):
    """Add a watermark to a video file using FFmpeg."""
    command = ['ffmpeg', '-i', input_file, '-i', watermark_file, '-filter_complex', 'overlay=10:10', output_file]
    
    def progress_callback_wrapper(progress):
        if progress_callback:
            progress_callback(progress)
    
    return run_ffmpeg_command(command, progress_callback_wrapper)
