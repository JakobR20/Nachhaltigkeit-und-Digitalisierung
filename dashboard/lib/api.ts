import axios from "axios";

import type {
  AnomalyDetail,
  AnomalyFilters,
  AnomalyListItem,
  EnsembleStats,
  SiteItem,
} from "@/types/anomaly";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30000,
});

export async function fetchAnomalies(
  filters: AnomalyFilters = {},
): Promise<AnomalyListItem[]> {
  const { data } = await api.get<AnomalyListItem[]>("/api/anomalies", {
    params: filters,
  });
  return data;
}

export async function fetchAnomaly(nr: string): Promise<AnomalyDetail> {
  const { data } = await api.get<AnomalyDetail>(`/api/anomalies/${nr}`);
  return data;
}

export async function fetchEnsembleStats(): Promise<EnsembleStats> {
  const { data } = await api.get<EnsembleStats>("/api/ensemble-stats");
  return data;
}

export async function fetchSites(): Promise<SiteItem[]> {
  const { data } = await api.get<SiteItem[]>("/api/sites");
  return data;
}
