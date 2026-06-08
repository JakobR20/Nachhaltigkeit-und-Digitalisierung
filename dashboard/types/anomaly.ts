// Mirrors backend/app/models/schemas.py

export type Severity = "hoch" | "mittel" | "niedrig";

export interface AnomalyListItem {
  nr: string;
  site: string;
  timestamp: string;
  method: string;
  segment: string;
  schweregrad: Severity;
  confidence: number;
  mehrkosten_eur: number | null;
  jahreskosten_eur: number | null;
  diff_kw: number | null;
  diff_pct: number | null;
  value_kw: number | null;
  expected_kw: number | null;
  vermutete_ursache: string;
  also_flagged_by: string[];
  is_underconsumption: boolean;
  is_negative_price: boolean;
}

export interface LoadPoint {
  timestamp: string;
  value_kw: number;
  expected_kw: number | null;
}

export interface CostBreakdown {
  diff_kw: number | null;
  dauer_h: number;
  diff_kwh: number | null;
  spotpreis_ct: number | null;
  mehrkosten_eur: number | null;
  jahreskosten_eur: number | null;
  is_underconsumption: boolean;
  is_negative_price: boolean;
}

export interface Conditions {
  temperatur_c: number | null;
  wetter_beschreibung: string | null;
  wochentag: string | null;
  feiertag: string | null;
  confidence: number;
}

export interface AnomalyDetail {
  nr: string;
  site: string;
  timestamp: string;
  method: string;
  segment: string;
  schweregrad: Severity;
  vermutete_ursache: string;
  handlungsempfehlungen: string[];
  also_flagged_by: string[];
  cost: CostBreakdown;
  conditions: Conditions;
  load_curve: LoadPoint[];
  expected_kw: number | null;
  value_kw: number | null;
}

export interface MethodStat {
  method: string;
  label: string;
  description: string;
  count: number;
}

export interface EnsembleStats {
  methods: MethodStat[];
  kappa: Record<string, number>;
}

export interface SiteItem {
  site: string;
  anomaly_count: number;
  is_special: boolean;
}

export interface SweepPoint {
  threshold_pct: number;
  arima: number | null;
  autoencoder: number | null;
  cluster_segment: number | null;
  zscore_stl: number | null;
}

export interface InferenceCost {
  method: string;
  fit_s: number;
  score_s: number;
}

export interface MethodComparison {
  kappa: Record<string, number>;
  sweep: SweepPoint[];
  inference: InferenceCost[];
  table_markdown: string;
}

export interface AnomalyFilters {
  site?: string;
  date_from?: string;
  date_to?: string;
  min_cost?: number;
  sort_by?: "cost" | "date" | "severity";
}
