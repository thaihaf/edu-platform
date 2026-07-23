import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Golden dataset"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Golden dataset"
        endpoint="GET /golden-datasets/{dataset_id}"
      />
    </AdminPage>
  );
}
