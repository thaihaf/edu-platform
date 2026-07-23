import { AdminPage } from "@/components/page";
import {
  CourseGenerationForm,
  Phase10CUnavailable,
} from "@/components/phase10c";
export default async function Page({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <AdminPage
      title="Courses"
      description="Course records remain FastAPI-authoritative."
    >
      <CourseGenerationForm projectId={projectId} />
      <Phase10CUnavailable
        feature="Paginated course list, curriculum review, and version summaries"
        endpoint="GET /projects/{project_id}/courses (paginated)"
      />
    </AdminPage>
  );
}
