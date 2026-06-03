import { Suspense } from "react";

import { AnomalyList } from "@/components/dashboard/AnomalyList";
import { EnsembleCard } from "@/components/dashboard/EnsembleCard";
import { FilterBarLoader } from "@/components/dashboard/FilterBarLoader";
import { Header } from "@/components/dashboard/Header";

export default function Home() {
  return (
    <main>
      <Header subtitle="Energie-Anomalien — Kostenpriorisierte Übersicht" />
      <EnsembleCard />
      <Suspense>
        <FilterBarLoader />
        <AnomalyList />
      </Suspense>
    </main>
  );
}
