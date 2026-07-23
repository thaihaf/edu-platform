import { AdminPage } from "@/components/page";
import { Phase10CUnavailable } from "@/components/phase10c";
export default function Page() {
  return (
    <AdminPage
      title="Lesson editor"
      description="This administrative view does not invent production records or policy outcomes."
    >
      <Phase10CUnavailable
        feature="Lesson editor"
        endpoint="GET /lessons/{lesson_id} with draft block mutations"
      />
    </AdminPage>
  );
}
