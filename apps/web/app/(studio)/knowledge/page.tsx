import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Knowledge"
      description="Explore reviewed skills, prerequisites, dependents, evidence, and actionable gaps."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
