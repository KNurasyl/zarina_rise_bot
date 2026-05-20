import { ArrowLeft, Check, Pause, Play, X } from "lucide-react";
import { useState } from "react";

import { api, type ContentTemplate, type FocusSession } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

type FocusFlowProps = {
  onBack: () => void;
};

const durations: Array<15 | 25 | 45> = [15, 25, 45];

export const FocusFlow = ({ onBack }: FocusFlowProps) => {
  const [plannedMinutes, setPlannedMinutes] = useState<15 | 25 | 45>(25);
  const [label, setLabel] = useState("");
  const [session, setSession] = useState<FocusSession | null>(null);
  const [completedMinutes, setCompletedMinutes] = useState(25);
  const [feedback, setFeedback] = useState<ContentTemplate | null>(null);
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  const start = async () => {
    setIsBusy(true);
    try {
      const result = await api.startFocus(plannedMinutes, label.trim() || undefined);
      setSession(result.session);
      setCompletedMinutes(plannedMinutes);
      setFeedback(null);
      setError("");
    } catch {
      setError("Не удалось начать фокус. Попробуй ещё раз.");
    } finally {
      setIsBusy(false);
    }
  };

  const finish = async (status: "completed" | "partial") => {
    if (!session) {
      return;
    }

    setIsBusy(true);
    try {
      const result = await api.completeFocus(session.session_id, completedMinutes, status);
      setSession(result.session);
      setFeedback(result.feedback);
      setError("");
    } catch {
      setError("Не удалось завершить фокус.");
    } finally {
      setIsBusy(false);
    }
  };

  const cancel = async () => {
    if (!session) {
      onBack();
      return;
    }

    setIsBusy(true);
    try {
      const result = await api.cancelFocus(session.session_id);
      setSession(result.session);
      setError("");
    } catch {
      setError("Не удалось отменить сессию.");
    } finally {
      setIsBusy(false);
    }
  };

  const isActive = session?.status === "started";

  return (
    <div className="page-stack flow-page">
      <button className="back-button" onClick={onBack} type="button">
        <ArrowLeft size={18} />
        Назад
      </button>

      <header className="page-heading">
        <span className="soft-label">Фокус</span>
        <h1>Спокойный блок внимания</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}

      <Card>
        <span className="soft-label">длительность</span>
        <div className="segmented">
          {durations.map((duration) => (
            <button
              className={plannedMinutes === duration ? "is-selected" : ""}
              disabled={isActive}
              key={duration}
              onClick={() => setPlannedMinutes(duration)}
              type="button"
            >
              {duration} мин
            </button>
          ))}
        </div>
        <label className="input-label">
          Название
          <input
            disabled={isActive}
            placeholder="Например: письма, задача, учёба"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
          />
        </label>
        {!isActive ? (
          <Button disabled={isBusy} onClick={() => void start()}>
            <Play size={18} />
            Начать
          </Button>
        ) : null}
      </Card>

      {session ? (
        <Card className="focus-session-card">
          <span className="soft-label">сессия</span>
          <h2>{session.status === "started" ? "Фокус идёт" : "Фокус сохранён"}</h2>
          <p>{session.label || "Без названия"} · {session.planned_minutes} мин</p>
          {isActive ? (
            <>
              <label className="input-label">
                Сколько получилось
                <input
                  min={0}
                  max={session.planned_minutes}
                  type="number"
                  value={completedMinutes}
                  onChange={(event) => setCompletedMinutes(Number(event.target.value))}
                />
              </label>
              <div className="button-grid">
                <Button disabled={isBusy} onClick={() => void finish("completed")}>
                  <Check size={18} />
                  Готово
                </Button>
                <Button variant="secondary" disabled={isBusy} onClick={() => void finish("partial")}>
                  <Pause size={18} />
                  Частично
                </Button>
                <Button variant="ghost" disabled={isBusy} onClick={() => void cancel()}>
                  <X size={18} />
                  Отменить
                </Button>
              </div>
            </>
          ) : null}
        </Card>
      ) : null}

      {feedback ? (
        <Card className="feedback-card">
          <p>{feedback.text}</p>
        </Card>
      ) : null}
    </div>
  );
};
