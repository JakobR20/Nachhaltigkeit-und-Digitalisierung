"use client";

import { useRouter } from "next/navigation";

import {
  METHOD_LABELS,
  SEVERITY_COLOR,
  fmtDateTime,
  fmtEur,
  segmentDe,
  truncate,
} from "@/lib/format";
import type { AnomalyListItem } from "@/types/anomaly";

export function AnomalyCard({ a }: { a: AnomalyListItem }) {
  const router = useRouter();
  const { date, time } = fmtDateTime(a.timestamp);

  const lastLine =
    a.diff_kw !== null && a.diff_kw >= 0
      ? a.diff_pct !== null
        ? `+${a.diff_pct.toFixed(0)}% (${a.value_kw?.toFixed(1)} statt ${a.expected_kw?.toFixed(1)} kW)`
        : `${a.value_kw?.toFixed(1)} kW`
      : `−${Math.abs(a.diff_kw ?? 0).toFixed(1)} kW unter Erwartung`;

  const open = () => router.push(`/anomaly/${a.nr}`);
  return (
    <div
      role="link"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open();
        }
      }}
      className="mb-2 flex cursor-pointer items-center gap-4 rounded-xl bg-hig-card px-4 py-3 shadow-sm ring-1 ring-black/5 transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-hig-accent"
      style={{ borderLeft: `4px solid ${SEVERITY_COLOR[a.schweregrad]}` }}
    >
      {/* cost */}
      <span className="tabular-nums w-28 shrink-0 text-[22px] font-bold leading-none text-hig-text">
        {fmtEur(a.mehrkosten_eur)}
      </span>
      {/* middle */}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="text-[15px] font-medium text-hig-text">{a.site}</span>
          <span className="text-[12px] text-hig-secondary">
            {segmentDe(a.segment)} · {date}, {time}
          </span>
        </div>
        <div className="truncate text-[13px] text-[#3A3A3C]">
          {lastLine} — {truncate(a.vermutete_ursache, 70)}
        </div>
      </div>
      {/* method + chevron */}
      <span className="shrink-0 text-[12px] text-hig-secondary">
        {METHOD_LABELS[a.method] ?? a.method}
      </span>
      <span className="shrink-0 text-[18px] text-hig-accent">›</span>
    </div>
  );
}
