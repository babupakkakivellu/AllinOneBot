import subprocess
import os
import asyncio

def merge_videos(video_files, output_file):
    # Create the ffmpeg command to merge videos
    file_list = '|'.join(video_files)
    command = f"ffmpeg -i \"concat:{file_list}\" -c copy \"{output_file}\""

    # Execute the command
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during merging videos: {e}")
        raise

def get_video_metadata(file_path):
    # Run ffprobe to get video metadata
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=duration,width,height", "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        metadata = result.stdout.strip().split('\n')

        if len(metadata) >= 3:
            duration_str, width_str, height_str = metadata[:3]
        else:
            # Handle case where metadata might be incomplete
            duration_str = metadata[0] if len(metadata) > 0 else '0'
            width_str = metadata[1] if len(metadata) > 1 else '0'
            height_str = metadata[2] if len(metadata) > 2 else '0'

        duration = float(duration_str) if duration_str and duration_str not in {'N/A', ''} else 0.0
        width = int(width_str) if width_str and width_str not in {'N/A', ''} else 0
        height = int(height_str) if height_str and height_str not in {'N/A', ''} else 0

        return width, height, duration

    except Exception as e:
        print(f"Error getting video metadata: {e}")
        return 0, 0, 0  # Return default values if an error occurs

async def download_media_with_progress(client, file_id, message):
    # Download the media file with progress tracking
    download_path = os.path.join("downloads", file_id + ".mp4")

    # Initialize progress variables
    progress = 0
    total_size = None
    downloaded_size = 0

    async def update_progress():
        nonlocal progress
        while progress < 100:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=f"Downloading... {progress:.2f}% complete"
            )
            await asyncio.sleep(4)  # Update every 4 seconds

    async def download():
        nonlocal downloaded_size
        async for chunk in client.download_media(file_id, chunk_size=1024*1024):
            downloaded_size += len(chunk)
            if total_size:
                progress = (downloaded_size / total_size) * 100
            else:
                progress = 0
            await update_progress()
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=f"Download complete! File saved as {download_path}"
        )

    # Start the download
    with open(download_path, 'wb') as f:
        await download()

    return download_path
