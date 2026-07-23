import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Courses"
      description="Select a project to start generation or manage API-backed course records."
    >
      <Phase10CUnavailable
        feature="Cross-project course list"
        endpoint="GET /courses (paginated)"
      />
    </AdminPage>
  );
}
