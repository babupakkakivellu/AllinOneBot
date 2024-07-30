import os
import subprocess

def merge_videos(video_files, output_file):
    """Merge multiple video files into a single output file."""
    try:
        # Create a text file with the list of videos to merge
        with open("videos_to_merge.txt", "w") as f:
            for video in video_files:
                f.write(f"file '{video}'\n")

        # Run FFmpeg command to merge the videos
        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", "videos_to_merge.txt",
            "-c", "copy",
            output_file
        ]
        subprocess.run(command, check=True)
        
    finally:
        # Clean up the text file
        if os.path.exists("videos_to_merge.txt"):
            os.remove("videos_to_merge.txt")
