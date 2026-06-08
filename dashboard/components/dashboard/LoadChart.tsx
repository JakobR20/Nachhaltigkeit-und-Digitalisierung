"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AnomalyDetail } from "@/types/anomaly";

export function LoadChart({ detail }: { detail: AnomalyDetail }) {
  const data = detail.load_curve.map((p) => ({
    t: new Date(p.timestamp).getTime(),
    kw: p.value_kw,
    expected: p.expected_kw,
  }));
  const anomalyT = new Date(detail.timestamp).getTime();

  const fmtTick = (t: number) =>
    new Date(t).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });

  return (
    <div>
      <div className="mb-2 flex gap-4 text-[13px] text-hig-secondary">
        <span>
          <span className="mr-1 inline-block h-2 w-3 bg-hig-text align-middle" />
          Last (kW)
        </span>
        <span>
          <span className="mr-1 inline-block h-[2px] w-3 bg-hig-secondary align-middle" />
          Erwartung (Median Vergleichstage)
        </span>
        <span>
          <span className="mr-1 inline-block align-middle text-severity-high">✕</span>
          Anomalie
        </span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="#E5E5EA" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={fmtTick}
            tick={{ fontSize: 12, fill: "#8E8E93" }}
            stroke="#E5E5EA"
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#8E8E93" }}
            stroke="#E5E5EA"
            width={40}
            unit=" kW"
          />
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #E5E5EA",
              fontSize: 13,
            }}
            labelFormatter={(t) =>
              new Date(t).toLocaleString("de-DE", {
                day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
              })
            }
            formatter={(v) => [`${Number(v).toFixed(1)} kW`, "Last"]}
          />
          <Line
            type="monotone"
            dataKey="expected"
            stroke="#8E8E93"
            strokeWidth={1.3}
            strokeDasharray="5 4"
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="kw"
            stroke="#1C1C1E"
            strokeWidth={1}
            dot={false}
            isAnimationActive={false}
          />
          {detail.value_kw !== null && (
            <ReferenceDot
              x={anomalyT}
              y={detail.value_kw}
              r={6}
              fill="#FF3B30"
              stroke="#fff"
              strokeWidth={1.5}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
