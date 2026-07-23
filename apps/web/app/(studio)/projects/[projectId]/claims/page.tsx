import { AdminPage } from "@/components/page";
import { Claims } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="Evidence claims"
      description="Review claims without recreating confidence or policy in the browser."
    >
      <Claims projectId={projectId} />
    </AdminPage>
  );
}
