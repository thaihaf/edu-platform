import { AdminPage } from "@/components/page";
import { Unavailable } from "@/components/admin-data";
export default function Page() {
  return (
    <AdminPage
      title="Source cluster"
      description="Canonical-source decisions require the evidence API."
    >
      <Unavailable
        feature="Source-cluster detail"
        endpoint="GET /source-clusters/{cluster_id}"
      />
    </AdminPage>
  );
}
