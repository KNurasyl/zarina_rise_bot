export const formatDate = (value?: string | null): string => {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
};

export const formatTime = (value?: string | null): string => {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const getGreeting = (): string => {
  const hour = new Date().getHours();

  if (hour < 11) {
    return "Доброе утро";
  }
  if (hour < 17) {
    return "Добрый день";
  }
  return "Добрый вечер";
};

export const endOfTodayIso = (): string => {
  const end = new Date();
  end.setHours(23, 59, 0, 0);
  return end.toISOString();
};

export const eveningIso = (): string => {
  const evening = new Date();
  evening.setHours(20, 30, 0, 0);
  if (evening.getTime() < Date.now()) {
    evening.setHours(23, 59, 0, 0);
  }
  return evening.toISOString();
};
