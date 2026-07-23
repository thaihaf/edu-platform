import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Evaluation"
      description="Evaluation runs and quality decisions are backend-authoritative."
    >
      <Phase10CUnavailable
        feature="Evaluation-run list and start evaluation"
        endpoint="GET/POST /projects/{project_id}/evaluation-runs"
      />
    </AdminPage>
  );
}
