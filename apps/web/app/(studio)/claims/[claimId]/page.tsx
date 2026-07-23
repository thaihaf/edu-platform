import { AdminPage } from "@/components/page";
import { ClaimDetail } from "@/components/admin-data";
export default async function Page({
  params,
}: {
  params: Promise<{ claimId: string }>;
}) {
  const { claimId } = await params;
  return (
    <AdminPage
      title="Evidence claim"
      description="Confidence and review transitions are calculated and authorized by FastAPI."
    >
      <ClaimDetail claimId={claimId} />
    </AdminPage>
  );
}
