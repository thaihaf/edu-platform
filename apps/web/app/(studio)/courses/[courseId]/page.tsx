import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Course editor"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Course editor"
        endpoint="GET /courses/{course_id} with modules, lessons, citations, validation and versions"
      />
    </AdminPage>
  );
}
