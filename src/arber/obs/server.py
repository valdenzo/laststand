from __future__ import annotations

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from arber.config.logging import get_logger

log = get_logger(__name__)


async def _metrics_handler(_: web.Request) -> web.Response:
    payload = generate_latest(REGISTRY)
    return web.Response(body=payload, content_type=CONTENT_TYPE_LATEST.split(";")[0])


async def _health_handler(_: web.Request) -> web.Response:
    return web.Response(text="ok")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/metrics", _metrics_handler)
    app.router.add_get("/healthz", _health_handler)
    return app


async def run_metrics_server(host: str, port: int) -> web.AppRunner:
    app = build_app()
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    log.info("metrics_server_started", host=host, port=port)
    return runner
