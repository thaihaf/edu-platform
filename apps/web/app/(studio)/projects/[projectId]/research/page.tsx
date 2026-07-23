import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Research jobs"
      description="Research lifecycle records remain API-authoritative."
    >
      <Unavailable
        feature="Project research-job list"
        endpoint="GET /projects/{project_id}/research-jobs (paginated)"
      />
    </AdminPage>
  );
}
