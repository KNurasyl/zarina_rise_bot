import type { ReactNode } from "react";
import { Settings } from "lucide-react";

import type { Tab } from "../types";
import { BottomNav } from "./BottomNav";

type AppShellProps = {
  tab: Tab;
  onTabChange: (tab: Tab) => void;
  onOpenSettings: () => void;
  showNav?: boolean;
  children: ReactNode;
};

export const AppShell = ({
  tab,
  onTabChange,
  onOpenSettings,
  showNav = true,
  children,
}: AppShellProps) => (
  <div className={`app-shell ${showNav ? "has-bottom-nav" : ""}`}>
    <header className="app-topbar">
      <div>
        <span>Zarina Rise</span>
        <strong>Мягкий ритм дня</strong>
      </div>
      <button
        aria-label="Открыть настройки"
        className="icon-button"
        onClick={onOpenSettings}
        type="button"
      >
        <Settings size={20} />
      </button>
    </header>
    <main className="app-main app-content">{children}</main>
    {showNav ? <BottomNav tab={tab} onChange={onTabChange} /> : null}
  </div>
);
