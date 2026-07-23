import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Courses"
      description="Generate cited drafts, edit only drafts, inspect citations, validate, diff, publish, or clone versions."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
