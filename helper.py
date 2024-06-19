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
    if proc.returncode != 0:
        raise Exception(stderr.decode())
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

async def modify_video(file):
    credit_video_url = "https://telegra.ph/file/4d138511c3fcb531e2f01.mp4"
    credit_video_path = "credit_video.mp4"
    
    # Download credit_video.mp4 if it doesn't exist
    if not os.path.exists(credit_video_path):
        await download_file(credit_video_url, credit_video_path)

    output_file = "output.mp4"
    concat_file = "concat_list.txt"

    # Create a file list for ffmpeg to concatenate
    with open(concat_file, 'w') as f:
        f.write(f"file '{os.path.abspath(credit_video_path)}'\n")
        f.write(f"file '{os.path.abspath(file)}'\n")

    cmd = f'ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_file}'
    await run(cmd)
    
    return output_file

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
            modified_file = await modify_video(name)
            return modified_file
        elif os.path.isfile(f"{name}.webm"):
            modified_file = await modify_video(f"{name}.webm")
            return modified_file
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mkv"):
            modified_file = await modify_video(f"{name}.mkv")
            return modified_file
        elif os.path.isfile(f"{name}.mp4"):
            modified_file = await modify_video(f"{name}.mp4")
            return modified_file
        elif os.path.isfile(f"{name}.mp4.webm"):
            modified_file = await modify_video(f"{name}.mp4.webm")
            return modified_file

        return name
    except FileNotFoundError as exc:
        return os.path.splitext(name)[0] + ".mp4"
