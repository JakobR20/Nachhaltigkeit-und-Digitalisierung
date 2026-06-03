export default async function AnomalyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <main>
      <p className="text-hig-secondary">
        Anomalie-Detail {id} — folgt in Phase 4.
      </p>
    </main>
  );
}
