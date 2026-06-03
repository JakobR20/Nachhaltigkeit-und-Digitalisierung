"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchSites } from "@/lib/api";

import { FilterBar } from "./FilterBar";

export function FilterBarLoader() {
  const { data } = useQuery({ queryKey: ["sites"], queryFn: fetchSites });
  const sites = (data ?? [])
    .map((s) => s.site)
    .sort((a, b) => a.localeCompare(b));
  return <FilterBar sites={sites} />;
}
