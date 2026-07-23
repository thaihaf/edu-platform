import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Quality-gate policies"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Quality-gate policies"
        endpoint="GET /quality-gate-policies (paginated)"
      />
    </AdminPage>
  );
}
