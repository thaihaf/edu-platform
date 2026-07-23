"use client";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AdminPage } from "@/components/page";
import { idempotencyKey } from "@/api/client";
const schema = z.object({
  title: z.string().min(3),
  description: z.string().min(1),
  locale: z.string().min(2),
  researchDepth: z.coerce.number().min(1).max(10),
});
type Values = z.infer<typeof schema>;
export default function Projects() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { locale: "en", researchDepth: 3 },
  });
  const submit = async (values: Values) => {
    sessionStorage.setItem("project-wizard-draft", JSON.stringify(values));
    console.info(
      "Project creation must be submitted to API with key",
      idempotencyKey(),
    );
  };
  return (
    <AdminPage
      title="Projects"
      description="Create projects through a resumable seven-step workflow; the API validates and owns project policy."
    >
      <form
        onSubmit={handleSubmit(submit)}
        className="max-w-2xl space-y-4 rounded border bg-white p-5"
        aria-label="Project creation wizard"
      >
        <h2 className="text-xl font-bold">1. Goal</h2>
        <label className="block">
          Title
          <input
            className="mt-1 w-full rounded border p-2"
            {...register("title")}
          />
          {errors.title && <span role="alert">{errors.title.message}</span>}
        </label>
        <label className="block">
          Description
          <textarea
            className="mt-1 w-full rounded border p-2"
            {...register("description")}
          />
          {errors.description && (
            <span role="alert">{errors.description.message}</span>
          )}
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label>
            Locale
            <input
              className="mt-1 w-full rounded border p-2"
              {...register("locale")}
            />
          </label>
          <label>
            Research depth
            <input
              type="number"
              className="mt-1 w-full rounded border p-2"
              {...register("researchDepth")}
            />
          </label>
        </div>
        <p className="text-sm text-amber-800">
          Higher depth can use more source and model budget. Credentials are
          never stored in this draft.
        </p>
        <button
          disabled={isSubmitting}
          className="rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-50"
        >
          Save draft and continue
        </button>
      </form>
    </AdminPage>
  );
}
