import asyncio
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))

import api.repositories as api_repository
import app.repository as app_repository


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]], projection: dict[str, int] | None = None):
        self.documents = [self.apply_projection(document, projection) for document in documents]

    @staticmethod
    def apply_projection(document: dict[str, Any], projection: dict[str, int] | None) -> dict[str, Any]:
        if not projection:
            return deepcopy(document)
        return {key: deepcopy(document[key]) for key, enabled in projection.items() if enabled and key in document}

    def sort(self, key: str, direction: int = 1) -> "FakeCursor":
        self.documents.sort(key=lambda document: document.get(key), reverse=direction < 0)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        if length is None:
            return deepcopy(self.documents)
        return deepcopy(self.documents[:length])


class FakeCollection:
    def __init__(self, documents: list[dict[str, Any]] | None = None):
        self.documents = documents or []

    @staticmethod
    def matches_value(actual: Any, expected: Any) -> bool:
        if isinstance(expected, dict):
            for operator, value in expected.items():
                if operator == "$in" and actual not in value:
                    return False
                if operator == "$gte" and actual < value:
                    return False
                if operator == "$ne" and actual == value:
                    return False
            return True
        return actual == expected

    @classmethod
    def matches(cls, document: dict[str, Any], query: dict[str, Any]) -> bool:
        return all(cls.matches_value(document.get(key), value) for key, value in query.items())

    def find(self, query: dict[str, Any], projection: dict[str, int] | None = None) -> FakeCursor:
        return FakeCursor(
            [document for document in self.documents if self.matches(document, query)],
            projection,
        )

    async def find_one(
        self,
        query: dict[str, Any],
        projection: dict[str, int] | None = None,
        sort: list[tuple[str, int]] | None = None,
    ) -> dict[str, Any] | None:
        documents = [document for document in self.documents if self.matches(document, query)]
        if sort:
            for key, direction in reversed(sort):
                documents.sort(key=lambda document: document.get(key), reverse=direction < 0)
        if not documents:
            return None
        return FakeCursor.apply_projection(documents[0], projection)

    async def insert_one(self, document: dict[str, Any]) -> None:
        self.documents.append(deepcopy(document))

    async def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> None:
        document = next((item for item in self.documents if self.matches(item, query)), None)
        if document is None:
            if not upsert:
                return
            document = {
                key: deepcopy(value)
                for key, value in query.items()
                if not isinstance(value, dict)
            }
            document.update(deepcopy(update.get("$setOnInsert", {})))
            self.documents.append(document)

        document.update(deepcopy(update.get("$set", {})))


class FakeDb:
    def __init__(self, templates: list[dict[str, Any]], logs: list[dict[str, Any]] | None = None):
        self.content_templates = FakeCollection(templates)
        self.content_delivery_log = FakeCollection(logs or [])
        self.users = FakeCollection([{"telegram_id": 9001, "timezone": "Asia/Almaty"}])
        self.settings = FakeCollection([])


def template(
    template_id: str,
    category: str,
    source_persona: str,
    subcategory: str,
    cooldown_days: int = 30,
    weight: int = 1,
) -> dict[str, Any]:
    return {
        "template_id": template_id,
        "category": category,
        "subcategory": subcategory,
        "source_persona": source_persona,
        "tone": "romantic" if source_persona == "nurasyl" else "care",
        "text": template_id,
        "active": True,
        "cooldown_days": cooldown_days,
        "weight": weight,
    }


async def check_template_cooldown(repository: Any) -> None:
    now = repository.now_utc()
    repository.db = FakeDb(
        templates=[
            template("compliment_work_001", "compliment_work", "bot", "work", cooldown_days=1, weight=100),
            template("compliment_work_002", "compliment_work", "bot", "work", cooldown_days=30),
        ],
        logs=[
            {
                "telegram_id": 9001,
                "template_id": "compliment_work_001",
                "category": "compliment_work",
                "subcategory": "work",
                "source_persona": "bot",
                "delivered_at": now - timedelta(days=2),
            }
        ],
    )

    selected = await repository.select_content_template(
        telegram_id=9001,
        category="compliment_work",
        source_persona="bot",
        trigger="unit_check",
    )

    assert selected is not None
    assert selected["template_id"] == "compliment_work_002"


async def check_romantic_subcategory_cooldown(repository: Any) -> None:
    now = repository.now_utc()
    original_categories = repository.NURASYL_COMPLIMENT_CATEGORIES
    repository.NURASYL_COMPLIMENT_CATEGORIES = [
        "nurasyl_romantic_soft",
        "nurasyl_romantic_care",
    ]
    repository.db = FakeDb(
        templates=[
            template("nurasyl_romantic_soft_001", "nurasyl_romantic_soft", "nurasyl", "soft"),
            template("nurasyl_romantic_care_001", "nurasyl_romantic_care", "nurasyl", "care"),
        ],
        logs=[
            {
                "telegram_id": 9001,
                "template_id": "old_soft",
                "category": "nurasyl_romantic_soft",
                "subcategory": "soft",
                "source_persona": "nurasyl",
                "delivered_at": now - timedelta(days=2),
            }
        ],
    )

    try:
        selected = await repository.get_random_compliment(
            telegram_id=9001,
            source_persona="nurasyl",
            trigger="unit_check",
        )
    finally:
        repository.NURASYL_COMPLIMENT_CATEGORIES = original_categories

    assert selected is not None
    assert selected["source_persona"] == "nurasyl"
    assert selected["subcategory"] == "care"


async def check_persona_separation(repository: Any) -> None:
    repository.db = FakeDb(
        templates=[
            template("mixed_bot_001", "mixed_test", "bot", "bot_side"),
            template("mixed_nurasyl_001", "mixed_test", "nurasyl", "nurasyl_side"),
        ]
    )

    bot_selected = await repository.select_content_template(
        telegram_id=9001,
        category="mixed_test",
        source_persona="bot",
        trigger="unit_check",
    )
    nurasyl_selected = await repository.select_content_template(
        telegram_id=9001,
        category="mixed_test",
        source_persona="nurasyl",
        trigger="unit_check",
    )

    assert bot_selected is not None
    assert nurasyl_selected is not None
    assert bot_selected["source_persona"] == "bot"
    assert nurasyl_selected["source_persona"] == "nurasyl"
    assert bot_selected["template_id"] == "mixed_bot_001"
    assert nurasyl_selected["template_id"] == "mixed_nurasyl_001"


async def check_fallback_persona(repository: Any) -> None:
    repository.db = FakeDb(templates=[])
    selected = await repository.select_content_template(
        telegram_id=9001,
        category="missing_category",
        source_persona="nurasyl",
        trigger="unit_check",
    )

    assert selected is not None
    assert selected["is_fallback"] is True
    assert selected["source_persona"] == "nurasyl"


async def run_checks(repository: Any) -> None:
    original_db = repository.db
    try:
        await check_template_cooldown(repository)
        await check_romantic_subcategory_cooldown(repository)
        await check_persona_separation(repository)
        await check_fallback_persona(repository)
    finally:
        repository.db = original_db


async def main() -> None:
    await run_checks(app_repository)
    await run_checks(api_repository)
    print("content selection checks passed")


if __name__ == "__main__":
    asyncio.run(main())
