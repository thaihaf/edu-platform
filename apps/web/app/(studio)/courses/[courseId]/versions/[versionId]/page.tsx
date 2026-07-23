import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Course version"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Course version"
        endpoint="GET /courses/{course_id}/versions/{version_id}"
      />
    </AdminPage>
  );
}
