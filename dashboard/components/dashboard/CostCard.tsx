import { Card } from "@/components/ui/card";
import { fmtDateTime, fmtEur } from "@/lib/format";
import type { AnomalyDetail } from "@/types/anomaly";

export function CostCard({ detail }: { detail: AnomalyDetail }) {
  const c = detail.cost;
  const { date, time } = fmtDateTime(detail.timestamp);

  let body: React.ReactNode;
  if (c.is_underconsumption) {
    body = (
      <p className="text-[14px] text-hig-text">
        Minderverbrauch {Math.abs(c.diff_kw ?? 0).toFixed(1)} kW unter Erwartung.
        <br />
        Minderverbrauch verursacht keine Mehrkosten. Möglicherweise
        Effizienzgewinn oder Anlagen-Ausfall — siehe KI-Analyse.
      </p>
    );
  } else if (c.is_negative_price) {
    body = (
      <pre className="hig-calc whitespace-pre-wrap rounded-lg bg-[#FAFAFC] p-4 font-mono text-[13.5px] leading-relaxed">
        {`Mehrverbrauch:   ${c.diff_kw?.toFixed(1)} kW über ${c.dauer_h} h = ${c.diff_kwh?.toFixed(1)} kWh
× Spotpreis:     ${c.spotpreis_ct?.toFixed(2)} ct/kWh (negativ — Stromüberschuss)
─────────────────────────────────────────────
= Dieser Vorfall: 0,00 €`}
        {"\n\n"}
        <span className="text-hig-secondary">
          Stromüberschuss — kein Kostenimpact. Der Mehrverbrauch ist trotzdem
          auffällig.
        </span>
      </pre>
    );
  } else {
    body = (
      <pre className="hig-calc whitespace-pre-wrap rounded-lg bg-[#FAFAFC] p-4 font-mono text-[13.5px] leading-relaxed">
        {`Mehrverbrauch:   ${c.diff_kw?.toFixed(1)} kW über ${c.dauer_h} h = ${c.diff_kwh?.toFixed(1)} kWh
× Spotpreis:     ${c.spotpreis_ct?.toFixed(2)} ct/kWh (${date}, ${time} Uhr)
─────────────────────────────────────────────
= Dieser Vorfall: ${fmtEur(c.mehrkosten_eur)}

Falls jährlich vergleichbar:
≈ ${fmtEur(c.jahreskosten_eur)} pro Jahr (365 × ${fmtEur(c.mehrkosten_eur)})`}
      </pre>
    );
  }

  return (
    <Card className="mb-4 rounded-xl bg-hig-card p-5 shadow-sm">
      <h3 className="mb-2 text-[15px] font-semibold text-hig-text">
        Kostenanalyse
      </h3>
      {body}
    </Card>
  );
}
