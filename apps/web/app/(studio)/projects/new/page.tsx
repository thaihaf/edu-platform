"use client";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { api, Project } from "@/api/client";
import { AdminPage } from "@/components/page";
import { ErrorState } from "@/components/primitives";
const schema = z.object({
  title: z.string().min(3),
  description: z.string().min(1),
  domain: z.string().min(1),
  target: z.string().min(1),
  locale: z.string().min(2),
  research_depth: z.coerce.number().min(1).max(10),
});
type Values = z.infer<typeof schema>;
export default function Page() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { locale: "en", research_depth: 3 },
  });
  const m = useMutation({
    mutationFn: (v: Values) =>
      api<Project>("/projects", {
        method: "POST",
        body: {
          ...v,
          workspace_id: "00000000-0000-0000-0000-000000000000",
          created_by: "00000000-0000-0000-0000-000000000001",
        },
      }),
  });
  return (
    <AdminPage
      title="New project"
      description="The API validates the project policy and persists the project."
    >
      <form
        onSubmit={handleSubmit((v) => m.mutate(v))}
        className="max-w-2xl space-y-3 rounded border bg-white p-5"
        aria-label="Project creation wizard"
      >
        <label className="block">
          Title
          <input className="block w-full border" {...register("title")} />
          {errors.title && <span role="alert">{errors.title.message}</span>}
        </label>
        <label className="block">
          Goal / description
          <textarea
            className="block w-full border"
            {...register("description")}
          />
        </label>
        <label className="block">
          Domain
          <input className="block w-full border" {...register("domain")} />
        </label>
        <label className="block">
          Target
          <input className="block w-full border" {...register("target")} />
        </label>
        <label>
          Locale
          <input className="ml-2 border" {...register("locale")} />
        </label>
        <label>
          Research depth
          <input
            type="number"
            className="ml-2 border"
            {...register("research_depth")}
          />
        </label>
        <button
          disabled={m.isPending}
          className="block rounded bg-blue-700 px-4 py-2 text-white"
        >
          {m.isPending ? "Creating…" : "Create project"}
        </button>
        {m.isError && <ErrorState error={m.error} />}{" "}
        {m.data && <p role="status">Project created: {m.data.title}</p>}
      </form>
    </AdminPage>
  );
}
