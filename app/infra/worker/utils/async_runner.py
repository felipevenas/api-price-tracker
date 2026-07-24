import asyncio


def run_async(coro):
    """Executa uma coroutine em contexto síncrono (Celery worker)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
