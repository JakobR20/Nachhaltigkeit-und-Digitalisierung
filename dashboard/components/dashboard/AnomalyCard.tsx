"use client";

import { useRouter } from "next/navigation";

import { Card } from "@/components/ui/card";
import {
  METHOD_COLORS,
  METHOD_LABELS,
  fmtDateTime,
  fmtEur,
  segmentDe,
  truncate,
} from "@/lib/format";
import type { AnomalyListItem } from "@/types/anomaly";

import { SeverityBadge } from "./SeverityBadge";

export function AnomalyCard({ a }: { a: AnomalyListItem }) {
  const router = useRouter();
  const { date, time } = fmtDateTime(a.timestamp);

  const lastLine =
    a.diff_kw !== null && a.diff_kw >= 0
      ? a.diff_pct !== null
        ? `+${a.diff_pct.toFixed(0)}% Last (${a.value_kw?.toFixed(1)} kW statt ${a.expected_kw?.toFixed(1)} kW)`
        : `${a.value_kw?.toFixed(1)} kW (Erwartung ${a.expected_kw?.toFixed(1)} kW)`
      : `Minderverbrauch ${a.diff_kw?.toFixed(1)} kW (Erwartung ${a.expected_kw?.toFixed(1)} kW)`;

  const methodLine =
    a.also_flagged_by.length > 0
      ? `${METHOD_LABELS[a.method] ?? a.method} · auch erkannt von ${a.also_flagged_by.map((m) => METHOD_LABELS[m] ?? m).join(", ")}`
      : METHOD_LABELS[a.method] ?? a.method;

  return (
    <Card
      onClick={() => router.push(`/anomaly/${a.nr}`)}
      className="mb-4 cursor-pointer rounded-xl bg-hig-card p-5 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-3">
          <span className="tabular-nums text-[28px] font-bold leading-none text-hig-text">
            {fmtEur(a.mehrkosten_eur)}
          </span>
          <SeverityBadge severity={a.schweregrad} />
        </div>
        <span className="text-[17px] font-medium text-hig-text">{a.site}</span>
      </div>
      <div className="mt-1.5 text-[14px] text-hig-secondary">
        {segmentDe(a.segment)}, {date}, {time} Uhr
      </div>
      <div className="text-[14px] text-hig-text">{lastLine}</div>
      <div className="mt-1 text-[14px] text-[#3A3A3C]">
        {truncate(a.vermutete_ursache)}
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="text-[13px]" style={{ color: METHOD_COLORS[a.method] }}>
          ● {methodLine}
        </span>
        <span className="text-[14px] font-medium text-hig-accent">Details ›</span>
      </div>
    </Card>
  );
}
