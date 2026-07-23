import { AdminPage } from "@/components/page";
const rows = [
  {
    name: "Active projects",
    status: "API-backed",
    detail:
      "Project aggregate endpoint recommended for dashboard optimization.",
  },
  {
    name: "Research jobs",
    status: "No selection",
    detail: "Select a project to poll job progress.",
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
