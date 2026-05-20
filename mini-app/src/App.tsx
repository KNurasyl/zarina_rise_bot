import { useEffect, useState } from "react";

import { AppShell } from "./components/AppShell";
import { FocusFlow } from "./pages/FocusFlow";
import { HomePage } from "./pages/HomePage";
import { JournalPage } from "./pages/JournalPage";
import { MoodFlow } from "./pages/MoodFlow";
import { OnboardingFlow } from "./pages/OnboardingFlow";
import { OutsideTelegramPage } from "./pages/OutsideTelegramPage";
import { PauseFlow } from "./pages/PauseFlow";
import { ProgressPage } from "./pages/ProgressPage";
import { SettingsFlow } from "./pages/SettingsFlow";
import { TodayPage } from "./pages/TodayPage";
import { isTelegramMiniApp } from "./telegram";
import type { Flow, NavigationTarget, Tab } from "./types";

const ONBOARDING_KEY = "zarina-rise-onboarding-v1";

export const App = () => {
  const [tab, setTab] = useState<Tab>("home");
  const [flow, setFlow] = useState<Flow | null>(null);

  useEffect(() => {
    if (isTelegramMiniApp() && localStorage.getItem(ONBOARDING_KEY) !== "done") {
      setFlow("onboarding");
    }
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [flow, tab]);

  if (!isTelegramMiniApp()) {
    return <OutsideTelegramPage />;
  }

  const navigate = (target: NavigationTarget) => {
    if (
      target === "focus" ||
      target === "pause" ||
      target === "mood" ||
      target === "settings" ||
      target === "onboarding"
    ) {
      setFlow(target);
      return;
    }

    setFlow(null);
    setTab(target);
  };

  const closeFlow = () => setFlow(null);

  const finishOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, "done");
    setFlow(null);
  };

  const content = (() => {
    if (flow === "onboarding") {
      return <OnboardingFlow onDone={finishOnboarding} />;
    }
    if (flow === "focus") {
      return <FocusFlow onBack={closeFlow} />;
    }
    if (flow === "pause") {
      return <PauseFlow onBack={closeFlow} />;
    }
    if (flow === "mood") {
      return <MoodFlow onBack={closeFlow} onNavigate={navigate} />;
    }
    if (flow === "settings") {
      return <SettingsFlow onBack={closeFlow} />;
    }
    if (tab === "today") {
      return <TodayPage onNavigate={navigate} />;
    }
    if (tab === "journal") {
      return <JournalPage />;
    }
    if (tab === "progress") {
      return <ProgressPage />;
    }
    return <HomePage onNavigate={navigate} />;
  })();

  return (
    <AppShell
      tab={tab}
      onTabChange={setTab}
      onOpenSettings={() => setFlow("settings")}
      showNav={flow === null}
    >
      {content}
    </AppShell>
  );
};
