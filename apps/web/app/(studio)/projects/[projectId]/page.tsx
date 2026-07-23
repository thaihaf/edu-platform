import { AdminPage } from "@/components/page";
import { ProjectDetail } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="Project"
      description="API-authoritative project metadata and Phase 10B research administration."
    >
      <ProjectDetail projectId={projectId} />
    </AdminPage>
  );
}
