import { AdminPage } from "@/components/page";
const rows = [
  {
    name: "Active projects",
    status: "Not available",
    detail:
      "A paginated project-list or dashboard aggregate endpoint is required; the UI does not count unbounded records.",
  },
  {
    name: "Research jobs and failures",
    status: "Not available",
    detail:
      "Individual job polling is supported after selection; a project/job list is not documented.",
  },
  {
    name: "Sources, claims, gaps, and reported questions",
    status: "Partial API coverage",
    detail:
      "Project source and claim reads exist. Aggregate counts, gaps, and reported-question review lists require read contracts.",
  },
  {
    name: "Deferred infrastructure checks",
    status: "Attention",
    detail: "View documented environment limitations in Settings.",
  },
];
export default function Dashboard() {
  return (
    <AdminPage
      title="Dashboard"
      description="Operational overview assembled from read-only API queries without client-side business logic."
      rows={rows}
    />
  );
}
