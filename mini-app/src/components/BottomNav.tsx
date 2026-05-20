import { BookOpen, CalendarDays, Home, Sprout } from "lucide-react";

import type { Tab } from "../types";

type BottomNavProps = {
  tab: Tab;
  onChange: (tab: Tab) => void;
};

const items: Array<{ tab: Tab; label: string; icon: typeof Home }> = [
  { tab: "home", label: "Home", icon: Home },
  { tab: "today", label: "Сегодня", icon: CalendarDays },
  { tab: "journal", label: "Дневник", icon: BookOpen },
  { tab: "progress", label: "Прогресс", icon: Sprout },
];

export const BottomNav = ({ tab, onChange }: BottomNavProps) => (
  <nav className="bottom-nav" aria-label="Основная навигация">
    {items.map((item) => {
      const Icon = item.icon;
      const isActive = tab === item.tab;

      return (
        <button
          className={`bottom-nav__item ${isActive ? "is-active" : ""}`}
          key={item.tab}
          onClick={() => onChange(item.tab)}
          type="button"
        >
          <span className="bottom-nav__icon">
            <Icon size={20} strokeWidth={2} />
          </span>
          <span>{item.label}</span>
        </button>
      );
    })}
  </nav>
);
