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
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(ka, mode='wb')
                    await f.write(await resp.read())
                    await f.close()  # Manually closing the file
                    return ka
    except Exception as e:
        print("Asynchronous download failed, Now will try synchronously. Error:", e)

    # Synchronous FallBack (Rexo)
    try:
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            print("Error:", url)
            return None
        with open(ka, "wb") as f:
            f.write(r.content)
            f.close()  # Manually closing the file
        print("Downloaded Synchronously:", ka)
        return ka
    except Exception as e:
        print("Synchronous Download Failed. Error:", e)

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

#for audio download 
async def download_mp3(url, name):
    aud = f'{name}.mp3'
    cmd = f'yt-dlp -x --audio-format mp3 -o "{aud}" "{url}"'
    process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"yt-dlp failed: {stderr.decode().strip()}")
    
    return aud
    
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



async def send_vid(bot: Client, m: Message, cc, filename, thumb, name):

    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
    
    #subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:12 -filter_complex "drawtext=text=\'Rexodas\':fontcolor=black@0.5:fontsize=(w/20):x=10:y=h-th-10+2:shadowcolor=white:shadowx=2:shadowy=2" -vframes 1 "{filename}.jpg"', shell=True)
    
  # await prog.delete (True)
    reply = await m.reply_text(f"**Downloading Over !**\n\n**Uploading** 📥To Telegram\n\n𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 𝐑𝐄𝐗𝐎𝐃𝐀𝐒 🇮🇳")
    try:
        if thumb == "no":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb
    except Exception as e:
        await m.reply_text(str(e))

    dur = int(duration(filename))

    start_time = time.time()

    try:
        copy = await bot.send_video(chat_id=m.chat.id,video=filename,caption=cc, supports_streaming=True,height=720,width=1280,thumb=thumbnail,duration=dur,progress=progress_bar,progress_args=(reply,start_time))
        await copy.copy(chat_id = LOG) 
    except TimeoutError:
        await asyncio.sleep(5) 
        copy = await bot.send_video(chat_id=m.chat.id,video=filename,caption=cc, supports_streaming=True,height=720,width=1280,thumb=thumbnail,duration=dur,progress=progress_bar,progress_args=(reply,start_time))
        await copy.copy(chat_id = LOG)       
    except Exception:
        copy = await bot.send_video(chat_id=m.chat.id,video=filename,caption=cc, supports_streaming=True,height=720,width=1280,thumb=thumbnail,duration=dur,progress=progress_bar,progress_args=(reply,start_time))
        await copy.copy(chat_id = LOG)


    os.remove(filename)

    os.remove(f"{filename}.jpg")
    await reply.delete(True)
  # await prog.delete(True)

def decrypt_pdf_data(pdf_data, key):
    max_length = 28
    data_length = len(pdf_data)
    if data_length < 28:
        max_length = data_length
    for index in range(max_length):
        current_byte = pdf_data[index]
        if index <= len(key)-1:
            decrypted_byte = current_byte ^ ord(key[index])
        else:
            decrypted_byte = current_byte ^ index
        pdf_data[index] = decrypted_byte
    return pdf_data


def download_pdf(pdf_url, pdf_key, pdf_path):
    try:
        response = requests.get(pdf_url, verify=False)
        if response.status_code == 200:
            encrypted_pdf_data = bytearray(response.content)
            decrypted_pdf_data = decrypt_pdf_data(encrypted_pdf_data, pdf_key)
            with open(pdf_path, 'wb') as f:
                f.write(decrypted_pdf_data)
            print("Decrypted PDF saved to: {pdf_path}")
            return pdf_path
        else:
            print("Failed to download the PDF file. HTTP status code: {
                  response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
