from asyncio.subprocess import PIPE, create_subprocess_exec
from subprocess import call

from .config import ROOT
from .log import server_log


async def uv_run(uv_scripts: str, *args: str, **kwargs: str):
    args = (*args, *(f"--{k}={v}" for k, v in kwargs.items()))
    process = await create_subprocess_exec(
        "uv", "run", uv_scripts, *map(str, args), stdout=PIPE, stderr=PIPE, cwd=ROOT
    )
    stdout, stderr = await process.communicate()
    if stdout:
        server_log.info(f"UV script {uv_scripts} output: {stdout.decode()}")
    if stderr:
        server_log.warning(f"Error running uv script {uv_scripts}: {stderr.decode()}")
    return stdout


try:
    call(["uv", "--version"], stdout=PIPE, stderr=PIPE)
    uv_available = True
except FileNotFoundError:
    uv_available = False
