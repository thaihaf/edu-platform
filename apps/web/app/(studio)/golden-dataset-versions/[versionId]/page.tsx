import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Golden dataset version"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Golden dataset version"
        endpoint="GET /golden-dataset-versions/{version_id}"
      />
    </AdminPage>
  );
}
