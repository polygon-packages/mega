import re
import asyncio
from os import kill
from pathlib import Path
from signal import SIGTERM
from client import TelegramClient
from telethon.events import StopPropagation
from pymegatools import Megatools, MegaError

client: TelegramClient
megatools = Megatools()
dest = Path("mega")

@client.interface(pattern="mega -c ?(.*)")
async def mega_cancel(event):
    try:
        pid = int(
            event.pattern_match.group(1)
        )
        kill(pid, SIGTERM)
    except (TypeError, ValueError, ProcessLookupError):
        await event.edit("`Download not found. (Invalid PID)`")
    else:
        await event.edit(f"`Successfully killed download with pid {pid}`")
    raise StopPropagation

@client.interface(pattern="mega ?(.*)")
async def mega(event):
    if not dest.exists():
        dest.mkdir()

    url = event.pattern_match.group(1)
    filename = None

    if not url:
        # No url provided
        return await event.edit((
            f"Megatools v`{megatools.version}`"
            "\n`.mega url`: Download files from mega.nz to mega folder"
            "\n`.mega -c pid`: Cancel an active download with its pid"
        ))

    await event.edit("`Trying to download..`")

    try:
        filename = megatools.filename(url)
        _, returncode = await megatools.download(
            url,
            progress=telegram_progress,
            progress_arguments=(event,),
            path=dest.name
        )
    except MegaError as err:
        returncode = err.returncode

    unknown_error = f"Whoops! Something went wrong, Return code: {returncode}"
    code_to_string = {
        0: f"Downloaded {filename} successfully." if filename else "Invalid URL.",
        1: "File already exists!\nCheck the mega folder.",
        -15: f'Download for "{filename}" was cancelled'
    }

    try:
        await event.edit(f"`{code_to_string.get(returncode, unknown_error)}`")
    except Exception:
        pass


async def telegram_progress(stream, process, event):
    progress = stream[-1]
    if progress:
        match = re.match(
            "(.*): (.*) - (.*) \(.*\) of (.*) \((.*)\)", progress
        )
        if match:
            await event.edit(
                f"**Downloading:** `{match.group(1)}`\
            \n**Progress:** `{match.group(2)}`\
            \n**Downloaded:** `{match.group(3)}`\
            \n**Total Size:** `{match.group(4)}`\
            \n**Speed:** `{match.group(5)}`\
            \n**PID:** `{process.pid}`\
            \n\n"
            )
        await asyncio.sleep(1)
