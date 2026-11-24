export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

export type Severity = "info" | "action" | "urgent";

export interface Deadline {
  label: string;
  due_date: string;
  due_date_display: string;
  notification_date: string | null;
  steps: string[];
  warnings: string[];
  kind: "period" | "explicit";
  days_left: number;
  type: "appeal" | "payment" | "action" | "appointment";
}

export interface Payment {
  recipient: string;
  iban: string;
  iban_valid: boolean;
  bic: string | null;
  reference: string | null;
  amount_eur: number | null;
}

export interface LetterCard {
  letter_id: number;
  case_id: number;
  linked_to_existing_case?: boolean;
  sender: { name: string; category: string; label: string; address: string | null };
  letter_type: { id: string; name_de: string; name_en: string; appeal_name: string | null };
  title: string;
  letter_date: string | null;
  severity: Severity;
  tldr: string;
  details: string;
  what_it_is: string;
  if_ignored: string;
  check_this: string[];
  required_actions: string[];
  reference_numbers: { label: string; value: string }[];
  amounts: { label: string; amount_eur: number; direction: "you_receive" | "you_pay" | "info"; due_date: string | null }[];
  payment: Payment | null;
  deadlines: Deadline[];
  checklist: string[];
  reply_templates: { id: string; title: string; channel: string }[];
  line_by_line: { de: string; en: string }[];
  glossary: Record<string, string>;
  confidence: number;
  warnings: string[];
  bundesland: string;
  disclaimer: string;
}

export interface TemplateField {
  name: string;
  label: string;
  required: boolean;
  multiline: boolean;
  placeholder: string;
}

export interface ReplyTemplate {
  id: string;
  title: string;
  channel: string;
  fields: TemplateField[];
}

export interface Meta {
  bundeslaender: Record<string, string>;
  default_bundesland: string;
  reply_templates: ReplyTemplate[];
  samples: { id: string; label: string; preview: string }[];
  case_statuses: string[];
  ai_provider: "anthropic" | "ollama";
  ai_model: string;
  /** Official product name, e.g. "Qwen2.5-VL 7B by Alibaba Cloud" */
  ai_model_name: string;
}

export interface Draft {
  template_id: string;
  subject_de: string;
  body_de: string;
  body_en: string;
  channel: string;
}

export interface CaseSummary {
  id: number;
  title: string;
  sender_name: string;
  sender_category: string;
  reference: string | null;
  status: string;
  updated_at: string;
  letter_count: number;
  next_deadline: Deadline | null;
  needs_follow_up: boolean;
  letters?: { id: number; title: string; letter_date: string | null; severity: Severity; created_at: string }[];
  timeline?: { kind: string; text: string; at: string }[];
}

export interface ReadingJob {
  id: string;
  status: "queued" | "running" | "done" | "error";
  stage: string;
  elapsed_s: number;
  result: LetterCard | null;
  error: string | null;
}

const IS_LOCAL = /\/\/(localhost|127\.0\.0\.1)[:/]/.test(API_URL);
const OWNER_KEY = "briefly.owner";

/**
 * A random id for this browser, sent with every request. The backend shows
 * each browser only its own cases, so visitors never see each other's letters.
 */
function ownerId(): string {
  let id = localStorage.getItem(OWNER_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(OWNER_KEY, id);
  }
  return id;
}

/** fetch() against the backend, with this browser's id attached. */
async function backend(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("X-Briefly-Owner", ownerId());
  try {
    return await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    const onLocalPage = /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);
    throw new Error(
      IS_LOCAL && !onLocalPage
        ? "This website isn't connected to its server yet, so letters can't be read here. Please check back soon."
        : IS_LOCAL
        ? `Can't reach the backend. Is it running on ${API_URL}?`
        : "Can't reach the server. It sleeps when nobody uses it and takes about a minute to wake up. Please try again shortly.",
    );
  }
}

/** Save a response as a file download. */
async function download(res: Response, filename: string) {
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await backend(path, init);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch {}
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  meta: () => request<Meta>("/api/meta"),
  glossary: () => request<Record<string, string>>("/api/glossary"),
  analyze: (files: File[], bundesland: string) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("bundesland", bundesland);
    return request<LetterCard>("/api/letters/analyze", { method: "POST", body: fd });
  },
  startReading: (files: File[], bundesland: string) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("bundesland", bundesland);
    return request<ReadingJob>("/api/letters/analyze/jobs", { method: "POST", body: fd });
  },
  job: (id: string) => request<ReadingJob>(`/api/jobs/${id}`),
  sample: (id: string, bundesland: string) =>
    request<LetterCard>(`/api/letters/sample/${id}?bundesland=${bundesland}`, { method: "POST" }),
  letter: (id: number | string) => request<LetterCard>(`/api/letters/${id}`),
  recompute: (id: number, body: { letter_date?: string; received_date?: string; bundesland?: string }) =>
    request<LetterCard>(`/api/letters/${id}/recompute`, json(body)),
  computeDeadline: (body: Record<string, unknown>) => request<Deadline>("/api/deadlines/compute", json(body)),
  prefill: (templateId: string, letterId: number) =>
    request<Record<string, string>>(`/api/replies/prefill?template_id=${templateId}&letter_id=${letterId}`),
  draft: (templateId: string, values: Record<string, string>, letterId?: number) =>
    request<Draft>("/api/replies/draft", json({ template_id: templateId, values, letter_id: letterId })),
  cases: () => request<CaseSummary[]>("/api/cases"),
  case: (id: number | string) => request<CaseSummary>(`/api/cases/${id}`),
  setStatus: (id: number, status: string) =>
    request<CaseSummary>(`/api/cases/${id}`, { ...json({ status }), method: "PATCH" }),
  deleteCase: (id: number) => request<{ deleted: number }>(`/api/cases/${id}`, { method: "DELETE" }),
  pdf: async (body: Record<string, string>): Promise<Blob> => {
    const res = await backend("/api/replies/pdf", json(body));
    if (!res.ok) throw new Error("Could not create the PDF");
    return res.blob();
  },
  downloadIcs: async (letterId: number) => {
    const res = await backend(`/api/letters/${letterId}/calendar.ics`);
    if (!res.ok) throw new Error("Could not create the calendar file");
    await download(res, `briefly-letter-${letterId}.ics`);
  },
  /** GiroCode as an object URL for an <img>; revoke it when done. */
  girocode: async (letterId: number): Promise<string> => {
    const res = await backend(`/api/letters/${letterId}/girocode.svg`);
    if (!res.ok) throw new Error("No GiroCode for this letter");
    return URL.createObjectURL(await res.blob());
  },
};

export const STATUS_LABELS: Record<string, string> = {
  new: "New",
  understood: "Understood",
  action_needed: "Action needed",
  replied: "Replied",
  waiting: "Waiting for answer",
  closed: "Closed",
};

export function euro(n: number): string {
  return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" }).format(n);
}

export function deDate(iso: string | null): string {
  if (!iso) return "–";
  const [y, m, d] = iso.slice(0, 10).split("-");
  return `${d}.${m}.${y}`;
}
