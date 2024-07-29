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

# Similarly, update other functions (like convert_video_format, resize_video) to use run_ffmpeg_command and support progress_callback.
