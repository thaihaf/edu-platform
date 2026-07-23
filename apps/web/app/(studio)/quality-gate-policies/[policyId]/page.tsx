import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Quality-gate policy"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Quality-gate policy"
        endpoint="GET /quality-gate-policies/{policy_id}"
      />
    </AdminPage>
  );
}
