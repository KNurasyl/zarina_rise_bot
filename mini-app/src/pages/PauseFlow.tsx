import { ArrowLeft, BellOff, Check, Clock3, Moon, SunMedium } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { formatTime } from "../lib/format";

type PauseFlowProps = {
  onBack: () => void;
};

const categories = [
  { key: "meal", label: "еда" },
  { key: "water", label: "вода" },
  { key: "focus", label: "фокус" },
  { key: "sleep", label: "сон" },
  { key: "compliments", label: "комплименты" },
];

export const PauseFlow = ({ onBack }: PauseFlowProps) => {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [pauseUntil, setPauseUntil] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const toggleCategory = (category: string) => {
    setSelectedCategories((current) =>
      current.includes(category)
        ? current.filter((item) => item !== category)
        : [...current, category],
    );
  };

  const savePause = async (mode: "1h" | "until_evening" | "today") => {
    setIsSaving(true);
    try {
      const result = await api.pause({ mode, categories: selectedCategories });
      setPauseUntil(result.pause_until);
      setMessage("Напоминания поставлены на мягкую паузу.");
      setError("");
    } catch {
      setError("Не удалось поставить паузу. Попробуй ещё раз.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-stack flow-page">
      <button className="back-button" onClick={onBack} type="button">
        <ArrowLeft size={18} />
        Назад
      </button>

      <header className="page-heading">
        <span className="soft-label">Пауза</span>
        <h1>Пауза без чувства долга</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}

      <div className="pause-options">
        <button disabled={isSaving} onClick={() => void savePause("1h")} type="button">
          <Clock3 size={20} />
          <span>На 1 час</span>
        </button>
        <button disabled={isSaving} onClick={() => void savePause("until_evening")} type="button">
          <SunMedium size={20} />
          <span>До вечера</span>
        </button>
        <button disabled={isSaving} onClick={() => void savePause("today")} type="button">
          <Moon size={20} />
          <span>Сегодня</span>
        </button>
      </div>

      <Card>
        <span className="soft-label">категории</span>
        <div className="chip-row">
          {categories.map((category) => (
            <button
              className={`chip ${selectedCategories.includes(category.key) ? "is-selected" : ""}`}
              key={category.key}
              onClick={() => toggleCategory(category.key)}
              type="button"
            >
              {category.label}
            </button>
          ))}
        </div>
      </Card>

      <Card className="pause-status">
        <BellOff size={26} />
        <h2>{message || "Можно сделать день тише"}</h2>
        <p>
          {pauseUntil
            ? `Пауза до ${formatTime(pauseUntil)}`
            : "Выбери длительность. Это не отменяет прогресс и ничего не ломает."}
        </p>
      </Card>

      {pauseUntil ? (
        <Button variant="secondary" onClick={onBack}>
          <Check size={18} />
          Готово
        </Button>
      ) : null}
    </div>
  );
};
