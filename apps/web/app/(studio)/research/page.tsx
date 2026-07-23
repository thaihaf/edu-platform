import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
export default function Page() {
  return (
    <AdminPage
      title="Research"
      description="Start, poll, resume, cancel, retry, and inspect queued research jobs and artifacts."
    >
      <StatusBadge value="API is authoritative" />
    </AdminPage>
  );
}
