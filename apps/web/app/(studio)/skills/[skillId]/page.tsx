import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Skill"
      description="Cycle validation remains an API responsibility."
    >
      <Unavailable
        feature="Skill detail and prerequisite action"
        endpoint="GET /skills/{skill_id}"
      />
    </AdminPage>
  );
}
