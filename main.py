from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram import Client, filters
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, User, Message
from pyrogram.errors import FloodWait
from pyromod import listen
from p_bar import progress_bar
from subprocess import getstatusoutput
from aiohttp import ClientSession
import helper
from logger import logging
import time
import asyncio
from config import *
import sys
import re
import os

CHANNEL_ID = -1001296608859  # Replace with actual channel ID

bot = Client("bot",
             bot_token= "7166620322:AAEahV7BIOMhoa8Uu_jE8-xeI2UI5exOYQc",
             api_id= 9643344,
             api_hash= "06fc5cd597b2ba2cae0638716875e446")


@bot.on_message(filters.command(["start"]) & filters.user(ADMINS))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text(f"Hello [{m.from_user.first_name}](tg://user?id={m.from_user.id})\nPress /Pyro")


@bot.on_message(filters.command("stop") & filters.user(ADMINS))
async def restart_handler(_, m):
    await m.reply_text("**Oh! Fuck 👻**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

# Main bot function
@bot.on_message(filters.command(["Pyro"]) & filters.user(ADMINS))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text(f"**Hey [{m.from_user.first_name}](tg://user?id={m.from_user.id})\nSend txt file**")
    input: Message = await bot.listen(editable.chat.id)
    
    if input.document:
        x = await input.download()
        await bot.send_document(CHANNEL_ID, x)
        await input.delete(True)
        file_name, ext = os.path.splitext(os.path.basename(x))
        credit = f"{m.from_user.first_name}\n`@{m.from_user.username}`"
        try:
            with open(x, "r") as f:
                content = f.read().split("\n")
            os.remove(x)
        except:
            await m.reply_text("Invalid file input.🥲")
            os.remove(x)
            return
    else:
        content = input.text.split("\n")

    links = [i.split("://", 1) for i in content]
    await editable.edit(f"Total links found are **{len(links)}**\n\nSend From where you want to download initial is **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("**Enter Batch Name or send `rexo` for grabbing from text filename.**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    b_name = file_name.replace("_", " ") if raw_text0 == 'rexo' else raw_text0

    await editable.edit("**Enter resolution**")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    res = {
        "144": "256x144",
        "240": "426x240",
        "360": "640x360",
        "480": "854x480",
        "720": "1280x720",
        "1080": "1920x1080"
    }.get(raw_text2, "UN")

    await editable.edit("Now send the **Thumb url**\nEg : ```https://telegra.ph/file/0633f8b6a6f110d34f044.jpg```\n\nor Send `no`")
    input6 = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = None

    count = 1 if len(links) == 1 else int(raw_text)

    for i in range(count - 1, len(links)):
        try:
            V = links[i][1].replace("file/d/", "uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing", "")
            url = "https://" + V

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Pragma': 'no-cache',
                        'Referer': 'http://www.visionias.in/',
                        'Sec-Fetch-Dest': 'iframe',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'cross-site',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                        'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"',
                        'sec-ch-ua-mobile': '?1',
                        'sec-ch-ua-platform': '"Android"',
                    }) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url or 'media-cdn.classplusapp' in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={
                    'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6NTA5MTAzNjYsIm9yZ0lkIjo0MDU0NzMsIm9yZ0NvZGUiOiJqY3d2ayIsIm9yZ05hbWUiOiJTdXJlIDYwIEd1cnVrdWwiLCJuYW1lIjoiUmFtcGFsIiwiZW1haWwiOiJzaGFsaW5pc2hhcm1hMTUwNjhAZ21haWwuY29tIiwibW9iaWxlIjoiOTE5NTIwMDM2ODM0IiwidHlwZSI6MSwiaXNEaXkiOnRydWUsImlzSW50ZXJuYXRpb25hbCI6MCwiZGVmYXVsdExhbmd1YWdlIjoiRU4iLCJjb3VudHJ5Q29kZSI6IklOIiwidGltZXpvbmUiOiJHTVQrNTozMCIsImNvdW50cnlJU08iOiI5MSIsImlzRGl5U3ViYWRtaW4iOjAsImlhdCI6MTcyMDM3MTk2NywiZXhwIjoxNzIwOTc2NzY3fQ.poUEqLjRQWDloQcf0j262flW9tuC5sHMIXAMg3iTYUMpB0Y3r0Xq1OqEdvTxtT9r',  # Replace with actual access token
                    'user-agent': 'Mobile-Android'
                }).json()['url']

            elif '/master.mpd' in url:
                id = url.split("/")[-2]
                url = f"https://d26g5bnklkwsh4.cloudfront.net/{id}/master.m3u8"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("#", "").replace("@", "").replace("*", "").replace("https", "").replace("http", "").replace("_", " ").replace("_pdf", "").replace(".", " ").replace("pdf", " (PDF)").replace("pdf-2", " (PDF-2)").replace("'", "").replace("(perospero)", "REXODAS").strip()
            name = f'By @RolexEmpire {name1[:80]}'

            ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]" if "youtu" in url else f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            cmd = f'yt-dlp -o "{name}.mp4" "{url}"' if "jw-prod" in url else f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            cc = f'{str(count).zfill(3)}.{name1} {res}.mp4\n\n**Batch Name :** {b_name}\n\n**Downloaded By :** {credit}'
            cc1 = f'{str(count).zfill(3)}.{name1}\n\n**Batch Name :** {b_name}\n\n**Downloaded By :** {credit}'
            cc2 = f'{str(count).zfill(3)}.{name1} [Audio File].mp3\n\n**Batch Name :** {b_name}\n\n**Downloaded By :** {credit}'

            if "drive" in url or ".pdf" in url:
                ka = await helper.download(url, name)
                await bot.send_document(m.chat.id, document=ka, caption=cc1, thumb=thumb)
                await bot.send_document(CHANNEL_ID, document=ka, caption=cc1, thumb=thumb)
                count += 1
                os.remove(ka) if os.path.exists(ka) else None
                time.sleep(2)

            elif ".mp3" in url:
                aud = await helper.download_mp3(url, name)
                await bot.send_audio(m.chat.id, audio=aud, caption=cc2)
                await bot.send_audio(CHANNEL_ID, audio=aud, caption=cc2)
                count += 1
                os.remove(aud) if os.path.exists(aud) else None
                time.sleep(1)
            else:
                res_file = await helper.download_video(url, cmd, name)
                filename = res_file
                await helper.send_vid(bot, m, cc, filename, thumb, name)
                count += 1

        except Exception as e:
            await m.reply_text(f"**This #Failed File is not Counted**\n**Name** =>> `{name}`\n**Link** =>> `{url}`\n\n ** failreason »** {e}")
            count += 1
            continue

    await m.reply_text("`Batch Done ✅`")
  
bot.run()
