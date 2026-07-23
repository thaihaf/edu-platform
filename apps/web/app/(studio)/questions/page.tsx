import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Question Banks"
      description="Generate, validate, review, revise, and publish evidence-grounded question-bank drafts."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
