import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { AnomalyListItem, EnsembleStats } from "@/types/anomaly";

import { AnomalyCard } from "../AnomalyCard";
import { paramsToFilters } from "../AnomalyList";
import { EnsembleCard } from "../EnsembleCard";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

const ENSEMBLE: EnsembleStats = {
  methods: [
    { method: "zscore_stl", label: "Z-Score-STL", description: "Punkt-Anomalien", count: 66074 },
    { method: "arima", label: "ARIMA-Forecast", description: "Vorhersage-Abweichungen", count: 55475 },
    { method: "cluster_segment", label: "Cluster-Distanz", description: "Tagessegmente", count: 801 },
    { method: "autoencoder", label: "Autoencoder", description: "Formauffälligkeiten", count: 24399 },
  ],
  kappa: { "arima|autoencoder": 0.11 },
};

const ANOMALY: AnomalyListItem = {
  nr: "21", site: "Baumarkt_08", timestamp: "2024-05-08T02:00:00+02:00",
  method: "cluster_segment", segment: "nachts", schweregrad: "hoch", confidence: 0.85,
  mehrkosten_eur: 45.95, jahreskosten_eur: 16771.75, diff_kw: 59.5, diff_pct: 807,
  value_kw: 72.6, expected_kw: 8.0, vermutete_ursache: "HVAC läuft nachts durch.",
  also_flagged_by: [], is_underconsumption: false, is_negative_price: false,
};

vi.mock("@/lib/api", () => ({
  fetchEnsembleStats: () => Promise.resolve(ENSEMBLE),
}));

function withClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

describe("paramsToFilters", () => {
  it("maps min_cost and sort", () => {
    const f = paramsToFilters(new URLSearchParams("min_cost=10&sort=date"));
    expect(f.min_cost).toBe(10);
    expect(f.sort_by).toBe("date");
  });

  it("maps period to a date_from", () => {
    const f = paramsToFilters(new URLSearchParams("period=30d"));
    expect(f.date_from).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("ignores defaults", () => {
    const f = paramsToFilters(new URLSearchParams("min_cost=0&period=all"));
    expect(f.min_cost).toBeUndefined();
    expect(f.date_from).toBeUndefined();
  });
});

describe("EnsembleCard", () => {
  it("renders the four methods with counts", async () => {
    render(withClient(<EnsembleCard />));
    await waitFor(() => expect(screen.getByText("Z-Score-STL")).toBeInTheDocument());
    expect(screen.getByText("ARIMA-Forecast")).toBeInTheDocument();
    expect(screen.getByText(/Komplementarität/)).toBeInTheDocument();
  });
});

describe("AnomalyCard", () => {
  it("renders cost, site and severity", () => {
    render(withClient(<AnomalyCard a={ANOMALY} />));
    expect(screen.getByText("Baumarkt_08")).toBeInTheDocument();
    expect(screen.getByText("hoch")).toBeInTheDocument();
    expect(screen.getByText(/45,95/)).toBeInTheDocument();
    expect(screen.getByText(/Details/)).toBeInTheDocument();
  });
});
