import { getTelegramInitData } from "../telegram";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";

export type DailyAction =
  | "breakfast"
  | "lunch"
  | "dinner"
  | "water"
  | "focus"
  | "journal"
  | "mood"
  | "sleep"
  | "small_win";

export type SourcePersona = "bot" | "nurasyl";
export type MoodState =
  | "calm"
  | "normal"
  | "tired"
  | "anxious"
  | "sad"
  | "overloaded"
  | "no_energy"
  | "productive";
export type JournalEntryType = "note" | "win" | "gratitude" | "idea" | "focus" | "evening";
export type FocusStatus = "started" | "completed" | "partial" | "cancelled";
export type ComplimentFrequency = "low" | "normal" | "high";

export type ContentTemplate = {
  template_id: string;
  category: string;
  subcategory?: string;
  source_persona: SourcePersona;
  tone?: string;
  text: string;
  is_fallback?: boolean;
};

export type TodayPatchKey =
  | "breakfast_done"
  | "lunch_done"
  | "dinner_done"
  | "water_count"
  | "focus_done"
  | "journal_done"
  | "mood_done"
  | "small_win_done"
  | "sleep_prep_done";

export type TodayItem = {
  key: string;
  action: DailyAction;
  title: string;
  done: boolean;
  value: boolean | number;
};

export type TodaySummary = {
  date: string;
  local_date: string;
  timezone: string;
  breakfast_done: boolean;
  lunch_done: boolean;
  dinner_done: boolean;
  water_count: number;
  focus_done: boolean;
  journal_done: boolean;
  mood_done: boolean;
  small_win_done: boolean;
  sleep_prep_done: boolean;
  completed_count: number;
  total_count: number;
  items: TodayItem[];
};

export type NextBestAction = {
  action: DailyAction | "rest";
  title: string;
  message: string;
};

export type MoodCheckin = {
  mood: MoodState;
  energy?: number;
  note?: string;
  created_at: string;
  local_date: string;
};

export type JournalEntry = {
  id: string;
  entry_id: string;
  type: JournalEntryType;
  text: string;
  tags: string[];
  created_at: string | null;
  local_date: string;
  is_deleted: boolean;
};

export type RollingProgress = {
  days: number;
  days_with_support: number;
  tasks_completed: number;
  tasks_possible: number;
  completion_ratio?: number;
  support_actions_completed: number;
  water_count: number;
  focus_days: number;
  focus_minutes: number;
  journal_count: number;
  mood_count?: number;
  small_wins: number;
  sleep_prep_days: number;
  daily_supports?: Array<{
    local_date: string;
    completed_count: number;
    total_count: number;
  }>;
  note: string;
};

export type Dashboard = {
  user: {
    telegram_id: number;
    timezone: string;
    active_day: number;
  };
  local_date: string;
  today_summary: TodaySummary;
  next_best_action: NextBestAction;
  latest_mood: MoodCheckin | null;
  latest_journal_entries: JournalEntry[];
  progress_snapshot: RollingProgress;
  message_of_day: ContentTemplate | null;
  random_gentle_message: ContentTemplate | null;
};

export type Progress = {
  today: TodaySummary;
  rolling_7_day: RollingProgress;
  rolling_30_day: RollingProgress;
  rolling_40_day: RollingProgress;
  rolling_28_day: RollingProgress;
  soft_30_40_day_progress?: {
    last_30_days: RollingProgress;
    last_40_days: RollingProgress;
    note: string;
  };
  focus_minutes: {
    last_7_days: number;
    last_30_days?: number;
    last_40_days?: number;
    last_28_days: number;
  };
  journal_count: {
    last_7_days: number;
    last_30_days?: number;
    last_40_days?: number;
    last_28_days: number;
  };
  mood_count?: {
    last_7_days: number;
    last_30_days?: number;
    last_40_days?: number;
    last_28_days: number;
  };
  small_wins: {
    last_7_days: number;
    last_30_days?: number;
    last_40_days?: number;
    last_28_days: number;
  };
  support_completed: {
    last_7_days: number;
    last_30_days?: number;
    last_40_days?: number;
    last_28_days: number;
  };
  daily_supports?: {
    today: TodaySummary;
    last_7_days: RollingProgress["daily_supports"];
    last_30_days: RollingProgress["daily_supports"];
    last_40_days: RollingProgress["daily_supports"];
  };
  message: string;
};

