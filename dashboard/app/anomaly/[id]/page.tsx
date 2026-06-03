import { AnomalyDetailView } from "@/components/dashboard/AnomalyDetailView";

export default async function AnomalyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AnomalyDetailView nr={id} />;
}
