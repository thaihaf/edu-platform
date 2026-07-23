import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Source independence clusters"
      description="Lineage certainty is never inferred in the browser."
    >
      <Unavailable
        feature="Source-cluster list and review"
        endpoint="paginated source-independence-cluster reads"
      />
    </AdminPage>
  );
}
