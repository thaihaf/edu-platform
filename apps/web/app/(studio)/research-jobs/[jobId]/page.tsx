import { AdminPage } from "@/components/page";
import { ResearchDetail } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return (
    <AdminPage
      title="Research job"
      description="Polls a non-terminal job and uses only supported lifecycle actions."
    >
      <ResearchDetail jobId={jobId} />
    </AdminPage>
  );
}
