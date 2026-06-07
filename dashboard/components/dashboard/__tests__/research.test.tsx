import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { MethodComparison } from "@/types/anomaly";

import { ResearchView } from "../ResearchView";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const MC: MethodComparison = {
  kappa: {
    "arima|autoencoder": 0.11, "autoencoder|arima": 0.11,
    "arima|zscore_stl": 0.08, "zscore_stl|arima": 0.08,
  },
  sweep: [
    { threshold_pct: 0, arima: 28.6, autoencoder: 14.2, cluster_segment: 0.6, zscore_stl: 13.1 },
    { threshold_pct: 0.25, arima: 1.0, autoencoder: 1.2, cluster_segment: 0.6, zscore_stl: 3.9 },
  ],
  inference: [
    { method: "arima", fit_s: 118.36, score_s: 50.06 },
    { method: "zscore_stl", fit_s: 0, score_s: 0 },
  ],
  table_markdown: "| Methode | ... |",
};

vi.mock("@/lib/api", () => ({
  fetchMethodComparison: () => Promise.resolve(MC),
}));

function withClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

describe("ResearchView", () => {
  it("renders all four cards without crashing", async () => {
    render(withClient(<ResearchView />));
    await waitFor(() =>
      expect(screen.getByText(/Komplementarität/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Inferenzkosten/)).toBeInTheDocument();
    expect(screen.getByText(/Schwellwert-Sweep/)).toBeInTheDocument();
    expect(screen.getByText(/Vergleichstabelle/)).toBeInTheDocument();
  });
});
