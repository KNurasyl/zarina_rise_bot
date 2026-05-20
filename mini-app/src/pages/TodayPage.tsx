import {
  BookOpen,
  Check,
  Droplet,
  Minus,
  Moon,
  Plus,
  Smile,
  Sparkles,
  Target,
  Trophy,
  Utensils,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { api, isAuthError, type ContentTemplate, type DailyAction, type TodaySummary } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import type { NavigationTarget } from "../types";

type TodayPageProps = {
  onNavigate: (target: NavigationTarget) => void;
};

type ToggleTask = {
  action: DailyAction;
  label: string;
  done: boolean;
  icon: typeof Check;
};

export const TodayPage = ({ onNavigate }: TodayPageProps) => {
  const [today, setToday] = useState<TodaySummary | null>(null);
  const [feedback, setFeedback] = useState<ContentTemplate | null>(null);
  const [quickWin, setQuickWin] = useState("");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const load = () => {
    api.today()
      .then((result) => {
        setToday(result);
        setError("");
      })
      .catch((requestError: unknown) => {
        setError(
          isAuthError(requestError)
            ? "Сессия Telegram недоступна. Открой Mini App из бота."
            : "Не удалось загрузить день.",
        );
      });
  };

  useEffect(load, []);

  const updateAction = async (action: DailyAction, done = true, value?: number) => {
    setIsSaving(true);
    try {
      const result = await api.updateToday({ action, done, value });
      setToday(result.day);
      setFeedback(result.reactive_feedback);
      setError("");
    } catch {
      setError("Не удалось сохранить действие. Попробуй ещё раз.");
    } finally {
      setIsSaving(false);
    }
  };

  const saveQuickWin = async (event: FormEvent) => {
    event.preventDefault();
    const text = quickWin.trim();
    if (!text) {
      return;
    }

    setIsSaving(true);
    try {
      await api.addJournalEntry({ type: "win", text });
      setQuickWin("");
      load();
      const compliment = await api.randomCompliment("bot");
      setFeedback(compliment.template);
    } catch {
      setError("Не удалось сохранить маленькую победу.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSupportTask = (task: ToggleTask) => {
    if (task.action === "focus") {
      onNavigate("focus");
      return;
    }
    if (task.action === "mood") {
      onNavigate("mood");
      return;
    }
    if (task.action === "journal") {
      onNavigate("journal");
      return;
    }

    void updateAction(task.action, !task.done);
  };

  const mealTasks: ToggleTask[] = [
    { action: "breakfast", label: "Завтрак", done: Boolean(today?.breakfast_done), icon: Utensils },
    { action: "lunch", label: "Обед", done: Boolean(today?.lunch_done), icon: Utensils },
    { action: "dinner", label: "Ужин", done: Boolean(today?.dinner_done), icon: Utensils },
  ];
  const supportTasks: ToggleTask[] = [
    { action: "focus", label: "Фокус", done: Boolean(today?.focus_done), icon: Target },
    { action: "mood", label: "Настроение", done: Boolean(today?.mood_done), icon: Smile },
    { action: "journal", label: "Дневник", done: Boolean(today?.journal_done), icon: BookOpen },
    { action: "small_win", label: "Победа", done: Boolean(today?.small_win_done), icon: Trophy },
    { action: "sleep", label: "Сон", done: Boolean(today?.sleep_prep_done), icon: Moon },
  ];

  const waterCount = today?.water_count ?? 0;
  const mealCount = Number(Boolean(today?.breakfast_done)) +
    Number(Boolean(today?.lunch_done)) +
    Number(Boolean(today?.dinner_done));
  const supportCompleted = today
    ? mealCount +
      Number(waterCount >= 2) +
      Number(Boolean(today.focus_done)) +
      Number(Boolean(today.mood_done)) +
      Number(Boolean(today.journal_done)) +
      Number(Boolean(today.sleep_prep_done))
    : 0;
  const progress = Math.round((supportCompleted / 8) * 100);

  return (
    <div className="page-stack">
      <header className="page-heading">
        <span className="soft-label">Сегодня</span>
        <h1>День без давления</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}

      <Card>
        <div className="card-title-row">
          <div>
            <span className="soft-label">ритм дня</span>
            <h2>{supportCompleted}/8</h2>
          </div>
          <Sparkles size={22} />
        </div>
        <div className="progress-bar">
          <span style={{ width: `${progress}%` }} />
        </div>
      </Card>

      <section className="task-section">
        <h2>Еда</h2>
        <div className="task-grid">
          {mealTasks.map((task) => {
            const Icon = task.icon;
            return (
              <button
                className={`task-card ${task.done ? "is-done" : ""}`}
                disabled={isSaving}
                key={task.action}
                onClick={() => void updateAction(task.action, !task.done)}
                type="button"
              >
                <Icon size={18} />
                <span>{task.label}</span>
                {task.done ? <Check size={18} /> : null}
              </button>
            );
          })}
        </div>
      </section>

      <Card className="water-card">
        <div>
          <span className="soft-label">вода</span>
          <h2>{waterCount} стакана</h2>
        </div>
        <div className="stepper">
          <button
            aria-label="Уменьшить воду"
            disabled={isSaving || waterCount <= 0}
            onClick={() => void updateAction("water", true, Math.max(0, waterCount - 1))}
            type="button"
          >
            <Minus size={18} />
          </button>
          <Droplet size={22} />
          <button
            aria-label="Добавить воду"
            disabled={isSaving}
            onClick={() => void updateAction("water")}
            type="button"
          >
            <Plus size={18} />
          </button>
        </div>
      </Card>

      <section className="task-section">
        <h2>Поддержка</h2>
        <div className="task-grid two">
          {supportTasks.map((task) => {
            const Icon = task.icon;
            return (
              <button
                className={`task-card ${task.done ? "is-done" : ""}`}
                disabled={isSaving}
                key={task.action}
                onClick={() => handleSupportTask(task)}
                type="button"
              >
                <Icon size={18} />
                <span>{task.label}</span>
                {task.done ? <Check size={18} /> : null}
              </button>
            );
          })}
        </div>
      </section>

      <Card>
        <form className="quick-win-form" onSubmit={saveQuickWin}>
          <label htmlFor="quick-win">Маленькая победа</label>
          <div>
            <input
              id="quick-win"
              placeholder="Например: вышла на прогулку"
              value={quickWin}
              onChange={(event) => setQuickWin(event.target.value)}
            />
            <button disabled={isSaving || !quickWin.trim()} type="submit">
              <Plus size={18} />
            </button>
          </div>
        </form>
      </Card>

      {feedback ? (
        <Card className="feedback-card">
          <p>{feedback.text}</p>
        </Card>
      ) : null}

      <div className="quick-actions">
        <button onClick={() => onNavigate("focus")} type="button">
          <Target size={18} />
          Фокус
        </button>
        <button onClick={() => onNavigate("pause")} type="button">
          <Moon size={18} />
          Пауза
        </button>
        <button onClick={() => onNavigate("mood")} type="button">
          <Smile size={18} />
          Настроение
        </button>
        <button onClick={() => onNavigate("journal")} type="button">
          <BookOpen size={18} />
          Дневник
        </button>
      </div>
    </div>
  );
};
