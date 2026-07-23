import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Evaluation baselines"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Evaluation baselines"
        endpoint="GET /evaluation-baselines (paginated)"
      />
    </AdminPage>
  );
}
