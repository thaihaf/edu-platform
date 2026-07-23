import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Reported question"
      description="Question-bank materialization remains a Phase 10C action."
    >
      <Unavailable
        feature="Reported-question detail and review"
        endpoint="GET /reported-questions/{question_id}"
      />
    </AdminPage>
  );
}
