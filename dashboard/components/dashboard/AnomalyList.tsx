"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";
import { fetchAnomalies } from "@/lib/api";
import { fmtEur } from "@/lib/format";
import type { AnomalyFilters } from "@/types/anomaly";

import { AnomalyCard } from "./AnomalyCard";

export function paramsToFilters(params: URLSearchParams): AnomalyFilters {
  const f: AnomalyFilters = {};
  const site = params.get("site");
  if (site) f.site = site;
  const minCost = params.get("min_cost");
  if (minCost && minCost !== "0") f.min_cost = Number(minCost);
  const sort = params.get("sort");
  if (sort === "date" || sort === "severity" || sort === "cost") f.sort_by = sort;
  const period = params.get("period");
  if (period === "30d" || period === "90d") {
    const days = period === "30d" ? 30 : 90;
    const from = new Date();
    from.setDate(from.getDate() - days);
    f.date_from = from.toISOString().slice(0, 10);
  }
  return f;
}

export function AnomalyList() {
  const params = useSearchParams();
  const filters = paramsToFilters(params);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["anomalies", filters],
    queryFn: () => fetchAnomalies(filters),
  });

  if (isError) {
    return (
      <div className="rounded-xl bg-hig-card p-6 text-center shadow-sm">
        <p className="font-medium text-severity-high">Backend nicht erreichbar</p>
        <p className="mt-1 text-[14px] text-hig-secondary">
          Läuft uvicorn auf Port 8000? Starte das Backend mit
          <code className="mx-1 rounded bg-black/5 px-1">
            uvicorn app.main:app --reload --app-dir backend
          </code>
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  const items = data!;
  const total = items.reduce((s, a) => s + (a.jahreskosten_eur ?? 0), 0);
  const sortBy = params.get("sort") ?? "cost";

  const SECTIONS: { key: "hoch" | "mittel" | "niedrig"; label: string }[] = [
    { key: "hoch", label: "Hoch" },
    { key: "mittel", label: "Mittel" },
    { key: "niedrig", label: "Niedrig" },
  ];

  return (
    <div>
      {sortBy === "severity" ? (
        items.map((a) => <AnomalyCard key={a.nr} a={a} />)
      ) : (
        SECTIONS.map(({ key, label }) => {
          const group = items.filter((a) => a.schweregrad === key);
          if (group.length === 0) return null;
          return (
            <section key={key} className="mb-5">
              <h2 className="mb-2 text-[13px] font-semibold uppercase tracking-wide text-hig-secondary">
                {label} · {group.length}
              </h2>
              {group.map((a) => (
                <AnomalyCard key={a.nr} a={a} />
              ))}
            </section>
          );
        })
      )}
      <p className="mt-4 text-[13px] text-hig-secondary">
        {items.length} Anomalien · {fmtEur(total)} hochgerechnet (jährlich)
        <br />
        <a href="/research" className="text-hig-accent">
          Weitere ~2.000 statistische Detektionen — Forschungs-Ansicht →
        </a>
      </p>
    </div>
  );
}
