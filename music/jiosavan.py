import os

import aiohttp

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import modules_help, prefix
from utils.scripts import format_exc

API_URL = "https://elorixapi-2c4d8785ada6.herokuapp.com/result/"


@Client.on_message(filters.command("jsm", prefix) & filters.me)
async def jiosaavn_music(client: Client, message: Message):
    if len(message.command) < 2:
        await message.edit_text(f"<b>Usage:</b> <code>{prefix}jsm [song name]</code>")
        return

    query = message.text.split(maxsplit=1)[1]
    file_path = None
    thumb_path = None

    try:
        await message.edit_text("<code>Searching...</code>")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL, params={"query": query, "lyrics": "true"}
            ) as resp:
                if resp.status != 200:
                    await message.edit_text(
                        f"<b>Error:</b> <code>API returned status {resp.status}</code>"
                    )
                    return
                data = await resp.json()

        if not data:
            await message.edit_text("<b>No results found.</b>")
            return

        track = data[0]
        media_url = track.get("media_url")
        if not media_url:
            await message.edit_text(
                "<b>No playable audio found for this track.</b>"
            )
            return

        title = track.get("song", "Unknown")
        artist = track.get("primary_artists", "Unknown")
        album = track.get("album", "")
        thumb_url = track.get("image", "")
        song_id = track.get("id", "jsm")

        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{song_id}.m4a"

        await message.edit_text(f"<code>Downloading {title}...</code>")

        async with aiohttp.ClientSession() as session:
            async with session.get(media_url) as resp:
                if resp.status != 200:
                    await message.edit_text(
                        f"<b>Error:</b> <code>Failed to download audio ({resp.status})</code>"
                    )
                    return
                with open(file_path, "wb") as f:
                    f.write(await resp.read())

        if thumb_url:
            thumb_path = f"downloads/{song_id}.jpg"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumb_url) as resp:
                        if resp.status == 200:
                            with open(thumb_path, "wb") as f:
                                f.write(await resp.read())
                        else:
                            thumb_path = None
            except Exception:
                thumb_path = None

        await message.edit_text("<code>Uploading...</code>")

        await client.send_audio(
            message.chat.id,
            audio=file_path,
            title=title,
            performer=artist,
            thumb=thumb_path,
            caption=f"<b>{title}</b>\n<b>Artist:</b> {artist}\n<b>Album:</b> {album}",
        )

        await message.delete()

    except Exception as e:
        await message.edit_text(f"<b>Error:</b> <code>{format_exc(e)}</code>")

    finally:
        for path in (file_path, thumb_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


modules_help["jiosavan"] = {
    "jsm [song name]": "Search JioSaavn and send the audio for the top match",
}
