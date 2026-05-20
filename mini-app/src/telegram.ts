type TelegramThemeParams = {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  secondary_bg_color?: string;
  button_color?: string;
  button_text_color?: string;
};

type TelegramWebApp = {
  initData: string;
  colorScheme?: "light" | "dark";
  themeParams?: TelegramThemeParams;
  ready: () => void;
  expand: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  enableClosingConfirmation?: () => void;
  disableClosingConfirmation?: () => void;
};

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export const tg = window.Telegram?.WebApp;

export const getTelegramInitData = (): string => tg?.initData ?? "";

export const isTelegramMiniApp = (): boolean => Boolean(tg?.initData);

export const setDraftProtection = (enabled: boolean): void => {
  if (!tg) {
    return;
  }

  if (enabled) {
    tg.enableClosingConfirmation?.();
  } else {
    tg.disableClosingConfirmation?.();
  }
};

export const setupTelegramApp = (): void => {
  if (!tg) {
    document.documentElement.dataset.telegramTheme = "outside";
    return;
  }

  tg.ready();
  tg.expand();
  tg.setHeaderColor?.("#2f2230");
  tg.setBackgroundColor?.("#2f2230");

  document.documentElement.dataset.telegramTheme = tg.colorScheme ?? "light";

  const theme = tg.themeParams;
  if (theme?.text_color) {
    document.documentElement.style.setProperty("--tg-text-color", theme.text_color);
  }
  if (theme?.hint_color) {
    document.documentElement.style.setProperty("--tg-hint-color", theme.hint_color);
  }
  if (theme?.secondary_bg_color) {
    document.documentElement.style.setProperty("--tg-secondary-bg-color", theme.secondary_bg_color);
  }
};
