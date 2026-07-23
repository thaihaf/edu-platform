import { AdminPage } from "@/components/page";
import { StatusBadge } from "@/components/primitives";
import { deferredChecks } from "@/lib/deferred-verification";
export default function Settings() {
  return (
    <AdminPage
      title="Settings"
      description="Authentication is an adapter boundary; FastAPI remains authoritative."
    >
      <section className="rounded border bg-white p-5">
        <h2 className="text-xl font-bold">Deferred verification</h2>
        <p className="mb-3 text-slate-600">
          These checks are documented, not passed.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr>
                <th>Check</th>
                <th>Phase</th>
                <th>Reason</th>
                <th>Command</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {deferredChecks.map((c) => (
                <tr className="border-t" key={c.name}>
                  <td className="p-2">{c.name}</td>
                  <td className="p-2">{c.phase}</td>
                  <td className="p-2">{c.reason}</td>
                  <td className="p-2">
                    <code>{c.command}</code>
                  </td>
                  <td className="p-2">
                    <StatusBadge value={c.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AdminPage>
  );
}
