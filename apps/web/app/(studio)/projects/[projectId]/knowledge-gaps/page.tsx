import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Knowledge gaps"
      description="Severity must be expressed in text as well as color."
    >
      <Unavailable
        feature="Knowledge-gap list and resolution"
        endpoint="GET /projects/{project_id}/knowledge-gaps (paginated)"
      />
    </AdminPage>
  );
}
