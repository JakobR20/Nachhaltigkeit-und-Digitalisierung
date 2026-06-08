"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchMethodComparison } from "@/lib/api";
import { METHOD_COLORS, METHOD_LABELS } from "@/lib/format";
import type { InferenceCost, SweepPoint } from "@/types/anomaly";

const METHODS = ["zscore_stl", "arima", "cluster_segment", "autoencoder"];

export function ResearchView() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["method-comparison"],
    queryFn: fetchMethodComparison,
  });

  return (
    <main>
      <Link href="/" className="text-[14px] font-medium text-hig-accent">
        ‹ Zurück zur Kostenübersicht
      </Link>
      <h1 className="mb-1 mt-2 text-[22px] font-semibold text-hig-text">
        Forschungs-Ansicht — Methoden im Detail
      </h1>
      <p className="mb-4 text-[13px] text-hig-secondary">
        Diese Ansicht ist primär für die wissenschaftliche Dokumentation gedacht.
      </p>

      {isError && (
        <Card className="rounded-xl bg-hig-card p-6 text-center shadow-sm">
          <p className="font-medium text-severity-high">Backend nicht erreichbar</p>
          <p className="mt-1 text-[14px] text-hig-secondary">
            Läuft uvicorn auf Port 8000? Starte es mit
            <code className="mx-1 rounded bg-black/5 px-1">
              uvicorn app.main:app --reload --app-dir backend
            </code>
          </p>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="mt-3 rounded-lg bg-hig-accent px-4 py-1.5 text-[14px] font-medium text-white disabled:opacity-50"
          >
            {isFetching ? "Lädt…" : "Erneut versuchen"}
          </button>
        </Card>
      )}
      {isLoading && <Skeleton className="h-96 w-full rounded-xl" />}
      {data && (
        <>
          <KappaCard kappa={data.kappa} />
          <InferenceCard inference={data.inference} />
          <SweepCard sweep={data.sweep} />
          <TableCard markdown={data.table_markdown} />
        </>
      )}
    </main>
  );
}

function KappaCard({ kappa }: { kappa: Record<string, number> }) {
  const cell = (a: string, b: string) =>
    a === b ? 1 : (kappa[`${a}|${b}`] ?? null);
  const color = (v: number | null) => {
    if (v === null) return "#fff";
    const t = Math.max(0, Math.min(1, v));
    return `rgba(0,122,255,${0.12 + t * 0.7})`;
  };
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-3 text-[15px] font-semibold text-hig-text">
        Komplementarität (Cohen&apos;s κ)
      </h3>
      <div className="grid grid-cols-[120px_repeat(4,1fr)] gap-1 text-[12px]">
        <div />
        {METHODS.map((m) => (
          <div key={m} className="truncate text-center text-hig-secondary">
            {METHOD_LABELS[m]}
          </div>
        ))}
        {METHODS.map((a) => (
          <FragmentRow key={a} a={a} cell={cell} color={color} />
        ))}
      </div>
      <p className="mt-3 text-[13px] text-hig-secondary">
        Niedrige κ-Werte = kaum Überlappung, komplementäre Sichten.
      </p>
    </Card>
  );
}

function FragmentRow({
  a,
  cell,
  color,
}: {
  a: string;
  cell: (a: string, b: string) => number | null;
  color: (v: number | null) => string;
}) {
  return (
    <>
      <div className="self-center text-hig-secondary">{METHOD_LABELS[a]}</div>
      {METHODS.map((b) => {
        const v = cell(a, b);
        return (
          <div
            key={b}
            className="rounded py-2 text-center tabular-nums text-hig-text"
            style={{ backgroundColor: color(v) }}
          >
            {v === null ? "" : v.toFixed(2)}
          </div>
        );
      })}
    </>
  );
}

function InferenceCard({ inference }: { inference: InferenceCost[] }) {
  const data = inference.map((i) => ({
    method: METHOD_LABELS[i.method] ?? i.method,
    "fit (s)": i.fit_s,
    "score (s)": i.score_s,
  }));
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-3 text-[15px] font-semibold text-hig-text">
        Inferenzkosten (Wall-Time, 5 Standorte)
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="#E5E5EA" vertical={false} />
          <XAxis dataKey="method" tick={{ fontSize: 12, fill: "#8E8E93" }} stroke="#E5E5EA" />
          <YAxis tick={{ fontSize: 12, fill: "#8E8E93" }} stroke="#E5E5EA" unit=" s" />
          <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #E5E5EA", fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="fit (s)" fill="#007AFF" radius={[4, 4, 0, 0]} />
          <Bar dataKey="score (s)" fill="#FF9500" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-1 text-[13px] text-hig-secondary">
        ARIMA dominiert die Kosten; Z-Score und Cluster sind quasi gratis.
      </p>
    </Card>
  );
}

function SweepCard({ sweep }: { sweep: SweepPoint[] }) {
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-3 text-[15px] font-semibold text-hig-text">
        Schwellwert-Sweep (Flag-Rate über Aggregations-Anteil)
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={sweep} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="#E5E5EA" vertical={false} />
          <XAxis
            dataKey="threshold_pct"
            tick={{ fontSize: 12, fill: "#8E8E93" }}
            stroke="#E5E5EA"
          />
          <YAxis tick={{ fontSize: 12, fill: "#8E8E93" }} stroke="#E5E5EA" unit=" %" />
          <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #E5E5EA", fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {METHODS.map((m) => (
            <Line
              key={m}
              type="monotone"
              dataKey={m}
              name={METHOD_LABELS[m]}
              stroke={METHOD_COLORS[m]}
              strokeWidth={1.5}
              dot={{ r: 3 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

function TableCard({ markdown }: { markdown: string }) {
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-3 text-[15px] font-semibold text-hig-text">
        Vergleichstabelle (Schritt 11)
      </h3>
      <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[12px] text-hig-text">
        {markdown}
      </pre>
    </Card>
  );
}
