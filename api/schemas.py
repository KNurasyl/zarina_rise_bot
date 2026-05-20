from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, StrictBool, StrictInt, field_validator, model_validator

DailyAction = Literal[
    "breakfast",
    "lunch",
    "dinner",
    "water",
    "focus",
    "journal",
    "mood",
    "sleep",
    "small_win",
]
TodayTaskKey = Literal[
    "breakfast_done",
    "lunch_done",
    "dinner_done",
    "water_count",
    "focus_done",
    "journal_done",
    "mood_done",
    "small_win_done",
    "sleep_prep_done",
]
JournalEntryType = Literal["note", "win", "gratitude", "idea", "focus", "evening"]
Mood = Literal[
    "calm",
    "normal",
    "tired",
    "anxious",
    "sad",
    "overloaded",
    "no_energy",
    "productive",
]
FocusStatus = Literal["started", "completed", "partial", "cancelled"]
NotificationStatus = Literal["sent", "skipped", "failed"]
ComplimentFrequency = Literal["low", "normal", "high"]
SourcePersona = Literal["bot", "nurasyl"]
TemplateTone = Literal["calm", "romantic", "focus", "care", "sleep", "progress"]
PauseMode = Literal["1h", "until_evening", "today"]
PAUSE_CATEGORIES = {
    "all",
    "morning",
    "meal",
    "breakfast",
    "lunch",
    "dinner",
    "water",
    "focus",
    "mood",
    "sleep",
    "compliments",
    "random_compliment",
    "romantic_from_nurasyl",
}


class TodayPatch(BaseModel):
    key: TodayTaskKey | None = None
    value: StrictBool | StrictInt | None = None

    # Backward-compatible Mini App fields. New clients should send key/value.
    action: DailyAction | None = None
    done: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self) -> "TodayPatch":
        if self.key is None and self.action is None:
            raise ValueError("Either key or action is required")
        if self.key is not None and self.value is None:
            raise ValueError("value is required when key is provided")
        return self


class JournalEntryCreate(BaseModel):
    type: JournalEntryType = "note"
    text: str = Field(min_length=1, max_length=3000)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        cleaned = []
        for tag in tags:
            value = tag.strip()
            if not value:
                continue
            if len(value) > 40:
                raise ValueError("Journal tag is too long")
            cleaned.append(value)
        return cleaned[:20]


class MoodCheckinCreate(BaseModel):
    mood: Mood
    energy: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)


class FocusStart(BaseModel):
    planned_minutes: Literal[15, 25, 45] = 25
    label: str | None = Field(default=None, max_length=200)


class FocusComplete(BaseModel):
    completed_minutes: int = Field(ge=0, le=180)
    status: Literal["completed", "partial"] = "completed"


class PauseCreate(BaseModel):
    mode: PauseMode = "1h"
    categories: list[str] = Field(default_factory=list, max_length=20)

    # Backward-compatible fields used by the current Mini App.
    pause_until: datetime | None = None
    minutes: int | None = Field(default=None, ge=1, le=1440)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, categories: list[str]) -> list[str]:
        cleaned = []
        for category in categories:
            value = category.strip()
            if not value:
                continue
            if value not in PAUSE_CATEGORIES:
                raise ValueError("Unknown pause category")
            if len(value) > 60:
                raise ValueError("Pause category is too long")
            cleaned.append(value)
        return cleaned[:20]


class ContentTemplateCreate(BaseModel):
    template_id: str = Field(min_length=3, max_length=160)
    category: str = Field(min_length=1, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    source_persona: SourcePersona = "bot"
    tone: TemplateTone = "care"
    text: str = Field(min_length=1, max_length=500)
    active: bool = True
    cooldown_days: int = Field(default=30, ge=0, le=365)
    weight: int = Field(default=1, ge=1, le=100)


class ContentTemplateUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    source_persona: SourcePersona | None = None
    tone: TemplateTone | None = None
    text: str | None = Field(default=None, min_length=1, max_length=500)
    active: bool | None = None
    cooldown_days: int | None = Field(default=None, ge=0, le=365)
    weight: int | None = Field(default=None, ge=1, le=100)


class SeedContentRequest(BaseModel):
    overwrite_existing: bool = False
    minutes: int | None = Field(default=60, ge=5, le=1440)
    categories: list[str] = Field(default_factory=list, max_length=20)


class ComplimentRandomRequest(BaseModel):
    source_persona: SourcePersona | None = None


class SettingsPatch(BaseModel):
    reminders_enabled: bool | None = None
    morning_enabled: bool | None = None
    meal_enabled: bool | None = None
    water_enabled: bool | None = None
    focus_enabled: bool | None = None
    sleep_enabled: bool | None = None
    mood_enabled: bool | None = None
    random_compliments_enabled: bool | None = None
    romantic_from_nurasyl_enabled: bool | None = None
    compliment_frequency: ComplimentFrequency | None = None
    max_messages_per_day: int | None = Field(default=None, ge=1, le=20)
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    preferred_wake_time: str | None = None
    preferred_sleep_time: str | None = None
    breakfast_time: str | None = None
    lunch_time: str | None = None
    dinner_time: str | None = None
    focus_time: str | None = None
    pause_until: datetime | None = None
