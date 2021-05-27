import re
import asyncio
from os import kill
from pathlib import Path
from signal import SIGTERM
from pymegatools import Megatools, MegaError

megatools = Megatools()
dldir = Path("mega")


@polygon.on(pattern="mega -c ?(.*)")
async def megakill(e):
    try:
        pid = int(e.pattern_match.group(1))
        kill(pid, SIGTERM)
    except (TypeError, ValueError, ProcessLookupError):
        await e.edit("`Download not found. (Invalid PID)`")
    else:
        await e.edit(f"`Successfully killed download with pid {pid}`")


@polygon.on(pattern="mega ?(.*)")
async def mega(e):
    if not dldir.exists():
        dldir.mkdir()

    url = e.pattern_match.group(1)
    filename = None

    if not url:
        # No url provided
        return await e.edit((
            f"Megatools v`{megatools.version}`"
            "\n`.mega url`: Download files from mega.nz to mega folder"
            "\n`.mega -c pid`: Cancel an active download with its pid"
        ))
    elif url.startswith("-c"):
        # Call to cancel handler
        return None

    await e.edit("`Trying to download..`")

    try:
        filename = megatools.filename(url)
        _, returncode = await megatools.download(
            url,
            progress=telegram_progress,
            progress_arguments=(e,),
            path=dldir.name
        )
    except MegaError as err:
        returncode = err.returncode

    outputs = {
        -1: f"Whoops! Something went wrong, Return code: {returncode}",
        0: f"Downloaded {filename} successfully." if filename else "Invalid URL.",
        1: "File already exists!\nCheck the mega folder.",
        -15: f'Download for "{filename}" was cancelled'
    }

    try:
        await e.edit(f"`{outputs.get(returncode) or outputs.get(-1)}`")
    except Exception:
        pass


async def telegram_progress(stream, process, e):
    progress = stream[-1]
    if progress:
        match = re.match(
            "(.*): (.*) - (.*) \(.*\) of (.*) \((.*)\)", progress
        )
        if match:
            await e.edit(
                f"**Downloading:** `{match.group(1)}`\
            \n**Progress:** `{match.group(2)}`\
            \n**Downloaded:** `{match.group(3)}`\
            \n**Total Size:** `{match.group(4)}`\
            \n**Speed:** `{match.group(5)}`\
            \n**PID:** `{process.pid}`\
            \n\n"
            )
        await asyncio.sleep(1)
