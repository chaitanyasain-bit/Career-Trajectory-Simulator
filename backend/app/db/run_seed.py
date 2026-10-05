import asyncio
import logging

from app.db.seed import seed_database
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)

async def main():
    async with AsyncSessionLocal() as session:
        await seed_database(session)

if __name__ == "__main__":
    asyncio.run(main())
