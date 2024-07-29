from pyrogram import Client, filters
from pyrogram.types import Message
from utils import download_video, merge_videos, upload_video
from config import API_ID, API_HASH, BOT_TOKEN, VIDEO_DIR

# Create the Pyrogram Client
app = Client("video_merger_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text("Send me video files and I'll merge them for you!")

# Function to handle incoming video messages
@app.on_message(filters.video & filters.private)
async def handle_video(client, message: Message):
    # Download video
    video_file = await download_video(client, message.video.file_id)
    
    await message.reply_text("Video received! Send more or type /merge to start merging.")
    
    # Save file path for merging
    if "videos" not in client.storage:
        client.storage["videos"] = []
    client.storage["videos"].append(video_file)

# Merge command handler
@app.on_message(filters.command("merge") & filters.private)
async def merge_handler(client, message: Message):
    video_paths = client.storage.get("videos", [])
    if len(video_paths) < 2:
        await message.reply_text("Please send at least two videos to merge.")
        return

    output_path = os.path.join(VIDEO_DIR, "merged_video.mkv")

    # Merge videos using utility function
    merge_videos(video_paths, output_path)

    # Send merged video with progress
    await upload_video(client, message.chat.id, output_path)

    # Cleanup
    for p in video_paths:
        os.remove(p)
    os.remove(output_path)
    client.storage["videos"] = []

if __name__ == "__main__":
    app.storage = {}
    app.run()
