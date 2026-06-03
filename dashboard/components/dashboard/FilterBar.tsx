"use client";

import { useRouter, useSearchParams } from "next/navigation";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PERIODS = [
  { value: "all", label: "Gesamt" },
  { value: "30d", label: "Letzte 30 Tage" },
  { value: "90d", label: "Letzte 90 Tage" },
];
const MIN_COSTS = [
  { value: "0", label: "Alle" },
  { value: "10", label: "≥ 10 €" },
  { value: "50", label: "≥ 50 €" },
  { value: "100", label: "≥ 100 €" },
];
const SORTS = [
  { value: "cost", label: "Kosten hoch→niedrig" },
  { value: "date", label: "Datum neu→alt" },
  { value: "severity", label: "Schweregrad" },
];

export function FilterBar({ sites }: { sites: string[] }) {
  const router = useRouter();
  const params = useSearchParams();

  function update(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value === "all" || value === "0" || (key === "sort" && value === "cost")) {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    router.push(`/?${next.toString()}`);
  }

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      <Select
        value={params.get("site") ?? "all"}
        onValueChange={(v: string | null) => update("site", v ?? "all")}
      >
        <SelectTrigger className="w-[180px] bg-hig-card">
          <SelectValue placeholder="Standort" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Alle Standorte</SelectItem>
          {sites.map((s) => (
            <SelectItem key={s} value={s}>
              {s}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <FilterSelect
        value={params.get("period") ?? "all"}
        options={PERIODS}
        onChange={(v) => update("period", v)}
      />
      <FilterSelect
        value={params.get("min_cost") ?? "0"}
        options={MIN_COSTS}
        onChange={(v) => update("min_cost", v)}
      />
      <FilterSelect
        value={params.get("sort") ?? "cost"}
        options={SORTS}
        onChange={(v) => update("sort", v)}
      />
    </div>
  );
}

function FilterSelect({
  value,
  options,
  onChange,
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <Select
      value={value}
      onValueChange={(v: string | null) => onChange(v ?? options[0].value)}
    >
      <SelectTrigger className="w-[180px] bg-hig-card">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
