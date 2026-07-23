import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Question-bank version"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Question-bank version"
        endpoint="GET /question-banks/{bank_id}/versions/{version_id}"
      />
    </AdminPage>
  );
}
