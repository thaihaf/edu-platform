import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Question review"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Question review"
        endpoint="GET /questions/{question_id} with revisions, provenance and validators"
      />
    </AdminPage>
  );
}
