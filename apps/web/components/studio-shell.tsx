"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { config } from "@/lib/config";
const navigation = [
  ["Dashboard", "/dashboard"],
  ["Projects", "/projects"],
  ["Sources", "/sources"],
  ["Research", "/research"],
  ["Evidence", "/evidence"],
  ["Knowledge", "/knowledge"],
  ["Courses", "/courses"],
  ["Question Banks", "/questions"],
  ["Evaluation", "/evaluation"],
  ["Settings", "/settings"],
] as const;
export function StudioShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen md:grid md:grid-cols-[16rem_1fr]">
      <aside className="border-r bg-slate-950 p-4 text-slate-100">
        <Link href="/dashboard" className="text-lg font-bold">
          Research Studio
        </Link>
        <label className="mt-6 block text-sm">
          Workspace
          <select
            aria-label="Workspace"
            className="mt-1 w-full rounded bg-slate-800 p-2"
          >
            <option>Default workspace</option>
          </select>
        </label>
        <label className="mt-3 block text-sm">
          Project
          <select
            aria-label="Project"
            className="mt-1 w-full rounded bg-slate-800 p-2"
          >
            <option>All projects</option>
          </select>
        </label>
        <nav aria-label="Primary" className="mt-6 space-y-1">
          {navigation.map(([name, href]) => (
            <Link
              key={href}
              href={href}
              className={`block rounded px-3 py-2 ${path === href ? "bg-blue-600" : "hover:bg-slate-800"}`}
            >
              {name}
            </Link>
          ))}
        </nav>
      </aside>
      <main>
        <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-white px-6 py-3">
          <div>
            <span className="text-sm text-slate-500">
              Admin /{" "}
              {path.split("/").filter(Boolean).join(" / ") || "Dashboard"}
            </span>
            <button
              className="ml-4 rounded border px-3 py-1"
              aria-label="Open command palette"
              disabled
            >
              Search / command palette
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-slate-100 px-2 py-1 text-xs">
              {config.environment}
            </span>
            <span aria-label="API health unknown" className="text-xs">
              ● API health pending
            </span>
            <Link href="/settings" className="text-sm">
              ⚠ Deferred checks
            </Link>
            <button className="rounded border px-2 py-1">
              Development Admin
            </button>
          </div>
        </header>
        <div className="mx-auto max-w-7xl p-6">{children}</div>
      </main>
    </div>
  );
}
