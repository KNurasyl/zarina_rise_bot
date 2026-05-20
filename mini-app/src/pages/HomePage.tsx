import {
  BookOpen,
  BriefcaseBusiness,
  Droplets,
  Moon,
  Pause,
  PenLine,
  Sparkles,
  Smile,
  Soup,
  Timer,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api, isAuthError, type ContentTemplate, type Dashboard, type MoodState } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { getGreeting } from "../lib/format";
import type { NavigationTarget } from "../types";

type HomePageProps = {
  onNavigate: (target: NavigationTarget) => void;
};

const moodLabels: Record<MoodState, string> = {
  calm: "Спокойно",
  normal: "Нормально",
  tired: "Устала",
  anxious: "Тревожно",
  sad: "Грустно",
  overloaded: "Перегруз",
  no_energy: "Нет сил",
  productive: "Продуктивно",
};

const getMainTarget = (action?: string): NavigationTarget => {
  if (action === "focus") {
    return "focus";
  }
  if (action === "mood") {
    return "mood";
  }
  if (action === "journal" || action === "small_win") {
    return "journal";
  }
  if (action === "rest") {
    return "pause";
  }
  return "today";
};

export const HomePage = ({ onNavigate }: HomePageProps) => {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [note, setNote] = useState<ContentTemplate | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = () => {
    setIsLoading(true);
    Promise.all([api.dashboard(), api.randomCompliment("nurasyl")])
      .then(([dashboardResult, complimentResult]) => {
        setDashboard(dashboardResult);
        setNote(complimentResult.template ?? dashboardResult.message_of_day ?? dashboardResult.random_gentle_message);
        setError("");
      })
      .catch((requestError: unknown) => {
        setError(
          isAuthError(requestError)
            ? "Сессия Telegram недоступна. Открой Mini App из бота."
            : "Не удалось обновить главную. Попробуй ещё раз чуть позже.",
        );
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(load, []);

  const summary = dashboard?.today_summary;
  const mealCount = Number(Boolean(summary?.breakfast_done)) +
    Number(Boolean(summary?.lunch_done)) +
    Number(Boolean(summary?.dinner_done));
  const supportCompleted = summary
    ? mealCount +
      Number((summary.water_count ?? 0) >= 2) +
      Number(Boolean(summary.focus_done)) +
      Number(Boolean(summary.mood_done)) +
      Number(Boolean(summary.journal_done)) +
      Number(Boolean(summary.sleep_prep_done))
    : 0;
  const supportItems = useMemo(
    () => [
      { label: "еда", done: mealCount === 3, icon: Soup },
      { label: "вода", done: (summary?.water_count ?? 0) >= 2, icon: Droplets },
      { label: "фокус", done: Boolean(summary?.focus_done), icon: BriefcaseBusiness },
      { label: "настроение", done: Boolean(summary?.mood_done), icon: Smile },
      { label: "дневник", done: Boolean(summary?.journal_done), icon: BookOpen },
      { label: "сон", done: Boolean(summary?.sleep_prep_done), icon: Moon },
    ],
    [mealCount, summary],
  );

  const nextAction = dashboard?.next_best_action;
  const mainTarget = getMainTarget(nextAction?.action);
  const latestMood = dashboard?.latest_mood;

  return (
    <div className="page-stack home-page">
      <header className="home-greeting">
        <span>Сегодня</span>
        <h1>{getGreeting()}</h1>
        <p>Один спокойный шаг на сейчас.</p>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}
      {isLoading ? <Card className="skeleton-card">Загружаю мягкий ритм дня...</Card> : null}

      <button className="home-mood-chip" onClick={() => onNavigate("mood")} type="button">
        <Smile size={18} />
        <span>Настроение</span>
        <strong>{latestMood ? moodLabels[latestMood.mood] : "Отметить"}</strong>
      </button>

      <Card className="next-card">
        <span className="soft-label">Сегодняшний шаг</span>
        <h2>{nextAction?.title ?? "Позавтракать"}</h2>
        <p>{nextAction?.message ?? "Один небольшой шаг будет достаточен."}</p>
        <Button onClick={() => onNavigate(mainTarget)}>
          {mainTarget === "focus" ? <Timer size={18} /> : <Sparkles size={18} />}
          Продолжить
        </Button>
      </Card>

      <Card className="support-card zr-card-strong">
        <div className="card-title-row">
          <div>
            <span className="soft-label">Поддержка дня</span>
            <h2>{supportCompleted}/8</h2>
          </div>
          <button className="text-button" onClick={() => onNavigate("today")} type="button">
            Сегодня
          </button>
        </div>
        <div className="support-grid">
          {supportItems.map((item) => {
            const Icon = item.icon;
            return (
              <span className={`support-chip ${item.done ? "is-done" : ""}`} key={item.label}>
                <Icon size={16} />
                {item.label}
              </span>
            );
          })}
        </div>
      </Card>

      <Card className="nurasyl-card">
        <span className="soft-label">{note?.source_persona === "nurasyl" ? "От Нурасыла" : "Вдохновение"}</span>
        <p>{note?.text ?? dashboard?.message_of_day?.text ?? "Ты можешь идти спокойно. Достаточно одного бережного шага."}</p>
      </Card>

      <div className="quick-actions">
        <button onClick={() => onNavigate("focus")} type="button">
          <Timer size={18} />
          Фокус
        </button>
        <button onClick={() => onNavigate("pause")} type="button">
          <Pause size={18} />
          Пауза
        </button>
        <button onClick={() => onNavigate("mood")} type="button">
          <Smile size={18} />
          Настроение
        </button>
        <button onClick={() => onNavigate("journal")} type="button">
          <PenLine size={18} />
          Дневник
        </button>
      </div>
    </div>
  );
};
