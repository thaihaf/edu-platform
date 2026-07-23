import { AdminPage } from "@/components/page";
import { QuestionGenerationDetail } from "@/components/phase10c";
export default async function Page({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return (
    <AdminPage
      title="Question generation"
      description="Inspect accepted asynchronous question generation work."
    >
      <QuestionGenerationDetail jobId={jobId} />
    </AdminPage>
  );
}
