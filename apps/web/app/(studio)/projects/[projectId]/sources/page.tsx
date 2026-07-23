import { AdminPage } from "@/components/page";
import { Sources } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="Sources"
      description="Register text sources and inspect source records from FastAPI."
    >
      <Sources projectId={projectId} />
    </AdminPage>
  );
}
