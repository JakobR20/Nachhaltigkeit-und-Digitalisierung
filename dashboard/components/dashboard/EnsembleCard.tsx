"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchEnsembleStats } from "@/lib/api";
import { METHOD_COLORS } from "@/lib/format";

export function EnsembleCard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["ensemble-stats"],
    queryFn: fetchEnsembleStats,
  });

  if (isError) return null;

  return (
    <Card className="mb-4 rounded-xl bg-hig-card shadow-sm">
      <CardContent className="p-5">
        {isLoading ? (
          <div className="space-y-2">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-5 w-full" />
            ))}
          </div>
        ) : (
          <>
            <div className="space-y-1.5">
              {data!.methods.map((m) => (
                <div
                  key={m.method}
                  className="flex items-center gap-2 text-[14px]"
                >
                  <span
                    className="text-lg leading-none"
                    style={{ color: METHOD_COLORS[m.method] ?? "#999" }}
                  >
                    ●
                  </span>
                  <span className="w-40 font-medium text-hig-text">
                    {m.label}
                  </span>
                  <span className="tabular-nums font-semibold text-hig-text">
                    {m.count.toLocaleString("de-DE")} Treffer
                  </span>
                  <span className="text-hig-secondary">({m.description})</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[13px] text-hig-secondary">
              Komplementarität: 4 Methoden, kaum Überlappung — zusammen 4× mehr
              erkannt als eine einzelne.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
