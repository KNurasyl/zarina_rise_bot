import { ArrowLeft, Download, Power, ShieldCheck, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { api, type ComplimentFrequency, type Settings } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { formatTime } from "../lib/format";

type SettingsFlowProps = {
  onBack: () => void;
};

const toggleItems: Array<{ key: keyof Settings; label: string }> = [
  { key: "reminders_enabled", label: "Напоминания" },
  { key: "morning_enabled", label: "Утро" },
  { key: "meal_enabled", label: "Еда" },
  { key: "water_enabled", label: "Вода" },
  { key: "focus_enabled", label: "Фокус" },
  { key: "sleep_enabled", label: "Сон" },
  { key: "random_compliments_enabled", label: "Случайные комплименты" },
  { key: "romantic_from_nurasyl_enabled", label: "Романтичные сообщения от Нурасыла" },
  { key: "mood_enabled", label: "Настроение" },
];

const timeItems: Array<{ key: keyof Settings; label: string }> = [
  { key: "quiet_hours_start", label: "Тихие часы с" },
  { key: "quiet_hours_end", label: "Тихие часы до" },
  { key: "breakfast_time", label: "Завтрак" },
  { key: "lunch_time", label: "Обед" },
  { key: "dinner_time", label: "Ужин" },
  { key: "focus_time", label: "Фокус" },
  { key: "preferred_sleep_time", label: "Сон" },
];

export const SettingsFlow = ({ onBack }: SettingsFlowProps) => {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    api
      .settings()
      .then(setSettings)
      .catch(() => setError("Не удалось загрузить настройки."));
  }, []);

  const patch = async (payload: Partial<Settings>) => {
    setIsBusy(true);
    try {
      const updated = await api.updateSettings(payload);
      setSettings(updated);
      setMessage("Настройки сохранены.");
      setError("");
    } catch {
      setError("Не удалось сохранить настройки.");
    } finally {
      setIsBusy(false);
    }
  };

  const exportData = async () => {
    setIsBusy(true);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "zarina-rise-export.json";
      link.click();
      URL.revokeObjectURL(url);
      setMessage("Экспорт подготовлен.");
    } catch {
      setError("Не удалось подготовить экспорт.");
    } finally {
      setIsBusy(false);
    }
  };

  const deleteAccount = async () => {
    if (!window.confirm("Удалить личные данные Zarina Rise?")) {
      return;
    }

    setIsBusy(true);
    try {
      await api.deleteMe();
      setMessage("Данные удалены.");
      setSettings(null);
    } catch {
      setError("Не удалось удалить данные.");
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className="page-stack flow-page">
      <button className="back-button" onClick={onBack} type="button">
        <ArrowLeft size={18} />
        Назад
      </button>

      <header className="page-heading">
        <span className="soft-label">Настройки</span>
        <h1>Настройки ритма</h1>
      </header>

      {error ? <div className="soft-alert">{error}</div> : null}
      {message ? <div className="success-alert">{message}</div> : null}

      <Card>
        <div className="setting-list">
          {toggleItems.map((item) => (
            <label
              className={`toggle-row ${Boolean(settings?.[item.key]) ? "is-active" : ""}`}
              key={item.key}
            >
              <span>{item.label}</span>
              <input
                checked={Boolean(settings?.[item.key])}
                disabled={!settings || isBusy}
                type="checkbox"
                onChange={(event) => void patch({ [item.key]: event.target.checked } as Partial<Settings>)}
              />
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <span className="soft-label">время</span>
        <div className="time-grid">
          {timeItems.map((item) => (
            <label className="input-label" key={item.key}>
              {item.label}
              <input
                disabled={!settings || isBusy}
                type="time"
                value={String(settings?.[item.key] ?? "")}
                onChange={(event) => void patch({ [item.key]: event.target.value } as Partial<Settings>)}
              />
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <label className="input-label">
          Частота комплиментов
          <select
            disabled={!settings || isBusy}
            value={settings?.compliment_frequency ?? "normal"}
            onChange={(event) =>
              void patch({ compliment_frequency: event.target.value as ComplimentFrequency })
            }
          >
            <option value="low">низкая</option>
            <option value="normal">обычная</option>
            <option value="high">частая</option>
          </select>
        </label>
      </Card>

      <Card>
        <label className="input-label">
          Максимум сообщений в день
          <input
            disabled={!settings || isBusy}
            min={1}
            max={20}
            type="number"
            value={settings?.max_messages_per_day ?? 8}
            onChange={(event) =>
              void patch({ max_messages_per_day: Number(event.target.value) } as Partial<Settings>)
            }
          />
        </label>
        <p className="muted-copy">Больше сообщений возможно только если они включены в настройках и подходят по времени.</p>
      </Card>

      <Card>
        <div className="card-title-row">
          <div>
            <span className="soft-label">пауза</span>
            <h2>{settings?.pause_until ? `До ${formatTime(settings.pause_until)}` : "Не включена"}</h2>
          </div>
        </div>
        <p className="muted-copy">
          Пауза временно делает напоминания тише. Её можно поставить в Pause flow или снять здесь.
        </p>
        <Button
          variant="secondary"
          disabled={!settings?.pause_until || isBusy}
          onClick={() => void patch({ pause_until: null })}
        >
          Снять паузу
        </Button>
      </Card>

      <Card className="privacy-card">
        <ShieldCheck size={24} />
        <div>
          <h2>Приватность</h2>
          <p>Дневник не уходит в аналитику. Экспорт и удаление доступны в любой момент.</p>
        </div>
        <div className="button-grid">
          <Button variant="secondary" disabled={isBusy} onClick={() => void exportData()}>
            <Download size={18} />
            Экспорт
          </Button>
          <Button variant="ghost" disabled={isBusy} onClick={() => void deleteAccount()}>
            <Trash2 size={18} />
            Удалить
          </Button>
        </div>
      </Card>

      <Button variant="soft" onClick={onBack}>
        <Power size={18} />
        Закрыть настройки
      </Button>
    </div>
  );
};
