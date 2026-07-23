import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Question review queue"
      description="Saved non-secret filters and reviewer decisions need an API-backed paginated queue."
    >
      <Phase10CUnavailable
        feature="Question review queue"
        endpoint="GET /projects/{project_id}/questions?review_status=… (paginated)"
      />
    </AdminPage>
  );
}
