import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Sources"
      description="Register and inspect URL, text, file, snapshot, chunk, lineage, and processing records."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
