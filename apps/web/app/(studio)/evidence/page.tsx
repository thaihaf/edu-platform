import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Evidence"
      description="Review claims, evidence links, reported questions, contradictions, confidence, and knowledge gaps."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
