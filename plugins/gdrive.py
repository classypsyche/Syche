# Ultroid - UserBot
# Copyright (C) 2021-2022 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
✘ Commands Available

• `{i}gdul <reply/file name>`
    Reply to file to upload on Google Drive.
    Add file name to upload on Google Drive.

• `{i}gdown <file id/link> | <filename>`
    Download from Gdrive link or file id.

• `{i}gdsearch <file name>`
    Search file name on Google Drive and get link.

• `{i}gdlist`
    List all GDrive files.

• `{i}gdfolder`
    Link to your Google Drive Folder.
    If added then all files will be uploaded in this folder.
"""

import os
import time

from pyUltroid.functions.gDrive import GDriveManager
from pyUltroid.functions.helper import time_formatter
from telethon.tl.types import Message

from . import asst, eod, eor, get_string, ultroid_cmd

GDrive = GDriveManager()


@ultroid_cmd(
    pattern="gdown ?(.*)",
    fullsudo=True,
)
async def gdown(event):
    match = event.pattern_match.group(1)
    if not match:
        return await eod(event, "`Give file id or Gdrive link to download from!`")
    filename = match.split(" | ")[1].strip() if " | " in match else None
    eve = await event.eor(get_string("com_1"))
    _start = time.time()
    status, response = await GDrive._download_file(eve, match, filename)
    if not status:
        return await eve.edit(response)
    await eve.edit(
        f"`Downloaded ``{response}`` in {time_formatter((time.time() - _start)*1000)}`"
    )


@ultroid_cmd(
    pattern="gdlist$",
    fullsudo=True,
)
async def files(event):
    if not os.path.exists(GDrive.token_file):
        return await event.eor(get_string("gdrive_6").format(asst.me.username))
    eve = await event.eor(get_string("com_1"))
    files = GDrive._list_files
    msg = ""
    if files:
        msg += f"{len(files.keys())} files found in gdrive.\n\n"
        for _ in files:
            msg += f"> [{files[_]}]({_})\n"
    else:
        msg += "Nothing in Gdrive"
    if len(msg) < 4096:
        await eve.edit(msg, link_preview=False)
    else:
        with open("drive-files.txt", "w") as f:
            f.write(
                msg.replace("[", "File Name: ")
                .replace("](", "\n» Link: ")
                .replace(")\n", "\n\n")
            )
        try:
            await eve.delete()
        except BaseException:
            pass
        await event.client.send_file(
            event.chat_id,
            "drive-files.txt",
            thumb="resources/extras/ultroid.jpg",
            reply_to=event,
        )
        os.remove("drive-files.txt")


@ultroid_cmd(
    pattern="gdul ?(.*)",
    fullsudo=True,
)
async def _(event):
    if not os.path.exists(GDrive.token_file):
        return await eod(event, get_string("gdrive_6").format(asst.me.username))
    input_file = event.pattern_match.group(1) or await event.get_reply_message()
    if not input_file:
        return await eod(event, "`Reply to file or give its location.`")
    mone = await event.eor(get_string("com_1"))
    if isinstance(input_file, Message):
        location = "resources/downloads"
        filename = input_file.file.name
        if not filename:
            filename = str(round(time.time()))
        filename = location + "/" + filename
        try:
            filename, downloaded_in = await event.client.fast_downloader(
                file=input_file.media.document,
                filename=filename,
                show_progress=True,
                event=mone,
                message=get_string("com_5"),
            )
            filename = filename.name
        except AttributeError:
            start_time = time.time()
            filename = await event.client.download_media(location, input_file.media)
            downloaded_in = time.time() - start_time
        except Exception as e:
            return await eor(mone, str(e), time=10)
        await mone.edit(
            f"`Downloaded to ``{filename}`` in {time_formatter(downloaded_in*1000)}.`",
        )
    else:
        filename = input_file.strip()
        if not os.path.exists(filename):
            return await eod(
                mone,
                "File Not found in local server. Give me a file path :((",
                time=5,
            )
    folder_id = None
    if os.path.isdir(filename):
        files = os.listdir(filename)
        if not files:
            return await eod(
                mone, "`Requested directory is empty. Can't create empty directory.`"
            )
        folder_id = GDrive.create_directory(filename)
        c = 0
        for files in sorted(files):
            file = filename + "/" + files
            if not os.path.isdir(file):
                try:
                    await GDrive._upload_file(mone, path=file, folder_id=folder_id)
                    c += 1
                except Exception as e:
                    return await mone.edit(
                        f"Exception occurred while uploading to gDrive {e}"
                    )
        return await mone.edit(
            f"`Uploaded `[{filename}](https://drive.google.com/folderview?id={folder_id})` with {c} files.`"
        )
    try:
        g_drive_link = await GDrive._upload_file(
            mone,
            filename,
        )
        await mone.edit(
            get_string("gdrive_7").format(filename.split("/")[-1], g_drive_link)
        )
    except Exception as e:
        await mone.edit(f"Exception occurred while uploading to gDrive {e}")


@ultroid_cmd(
    pattern="gdsearch ?(.*)",
    fullsudo=True,
)
async def _(event):
    if not os.path.exists(GDrive.token_file):
        return await event.eor(get_string("gdrive_6").format(asst.me.username))
    input_str = event.pattern_match.group(1)
    if not input_str:
        return await event.eor("`Give filename to search on GDrive...`")
    eve = await event.eor(f"`Searching for {input_str} in G-Drive...`")
    files = GDrive.search(input_str)
    msg = ""
    if files:
        msg += (
            f"{len(files.keys())} files with {input_str} in title found in GDrive.\n\n"
        )
        for _ in files:
            msg += f"> [{files[_]}]({_})\n"
    else:
        msg += f"`No files with title {input_str}`"
    if len(msg) < 4096:
        await eve.eor(msg, link_preview=False)
    else:
        with open("drive-files.txt", "w") as f:
            f.write(
                msg.replace("[", "File Name: ")
                .replace("](", "\n» Link: ")
                .replace(")\n", "\n\n")
            )
        try:
            await eve.delete()
        except BaseException:
            pass
        await event.client.send_file(
            event.chat_id,
            f"{input_str}.txt",
            thumb="resources/extras/ultroid.jpg",
            reply_to=event,
        )
        os.remove(f"{input_str}.txt")


"""
@ultroid_cmd(
    pattern="udir ?(.*)",
    fullsudo=True,
)
async def _(event):
    if not os.path.exists(TOKEN_FILE):
        return await event.eor(get_string("gdrive_6").format(asst.me.username), time=5)
    input_str = event.pattern_match.group(1)
    if not os.path.isdir(input_str):
        return await event.eor(f"Directory {input_str} does not seem to exist", time=5)

    http = authorize(TOKEN_FILE, None)
    a = await event.eor(f"Uploading `{input_str}` to G-Drive...")
    dir_id = await create_directory(
        http,
        os.path.basename(os.path.abspath(input_str)),
        Redis("GDRIVE_FOLDER_ID"),
    )
    await DoTeskWithDir(http, input_str, event, dir_id)
    dir_link = f"https://drive.google.com/folderview?id={dir_id}"
    await eor(a, get_string("gdrive_7").format(input_str, dir_link), time=5)
"""


@ultroid_cmd(
    pattern="gdfolder$",
    fullsudo=True,
)
async def _(event):
    if not os.path.exists(GDrive.token_file):
        return await event.eor(get_string("gdrive_6").format(asst.me.username))
    if GDrive.folder_id:
        await event.eor(
            "`Here is Your G-Drive Folder link : `\n"
            + "https://drive.google.com/folderview?id="
            + GDrive.folder_id,
        )
    else:
        await eod(event, "Set FOLDERID from your Assistant bot's Settings ")
