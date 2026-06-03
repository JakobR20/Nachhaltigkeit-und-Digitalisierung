import { Card } from "@/components/ui/card";
import { METHOD_CATEGORY, METHOD_LABELS } from "@/lib/format";
import type { AnomalyDetail } from "@/types/anomaly";

import { SeverityBadge } from "./SeverityBadge";

export function AiCard({ detail }: { detail: AnomalyDetail }) {
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-semibold text-hig-text">KI-Analyse</h3>
        <SeverityBadge severity={detail.schweregrad} />
      </div>
      <h4 className="mt-3 text-[15px] font-medium text-hig-text">
        Vermutete Ursache
      </h4>
      <p className="text-[15px] text-hig-text">{detail.vermutete_ursache}</p>
      <h4 className="mt-3 text-[15px] font-medium text-hig-text">
        Handlungsempfehlungen
      </h4>
      <ol className="ml-5 list-decimal text-[15px] text-hig-text">
        {detail.handlungsempfehlungen.map((e, i) => (
          <li key={i}>{e}</li>
        ))}
      </ol>
    </Card>
  );
}

export function DetectionCard({ detail }: { detail: AnomalyDetail }) {
  const others =
    detail.also_flagged_by.length > 0
      ? detail.also_flagged_by.map((m) => METHOD_LABELS[m] ?? m).join(", ")
      : "keine andere Methode hat geflaggt";
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-2 text-[15px] font-semibold text-hig-text">Erkennung</h3>
      <p className="text-[14px] text-hig-text">
        Primäre Methode: <b>{METHOD_LABELS[detail.method] ?? detail.method}</b>
      </p>
      <p className="text-[14px] text-hig-secondary">
        {METHOD_CATEGORY[detail.method]}
      </p>
      <p className="mt-1 text-[14px] text-hig-text">
        Auch erkannt von: {others}
      </p>
    </Card>
  );
}

export function ConditionsCard({ detail }: { detail: AnomalyDetail }) {
  const k = detail.conditions;
  const feiertag = k.feiertag === "ja" ? "Feiertag" : "kein Feiertag";
  const rows = [
    `Wetter: ${k.temperatur_c ?? "—"} °C · ${k.wetter_beschreibung ?? "—"}`,
    `Wochentag: ${k.wochentag ?? "—"} · ${feiertag}`,
    `Konfidenz der KI-Analyse: ${k.confidence.toFixed(2)}`,
  ];
  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-2 text-[15px] font-semibold text-hig-text">
        Rahmenbedingungen
      </h3>
      {rows.map((r, i) => (
        <p key={i} className="text-[13px] text-hig-secondary">
          {r}
        </p>
      ))}
    </Card>
  );
}
