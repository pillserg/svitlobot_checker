#!/usr/bin/env python3
"""Simple HTTP server that starts/stops based on ping connectivity."""

import asyncio
import logging

from aiohttp import web

PING_TARGET = "192.168.0.162"
PING_INTERVAL = 10  # seconds


routes = web.RouteTableDef()
@routes.get('/')
async def hello(request):
    logging.info(f"got incoming request: {request}")
    return web.Response(text="OK")


 
async def run_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    logging.info(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        logging.info(f'[stdout]\n{stdout.decode()}')
    if stderr:
        logging.info(f'[stderr]\n{stderr.decode()}')

    return proc.returncode

async def ping(host):
    return (await run_cmd(f"ping -c 1 -W 2 {host}")) == 0
    

async def main():
    host = "0.0.0.0"
    port = 7099
    
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"server up on {host}:{port}")

    logging.info(f"Starting ping monitor (target: {PING_TARGET}, interval: {PING_INTERVAL}s)")

    while True:
        reachable = await ping(PING_TARGET)
        is_server_running = site in runner._sites
        if not reachable and is_server_running:
            logging.info(f"target unreacheble and server running - stop server")
            await site.stop() 
            await runner.cleanup()
        elif reachable and not is_server_running:
            logging.info(f"target reachable and server not running - start server")
            await runner.setup()
            await site.start()
        
        await asyncio.sleep(PING_INTERVAL)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    asyncio.run(main())
