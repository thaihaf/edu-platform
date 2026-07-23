import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Reported questions"
      description="Reported content must remain distinct from AI-synthesized content."
    >
      <Unavailable
        feature="Reported-question list"
        endpoint="GET /projects/{project_id}/reported-questions (paginated)"
      />
    </AdminPage>
  );
}
