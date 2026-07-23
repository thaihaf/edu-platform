import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Evaluation"
      description="Inspect deterministic runs, results, gate decisions, datasets, policies, baselines, and regressions."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
