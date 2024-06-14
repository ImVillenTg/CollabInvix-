import logging
import subprocess
import datetime
import asyncio
import os
import requests
import time
from p_bar import progress_bar
from config import LOG
import aiohttp
import tgcrypto
import aiofiles
from pyrogram.types import Message
from pyrogram import Client, filters


def duration(filename):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", filename
    ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


async def download(url, name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka



async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'


def old_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


async def download_video(url, cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    global failed_counter
    print(download_cmd)
    logging.info(download_cmd)
    k = subprocess.run(download_cmd, shell=True)
    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        await download_video(url, cmd, name)
    failed_counter = 0
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        elif os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.mp4.webm"):
            return f"{name}.mp4.webm"

        return name
    except FileNotFoundError as exc:
        return os.path.isfile.splitext[0] + "." + "mp4"


async def add_watermark(filename, watermark_text):
    try:
        # Add watermark using ffmpeg
        subprocess.run(
            f'ffmpeg -i "{filename}" -vf "drawtext=text=\'{watermark_text}\':x=(w-text_w-10):y=(h-text_h-10):fontsize=24:fontcolor=white@0.5:shadowcolor=black:shadowx=2:shadowy=2" -codec:a copy "{filename}_watermarked.mp4"',
            shell=True,
            check=True
        )
        return f"{filename}_watermarked.mp4"
    except subprocess.CalledProcessError as e:
        print(f"Error adding watermark: {e}")
        return None

async def send_vid(bot, m, cc, filename, thumb, name):
    # Generate watermark text
    watermark_text = "DRAGO"

    # Add watermark to the video
    watermarked_filename = await add_watermark(filename, watermark_text)
    if watermarked_filename is None:
        await m.reply_text("Failed to add watermark.")
        return

    # Get thumbnail or use default
    try:
        if thumb == "no":
            subprocess.run(
                f'ffmpeg -i "{watermarked_filename}" -ss 00:01:00 -vframes 1 "{watermarked_filename}.jpg"',
                shell=True,
                check=True
            )
            thumbnail = f"{watermarked_filename}.jpg"
        else:
            thumbnail = thumb
    except subprocess.CalledProcessError as e:
        await m.reply_text(f"Error generating thumbnail: {e}")
        return

    # Get duration of the video
    dur = int(duration(watermarked_filename))

    start_time = time.time()

    # Send video with watermark
    reply = await m.reply_text(f"**Downloading Over !**\n\n**Uploading** 📥To Telegram\n\n𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 𝐑𝐄𝐗𝐎𝐃𝐀𝐒 🇮🇳")
    try:
        copy = await bot.send_video(
            chat_id=m.chat.id,
            video=watermarked_filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
        await copy.copy(chat_id=LOG)
    except telethon.errors.TimeoutError:
        await asyncio.sleep(5)
        copy = await bot.send_video(
            chat_id=m.chat.id,
            video=watermarked_filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
        await copy.copy(chat_id=LOG)
    except Exception as e:
        await m.reply_text(f"Failed to send video: {str(e)}")

    # Clean up temporary files
    os.remove(watermarked_filename)
    os.remove(f"{watermarked_filename}.jpg")
    await reply.delete(True)

# Example usage:
# await send_vid(bot, m, "Video caption", "input_video.mp4", "no", "Test Video")
