import { AdminPage } from "@/components/page";
import { CourseGenerationForm } from "@/components/phase10c";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="New course draft"
      description="Start an API-backed asynchronous course generation job."
    >
      <CourseGenerationForm projectId={projectId} />
    </AdminPage>
  );
}
