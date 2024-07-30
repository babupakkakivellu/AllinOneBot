# utils.py

import subprocess
import os

def merge_videos(video_files, output_file):
    """Merges a list of video files into a single output file using ffmpeg."""
    with open("filelist.txt", "w") as file_list:
        for video_file in video_files:
            file_list.write(f"file '{video_file}'\n")

    command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "filelist.txt",
        "-c", "copy",
        output_file
    ]
    subprocess.run(command, check=True)

    os.remove("filelist.txt")
