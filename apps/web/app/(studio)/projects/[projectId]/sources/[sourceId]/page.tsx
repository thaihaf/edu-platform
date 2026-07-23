import { AdminPage } from "@/components/page";
import { SourceDetail } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ sourceId: string }>;
}) {
  const { sourceId } = await params;
  return (
    <AdminPage
      title="Source"
      description="Safe source metadata and explicitly bounded detail panels."
    >
      <SourceDetail sourceId={sourceId} />
    </AdminPage>
  );
}
