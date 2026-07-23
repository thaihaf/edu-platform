"use client";
import { AdminPage } from "@/components/page";
import Link from "next/link";
import { Unavailable } from "@/components/admin-data";
export default function Projects() {
  return (
    <AdminPage
      title="Projects"
      description="Create projects through the existing validated wizard; project-list records require a paginated API contract."
    >
      <Link
        href="/projects/new"
        className="rounded bg-blue-700 px-4 py-2 text-white"
      >
        New project
      </Link>
      <Unavailable
        feature="Project list, search, filters, and pagination"
        endpoint="GET /projects (paginated)"
      />
    </AdminPage>
  );
}
