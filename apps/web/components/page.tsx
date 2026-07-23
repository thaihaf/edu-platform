import { EmptyState, StatusBadge } from "@/components/primitives";
export type Row = { name: string; status: string; detail: string };
export function AdminPage({
  title,
  description,
  rows = [],
  children,
}: {
  title: string;
  description: string;
  rows?: Row[];
  children?: React.ReactNode;
}) {
  return (
    <>
      <header className="mb-6 flex flex-wrap justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="mt-1 text-slate-600">{description}</p>
        </div>
        {children}
      </header>
      {rows.length ? (
        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full text-left">
            <thead className="bg-slate-50">
              <tr>
                <th className="p-3">Name</th>
                <th className="p-3">Status</th>
                <th className="p-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.name} className="border-t">
                  <td className="p-3 font-medium">{r.name}</td>
                  <td className="p-3">
                    <StatusBadge value={r.status} />
                  </td>
                  <td className="p-3">{r.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title={`No ${title.toLowerCase()} yet`}
          detail="Create or select a project to view API-backed records."
        />
      )}
    </>
  );
}
