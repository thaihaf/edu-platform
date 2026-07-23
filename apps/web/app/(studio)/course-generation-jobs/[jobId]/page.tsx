import { AdminPage } from "@/components/page";
import { CourseGenerationDetail } from "@/components/phase10c";
export default async function Page({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return (
    <AdminPage
      title="Course generation"
      description="Polling pauses at terminal states and when the tab is hidden."
    >
      <CourseGenerationDetail jobId={jobId} />
    </AdminPage>
  );
}
