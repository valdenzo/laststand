from __future__ import annotations

import asyncio
import signal

import uvloop

from arber.config.logging import configure_logging, get_logger
from arber.config.settings import get_settings
from arber.db.engine import create_engine, dispose_engine
from arber.obs.server import run_metrics_server


async def _run() -> None:
    settings = get_settings()
    configure_logging(level=settings.obs.log_level, fmt=settings.obs.log_format)
    log = get_logger(__name__)

    log.info("arber_starting", env=settings.env)
    create_engine()
    runner = await run_metrics_server(settings.obs.metrics_host, settings.obs.metrics_port)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    log.info("arber_ready")
    try:
        await stop.wait()
    finally:
        log.info("arber_shutting_down")
        await runner.cleanup()
        await dispose_engine()
        log.info("arber_stopped")


def main() -> None:
    uvloop.install()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
