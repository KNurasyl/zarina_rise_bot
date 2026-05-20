import { BookOpen, PenLine, Save } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { api, isAuthError, type JournalEntry, type JournalEntryType } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { formatDate } from "../lib/format";
import { setDraftProtection } from "../telegram";

const DRAFT_KEY = "zarina-rise-journal-draft-v1";

const entryTypes: Array<{ type: JournalEntryType; label: string }> = [
  { type: "note", label: "мысль" },
  { type: "win", label: "победа" },
  { type: "gratitude", label: "благодарность" },
  { type: "idea", label: "идея" },
  { type: "focus", label: "фокус" },
  { type: "evening", label: "вечер" },
];

const typeLabels: Record<JournalEntryType, string> = {
  note: "Мысль",
  win: "Победа",
  gratitude: "Благодарность",
  idea: "Идея",
  focus: "Фокус",
  evening: "Вечер",
};

export const JournalPage = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [type, setType] = useState<JournalEntryType>("note");
  const [text, setText] = useState(() => localStorage.getItem(DRAFT_KEY) ?? "");
  const [filter, setFilter] = useState<JournalEntryType | "all">("all");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const loadEntries = () => {
    api
      .journal({ type: filter === "all" ? undefined : filter, limit: 30 })
      .then((result) => {
        setEntries(result.items);
        setError("");
      })
      .catch((requestError: unknown) => {
        setError(
          isAuthError(requestError)
            ? "Сессия Telegram недоступна. Открой Mini App из бота."
            : "Не удалось загрузить дневник.",
        );
      });
  };

  useEffect(loadEntries, [filter]);

  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, text);
    setDraftProtection(Boolean(text.trim()));
    return () => setDraftProtection(false);
  }, [text]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const value = text.trim();
    if (!value) {
      return;
    }

    setIsSaving(true);
    try {
      await api.addJournalEntry({ type, text: value });
      setText("");
      localStorage.removeItem(DRAFT_KEY);
      loadEntries();
    } catch {
      setError("Не удалось сохранить запись. Черновик остался на месте.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-stack">
      <header className="page-heading">
        <span className="soft-label">Дневник</span>
        <h1>Тихое место для мыслей</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}

      <Card>
        <form className="journal-form" onSubmit={submit}>
          <label>
            Тип записи
            <select value={type} onChange={(event) => setType(event.target.value as JournalEntryType)}>
              {entryTypes.map((entryType) => (
                <option key={entryType.type} value={entryType.type}>
                  {entryType.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Текст
            <textarea
              placeholder="Что важно сохранить из этого момента?"
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <div className="form-footer">
            <span>{text.trim() ? "Черновик сохранён" : "Можно написать одну строку"}</span>
            <Button disabled={isSaving || !text.trim()} type="submit">
              <Save size={18} />
              Сохранить
            </Button>
          </div>
        </form>
      </Card>

      <div className="chip-row horizontal-scroll">
        <button className={`chip ${filter === "all" ? "is-selected" : ""}`} onClick={() => setFilter("all")} type="button">
          все
        </button>
        {entryTypes.map((entryType) => (
          <button
            className={`chip ${filter === entryType.type ? "is-selected" : ""}`}
            key={entryType.type}
            onClick={() => setFilter(entryType.type)}
            type="button"
          >
            {entryType.label}
          </button>
        ))}
      </div>

      <div className="entry-list">
        {entries.length ? (
          entries.map((entry) => (
            <Card className="entry-card" key={entry.entry_id}>
              <div className="entry-meta">
                <span>{typeLabels[entry.type]}</span>
                <time>{formatDate(entry.created_at)}</time>
              </div>
              <p>{entry.text}</p>
            </Card>
          ))
        ) : (
          <Card className="empty-state">
            <BookOpen size={28} />
            <h2>Пока здесь тихо</h2>
            <p>Первая запись может быть совсем короткой: мысль, благодарность или маленькая победа.</p>
            <Button variant="soft" onClick={() => setType("note")}>
              <PenLine size={18} />
              Начать запись
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
};
