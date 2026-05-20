import { BookOpen, CalendarHeart, CheckCircle2, Clock3, Moon, Smile, Sparkles, Trophy } from "lucide-react";
import { useEffect, useState } from "react";

import { api, isAuthError, type Progress, type RollingProgress } from "../api/client";
import { Card } from "../components/Card";

const rhythmPercent = (summary: RollingProgress): number =>
  Math.min(100, Math.round((summary.support_actions_completed / Math.max(1, summary.tasks_possible)) * 100));

export const ProgressPage = () => {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .progress()
      .then((result) => {
        setProgress(result);
        setError("");
      })
      .catch((requestError: unknown) => {
        setError(
          isAuthError(requestError)
            ? "Сессия Telegram недоступна. Открой Mini App из бота."
            : "Не удалось загрузить прогресс.",
        );
      });
  }, []);

  const rolling7 = progress?.rolling_7_day;
  const rolling30 = progress?.rolling_30_day ?? progress?.rolling_28_day;
  const rolling40 = progress?.rolling_40_day ?? rolling30;

  return (
    <div className="page-stack">
      <header className="page-heading">
        <span className="soft-label">Прогресс</span>
        <h1>Мягкий ритм</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}

      <Card className="hero-card">
        <div className="card-title-row">
          <div>
            <span className="soft-label">последние 7 дней</span>
            <h2>{rolling7?.days_with_support ?? 0} дней с опорой</h2>
          </div>
          <CalendarHeart size={24} />
        </div>
        <div className="progress-bar">
          <span style={{ width: `${rolling7 ? rhythmPercent(rolling7) : 0}%` }} />
        </div>
        <p className="muted-copy">{rolling7?.note ?? progress?.message ?? "Ритм складывается из маленьких действий."}</p>
      </Card>

      <div className="metric-grid">
        <Card className="metric-card">
          <Clock3 size={20} />
          <strong>{progress?.focus_minutes.last_7_days ?? 0}</strong>
          <span>минут фокуса</span>
        </Card>
        <Card className="metric-card">
          <BookOpen size={20} />
          <strong>{progress?.journal_count.last_7_days ?? 0}</strong>
          <span>записей</span>
        </Card>
        <Card className="metric-card">
          <Smile size={20} />
          <strong>{progress?.mood_count?.last_7_days ?? 0}</strong>
          <span>чек-инов настроения</span>
        </Card>
        <Card className="metric-card">
          <Trophy size={20} />
          <strong>{progress?.small_wins.last_7_days ?? 0}</strong>
          <span>маленьких побед</span>
        </Card>
        <Card className="metric-card">
          <Moon size={20} />
          <strong>{rolling7?.sleep_prep_days ?? 0}</strong>
          <span>вечеров с заботой</span>
        </Card>
      </div>

      <Card>
        <div className="card-title-row">
          <div>
            <span className="soft-label">30/40 дней</span>
            <h2>{rolling30?.support_actions_completed ?? 0} поддерживающих действий</h2>
          </div>
          <Sparkles size={22} />
        </div>
        <div className="soft-bars">
          <div>
            <span>Фокус</span>
            <strong>{progress?.focus_minutes.last_30_days ?? progress?.focus_minutes.last_28_days ?? 0} мин</strong>
          </div>
          <div>
            <span>Дневник</span>
            <strong>{progress?.journal_count.last_30_days ?? progress?.journal_count.last_28_days ?? 0}</strong>
          </div>
          <div>
            <span>Настроение</span>
            <strong>{progress?.mood_count?.last_30_days ?? progress?.mood_count?.last_28_days ?? 0}</strong>
          </div>
          <div>
            <span>Победы</span>
            <strong>{progress?.small_wins.last_30_days ?? progress?.small_wins.last_28_days ?? 0}</strong>
          </div>
          <div>
            <span>40 дней</span>
            <strong>{rolling40?.days_with_support ?? 0} дней с опорой</strong>
          </div>
        </div>
        <p className="muted-copy">
          {progress?.soft_30_40_day_progress?.note ?? "Это мягкая картина ритма, без требований к непрерывности."}
        </p>
      </Card>

      <Card className="feedback-card">
        <CheckCircle2 size={22} />
        <p>{progress?.message ?? "Прогресс показывает, где уже есть жизнь, внимание и опора."}</p>
      </Card>
    </div>
  );
};
