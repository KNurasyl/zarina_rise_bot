import asyncio

from app.content_seed import CONTENT_TEMPLATE_COUNTS
from app.db import db, init_db
from app.seed import seed_contents

MENU = """
Choose an action:

1 - Seed content templates
2 - Show MVP bot commands
3 - Show content category counts
0 - Exit
"""

MVP_COMMANDS = (
    "/start",
    "/help",
    "/today",
    "/focus",
    "/pause",
    "/resume",
    "/compliment",
    "/progress",
    "/settings",
    "/stop",
)


async def show_commands() -> None:
    print("\nZarina Rise MVP commands:\n")
    for command in MVP_COMMANDS:
        print(command)


async def show_content_counts() -> None:
    print("\nContent template categories:\n")
    for category, expected_count in CONTENT_TEMPLATE_COUNTS.items():
        actual_count = await db.content_templates.count_documents(
            {"category": category, "active": True}
        )
        print(f"{category}: {actual_count}/{expected_count}")


async def main() -> None:
    await init_db()

    while True:
        print(MENU)
        choice = input("Choice: ").strip()

        if choice == "1":
            await seed_contents()
            print("Content templates seeded safely.")
        elif choice == "2":
            await show_commands()
        elif choice == "3":
            await show_content_counts()
        elif choice == "0":
            print("Exit.")
            break
        else:
            print("Unknown command.")


if __name__ == "__main__":
    asyncio.run(main())
