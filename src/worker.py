import asyncio
import logging

from src.shared.database.engine import close_database, init_database
from src.shared.queue.app import queue_app


async def main() -> None:
    await init_database()
    try:
        async with queue_app.open_async():
            await queue_app.run_worker_async(queues=["recording"])
    finally:
        await close_database()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