export type FocusSession = {
  session_id: string;
  planned_minutes: number;
  completed_minutes: number;
  label?: string;
  status: FocusStatus;
  started_at: string;
  completed_at?: string | null;
  local_date: string;
};

export type Settings = {
  reminders_enabled: boolean;
  morning_enabled: boolean;
  meal_enabled: boolean;
  water_enabled: boolean;
  focus_enabled: boolean;
  sleep_enabled: boolean;
  mood_enabled: boolean;
  random_compliments_enabled: boolean;
  romantic_from_nurasyl_enabled: boolean;
  compliment_frequency: ComplimentFrequency;
  max_messages_per_day: number;
  quiet_hours_start: string;
  quiet_hours_end: string;
  preferred_wake_time: string;
  preferred_sleep_time: string;
  breakfast_time: string;
  lunch_time: string;
  dinner_time: string;
  focus_time: string;
  pause_until?: string | null;
};

export type TodayPatchResponse = {
  day: TodaySummary;
  updated_action: DailyAction;
  reactive_feedback: ContentTemplate | null;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
  const initData = getTelegramInitData();

  if (!initData) {
    throw new ApiError(401, "Telegram initData is missing");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(response.status, message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
};

export const isAuthError = (error: unknown): boolean =>
  error instanceof ApiError && (error.status === 401 || error.status === 403);

export const api = {
  dashboard: () => request<Dashboard>("/dashboard"),
  today: () => request<TodaySummary>("/today"),
  updateToday: (payload: {
    action?: DailyAction;
    key?: TodayPatchKey;
    done?: boolean;
    value?: boolean | number;
  }) =>
    request<TodayPatchResponse>("/today", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  startFocus: (plannedMinutes: 15 | 25 | 45, label?: string) =>
    request<{ session: FocusSession }>("/focus/start", {
      method: "POST",
      body: JSON.stringify({ planned_minutes: plannedMinutes, label: label || null }),
    }),
  completeFocus: (sessionId: string, completedMinutes: number, status: "completed" | "partial") =>
    request<{ session: FocusSession; feedback: ContentTemplate | null }>(
      `/focus/${sessionId}/complete`,
      {
        method: "POST",
        body: JSON.stringify({ completed_minutes: completedMinutes, status }),
      },
    ),
  cancelFocus: (sessionId: string) =>
    request<{ session: FocusSession }>(`/focus/${sessionId}/cancel`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  mood: (payload: { mood: MoodState; energy?: number | null; note?: string | null }) =>
    request<{ mood: MoodCheckin }>("/mood", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  journal: (params: { type?: JournalEntryType; localDate?: string; limit?: number; offset?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.type) {
      query.set("type", params.type);
    }
    if (params.localDate) {
      query.set("local_date", params.localDate);
    }
    if (params.limit) {
      query.set("limit", String(params.limit));
    }
    if (params.offset) {
      query.set("offset", String(params.offset));
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<{ items: JournalEntry[]; limit: number; offset: number }>(`/journal${suffix}`);
  },
  addJournalEntry: (payload: { type: JournalEntryType; text: string; tags?: string[] }) =>
    request<{ entry: JournalEntry }>("/journal", {
      method: "POST",
      body: JSON.stringify({ ...payload, tags: payload.tags ?? [] }),
    }),
  progress: () => request<Progress>("/progress"),
  settings: () => request<Settings>("/settings"),
  updateSettings: (payload: Partial<Settings>) =>
    request<Settings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  pause: (payload: {
    mode?: "1h" | "until_evening" | "today";
    pause_until?: string;
    minutes?: number;
    categories?: string[];
  }) =>
    request<{ mode: string; pause_until: string; categories: string[]; settings: Settings }>("/pause", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  randomCompliment: (sourcePersona?: SourcePersona) =>
    request<{ template: ContentTemplate | null }>("/compliment/random", {
      method: "POST",
      body: JSON.stringify({ source_persona: sourcePersona }),
    }),
  exportData: () => request<Record<string, unknown>>("/export", { method: "POST" }),
  deleteMe: () => request<{ deleted: boolean; deleted_counts: Record<string, number> }>("/me", {
    method: "DELETE",
  }),
};
