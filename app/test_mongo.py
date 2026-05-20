import asyncio

from app.db import db


async def main() -> None:
    result = await db.command("ping")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
