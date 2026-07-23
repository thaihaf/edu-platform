import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Skills"
      description="Accessible tree and prerequisite data require a dedicated read contract."
    >
      <Unavailable
        feature="Skill tree, flat list, and prerequisites"
        endpoint="GET /projects/{project_id}/skills (paginated/tree)"
      />
    </AdminPage>
  );
}
