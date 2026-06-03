import type { Severity } from "@/types/anomaly";

const MONTHS_DE = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];
const SEGMENT_DE: Record<string, string> = {
  nachts: "Nachts", vormittag: "Vormittag", mittag: "Mittag", nachmittag: "Nachmittag",
};

export const METHOD_COLORS: Record<string, string> = {
  zscore_stl: "#007AFF",
  arima: "#FF3B30",
  cluster_segment: "#34C759",
  autoencoder: "#AF52DE",
};
export const METHOD_LABELS: Record<string, string> = {
  zscore_stl: "Z-Score-STL",
  arima: "ARIMA-Forecast",
  cluster_segment: "Cluster-Distanz",
  autoencoder: "Autoencoder",
};
export const METHOD_CATEGORY: Record<string, string> = {
  zscore_stl: "Punkt-Anomalie (einzelner Messzeitpunkt)",
  arima: "Vorhersage-Abweichung (Forecast vs. Real)",
  cluster_segment: "Segment-Anomalie (Tagessegment auffällig)",
  autoencoder: "Form-Anomalie (Rekonstruktionsfehler)",
};

export const SEVERITY_COLOR: Record<Severity, string> = {
  hoch: "var(--severity-high)",
  mittel: "var(--severity-medium)",
  niedrig: "var(--severity-low)",
};

export function fmtEur(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(v);
}

export function fmtDateTime(ts: string): { date: string; time: string } {
  const d = new Date(ts);
  return {
    date: `${d.getDate()}. ${MONTHS_DE[d.getMonth()]} ${d.getFullYear()}`,
    time: d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" }),
  };
}

export function segmentDe(seg: string): string {
  return SEGMENT_DE[seg] ?? seg;
}

export function truncate(s: string, max = 80): string {
  if (s.length <= max) return s;
  return s.slice(0, max).replace(/\s\S*$/, "") + "…";
}
