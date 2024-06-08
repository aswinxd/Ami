from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import AudioPiped, StreamType
from yt_dlp import YoutubeDL
import os

# Bot configuration
API_ID = "22710783"
API_HASH = "616ea341acfed51f916506c20b8a0a44"
BOT_TOKEN = "6520550784:AAHCm37TCQM9JsX4iV4AX6M8k3UsJ3NZKEA"
SESSION_NAME = "music_bot"

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(app)

# Queue to manage the songs
queue = []

# YTDL options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'quiet': True
}

@app.on_message(filters.command("play") & filters.group)
async def play(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please provide the name of the song.")
        return

    query = " ".join(message.command[1:])
    await message.reply(f"Searching for {query}...")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url = info['url']
        title = info['title']
        ydl.download([url])

    file_path = f"downloads/{title}.mp3"
    queue.append(file_path)

    if len(queue) == 1:
        await start_playback(client, message.chat.id)

    await message.reply(f"Added {title} to the queue.")

async def start_playback(client: Client, chat_id):
    if not queue:
        return

    file_path = queue[0]
    pytgcalls.join_group_call(
        chat_id,
        AudioPiped(file_path, stream_type=StreamType().local_stream)
    )

@app.on_message(filters.command("skip") & filters.group)
async def skip(client: Client, message: Message):
    if not queue:
        await message.reply("Queue is empty.")
        return

    os.remove(queue.pop(0))
    if queue:
        await start_playback(client, message.chat.id)
    else:
        pytgcalls.leave_group_call(message.chat.id)

    await message.reply("Skipped the current song.")

@app.on_message(filters.command("pause") & filters.group)
async def pause(client: Client, message: Message):
    pytgcalls.pause_stream(message.chat.id)
    await message.reply("Paused the playback.")

@app.on_message(filters.command("resume") & filters.group)
async def resume(client: Client, message: Message):
    pytgcalls.resume_stream(message.chat.id)
    await message.reply("Resumed the playback.")

@app.on_message(filters.command("end") & filters.group)
async def end(client: Client, message: Message):
    pytgcalls.leave_group_call(message.chat.id)
    queue.clear()
    await message.reply("Ended the playback and cleared the queue.")

@pytgcalls.on_stream_end()
async def on_stream_end(client, update):
    if queue:
        os.remove(queue.pop(0))
        if queue:
            await start_playback(client, update.chat_id)
        else:
            await pytgcalls.leave_group_call(update.chat_id)

app.start()
pytgcalls.start()
idle()
