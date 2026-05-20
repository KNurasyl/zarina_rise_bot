from app.content_seed import seed_content_templates


async def seed_contents() -> None:
    await seed_content_templates()
