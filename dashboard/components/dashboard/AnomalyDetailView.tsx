"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAnomaly } from "@/lib/api";
import { fmtDateTime, segmentDe } from "@/lib/format";

import { AiCard, ConditionsCard, DetectionCard } from "./AnalysisCards";
import { CostCard } from "./CostCard";
import { LoadChart } from "./LoadChart";

export function AnomalyDetailView({ nr }: { nr: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["anomaly", nr],
    queryFn: () => fetchAnomaly(nr),
  });

  const back = (
    <Link href="/" className="text-[14px] font-medium text-hig-accent">
      ‹ Zurück zur Übersicht
    </Link>
  );

  if (isError) {
    return (
      <main>
        {back}
        <div className="mt-4 rounded-xl bg-hig-card p-6 text-center shadow-sm">
          <p className="font-medium text-severity-high">Backend nicht erreichbar</p>
          <p className="mt-1 text-[14px] text-hig-secondary">
            Läuft uvicorn auf Port 8000?
          </p>
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main>
        {back}
        <Skeleton className="mt-4 h-8 w-80" />
        <Skeleton className="mt-4 h-72 w-full rounded-xl" />
        <Skeleton className="mt-4 h-40 w-full rounded-xl" />
      </main>
    );
  }

  const d = data!;
  const { date } = fmtDateTime(d.timestamp);

  return (
    <main>
      {back}
      <h1 className="mb-4 mt-2 text-[24px] font-bold text-hig-text">
        {d.site} · {segmentDe(d.segment)} · {date}
      </h1>
      <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
        <LoadChart detail={d} />
      </Card>
      <CostCard detail={d} />
      <AiCard detail={d} />
      <DetectionCard detail={d} />
      <ConditionsCard detail={d} />
    </main>
  );
}
