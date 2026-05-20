import {
  ArrowLeft,
  BatteryMedium,
  Cloud,
  CloudRain,
  Flame,
  Leaf,
  LoaderCircle,
  Moon,
  Save,
  Sparkles,
  Waves,
} from "lucide-react";
import { useState } from "react";

import { api, type MoodState } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import type { NavigationTarget } from "../types";

type MoodFlowProps = {
  onBack: () => void;
  onNavigate: (target: NavigationTarget) => void;
};

const heavyMoods: MoodState[] = ["anxious", "overloaded", "no_energy"];
const resourceMoods: MoodState[] = ["calm", "productive"];

const moodOptions: Array<{
  value: MoodState;
  label: string;
  hint: string;
  icon: typeof Leaf;
}> = [
  { value: "calm", label: "Спокойно", hint: "ровно внутри", icon: Leaf },
  { value: "normal", label: "Нормально", hint: "обычный день", icon: Waves },
  { value: "tired", label: "Устала", hint: "нужен бережный темп", icon: Moon },
  { value: "anxious", label: "Тревожно", hint: "можно замедлиться", icon: Cloud },
  { value: "sad", label: "Грустно", hint: "без лишних требований", icon: CloudRain },
  { value: "overloaded", label: "Перегруз", hint: "оставить только главное", icon: LoaderCircle },
  { value: "no_energy", label: "Нет сил", hint: "минимальный шаг", icon: BatteryMedium },
  { value: "productive", label: "Продуктивно", hint: "собранный фокус", icon: Flame },
];

const getMoodFeedback = (mood: MoodState): string => {
  if (heavyMoods.includes(mood)) {
    return "Отметила. Без оценки: просто заметили состояние. Если сегодня тяжело, можно выбрать режим тише.";
  }

  if (resourceMoods.includes(mood)) {
    return "Отметила. Без оценки: просто заметили состояние. Можно мягко направить это в фокус или план дня.";
  }

  return "Отметила. Без оценки: просто заметили состояние.";
};

export const MoodFlow = ({ onBack, onNavigate }: MoodFlowProps) => {
  const [selectedMood, setSelectedMood] = useState<MoodState>("normal");
  const [savedMood, setSavedMood] = useState<MoodState | null>(null);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const save = async () => {
    setIsSaving(true);
    try {
      await api.mood({
        mood: selectedMood,
        energy: null,
        note: note.trim() || null,
      });
      setSavedMood(selectedMood);
      setMessage(getMoodFeedback(selectedMood));
      setError("");
    } catch {
      setError("Не удалось сохранить настроение. Попробуй ещё раз чуть позже.");
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
        <span className="soft-label">Настроение</span>
        <h1>Короткий чек-ин</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}
      {message ? <div className="success-alert">{message}</div> : null}

      <Card>
        <div className="mood-grid">
          {moodOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = selectedMood === option.value;

            return (
              <button
                className={`mood-option ${isSelected ? "is-selected" : ""}`}
                key={option.value}
                onClick={() => {
                  setSelectedMood(option.value);
                  setSavedMood(null);
                  setMessage("");
                }}
                type="button"
              >
                <Icon size={18} />
                <span>{option.label}</span>
                <small>{option.hint}</small>
              </button>
            );
          })}
        </div>
      </Card>

      <Card>
        <label className="input-label">
          Заметка по желанию
          <textarea
            className="mood-note"
            maxLength={1000}
            placeholder="Можно оставить одну строку или оставить поле пустым."
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
      </Card>

      <Button disabled={isSaving} onClick={() => void save()}>
        <Save size={18} />
        Сохранить
      </Button>

      {message ? (
        <div className="mood-followup-actions">
          {savedMood && heavyMoods.includes(savedMood) ? (
            <>
              <Button variant="soft" onClick={() => onNavigate("pause")}>
                Режим тише
              </Button>
              <Button variant="secondary" onClick={() => onNavigate("today")}>
                Один маленький шаг
              </Button>
            </>
          ) : null}

          {savedMood && resourceMoods.includes(savedMood) ? (
            <>
              <Button variant="secondary" onClick={() => onNavigate("focus")}>
                Фокус
              </Button>
              <Button variant="soft" onClick={() => onNavigate("today")}>
                Сегодня
              </Button>
            </>
          ) : null}
        </div>
      ) : null}

      <Button variant="soft" onClick={onBack}>
        <Sparkles size={18} />
        Вернуться
      </Button>
    </div>
  );
};
