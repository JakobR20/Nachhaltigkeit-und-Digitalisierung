import { SEVERITY_COLOR } from "@/lib/format";
import type { Severity } from "@/types/anomaly";

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold text-white"
      style={{ backgroundColor: SEVERITY_COLOR[severity] }}
    >
      {severity}
    </span>
  );
}
