import { AdminPage } from "@/components/page";
import {
  Phase10CUnavailable,
  QuestionGenerationForm,
} from "@/components/phase10c";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="Question banks"
      description="Question-bank records and review status remain FastAPI-authoritative."
    >
      <QuestionGenerationForm projectId={projectId} />
      <Phase10CUnavailable
        feature="Paginated question-bank list and version summaries"
        endpoint="GET /projects/{project_id}/question-banks (paginated)"
      />
    </AdminPage>
  );
}
