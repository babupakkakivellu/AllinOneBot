import ffmpeg
import os
import time

def change_metadata(input_file, metadata, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, **metadata).run()
        return True, "Metadata changed successfully!"
    except Exception as e:
        print(f"Failed to change metadata: {e}")
        return False, f"Error: {e}"

def add_subtitles(input_file, subtitles_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, vf=f"subtitles={subtitles_file}").run()
        return True, "Subtitles added successfully!"
    except Exception as e:
        print(f"Failed to add subtitles: {e}")
        return False, f"Error: {e}"

def add_watermark(input_file, watermark_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, vf=f"movie={watermark_file} [watermark]; [in][watermark] overlay=W-w-10:H-h-10 [out]").run()
        return True, "Watermark added successfully!"
    except Exception as e:
        print(f"Failed to add watermark: {e}")
        return False, f"Error: {e}"

def extract_audio(input_file, output_audio_file):
    try:
        ffmpeg.input(input_file).output(output_audio_file).run()
        return True, "Audio extracted successfully!"
    except Exception as e:
        print(f"Failed to extract audio: {e}")
        return False, f"Error: {e}"

def convert_video_format(input_file, output_file, format):
    try:
        ffmpeg.input(input_file).output(output_file, vcodec=format).run()
        return True, f"Video converted to {format} format!"
    except Exception as e:
        print(f"Failed to convert video format: {e}")
        return False, f"Error: {e}"

def split_video(input_file, start_time, duration, output_file):
    try:
        ffmpeg.input(input_file, ss=start_time, t=duration).output(output_file).run()
        return True, "Video split successfully!"
    except Exception as e:
        print(f"Failed to split video: {e}")
        return False, f"Error: {e}"

def compress_video(input_file, bitrate, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, video_bitrate=bitrate).run()
        return True, "Video compressed successfully!"
    except Exception as e:
        print(f"Failed to compress video: {e}")
        return False, f"Error: {e}"

def resize_video(input_file, width, height, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, vf=f"scale={width}:{height}").run()
        return True, "Video resized successfully!"
    except Exception as e:
        print(f"Failed to resize video: {e}")
        return False, f"Error: {e}"

def progress_bar(current, total, action):
    percent = int((current / total) * 100)
    bar_length = 20
    filled_length = int(bar_length * current // total)
    bar = '■' * filled_length + '▤' * (bar_length - filled_length)
    processed_mb = current / (1024**2)
    total_mb = total / (1024**2)
    status = "Processing" if action == "process" else "Downloading"
    return (
        f"┃ {bar} {percent:.2f}%\n"
        f"┠ Processed: {processed_mb:.2f}MB of {total_mb:.2f}MB\n"
        f"┠ Status: {status} | ETA: TBD\n"
        f"┠ Speed: TBD | Elapsed: TBD\n"
        f"┠ Engine: qBit v4.5.5\n"
        f"┠ Mode: #Leech | #qBit\n"
        f"┠ User: █【﻿ＹＡＡＲ】█ | ID: TBD\n"
        f"┖ /cancel_{int(time.time())}"
    )

def process_file(file_path, action, **kwargs):
    output_file = f"processed_{int(time.time())}.mp4"
    success = False
    message = "Unknown action."
    
    if action == "change_metadata":
        metadata = kwargs.get('metadata', {})
        success, message = change_metadata(file_path, metadata, output_file)
    
    elif action == "add_subtitles":
        subtitles_file = kwargs.get('subtitles_file')
        success, message = add_subtitles(file_path, subtitles_file, output_file)
    
    elif action == "add_watermark":
        watermark_file = kwargs.get('watermark_file')
        success, message = add_watermark(file_path, watermark_file, output_file)
    
    elif action == "extract_audio":
        output_audio_file = kwargs.get('output_audio_file')
        success, message = extract_audio(file_path, output_audio_file)
    
    elif action ==
