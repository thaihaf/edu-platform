"use client";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import {
  api,
  apiPaths,
  Claim,
  Project,
  ResearchJob,
  Source,
  idempotencyKey,
  ReviewDecision,
} from "@/api/client";
import {
  ConfirmButton,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  SafeMarkdown,
  StatusBadge,
} from "@/components/primitives";

export function Unavailable({
  feature,
  endpoint,
}: {
  feature: string;
  endpoint: string;
}) {
  return (
    <section
      className="rounded border border-amber-300 bg-amber-50 p-5"
      role="status"
    >
      <h2 className="font-bold">{feature} is not available from the API</h2>
      <p className="mt-1">
        This administrator view does not invent production records. A paginated
        read contract is required: <code>{endpoint}</code>.
      </p>
    </section>
  );
}
function State({
  query,
  empty,
  children,
}: {
  query: ReturnType<typeof useQuery>;
  empty: string;
  children: (data: any) => React.ReactNode;
}) {
  if (query.isLoading) return <LoadingSkeleton />;
  if (query.isError)
    return <ErrorState error={query.error} retry={() => query.refetch()} />;
  if (!query.data || (Array.isArray(query.data) && !query.data.length))
    return (
      <EmptyState title={empty} detail="No API-backed records were returned." />
    );
  return <>{children(query.data)}</>;
}
export function ProjectDetail({ projectId }: { projectId: string }) {
  const q = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api<Project>(apiPaths.project(projectId)),
  });
  return (
    <State query={q} empty="Project not found">
      {(p: Project) => (
        <section className="rounded border bg-white p-5">
          <h2 className="text-xl font-bold">{p.title}</h2>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <dt>Domain</dt>
              <dd>{p.domain}</dd>
            </div>
            <div>
              <dt>Target</dt>
              <dd>{p.target}</dd>
            </div>
            <div>
              <dt>Locale</dt>
              <dd>{p.locale}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={p.status} />
              </dd>
            </div>
            <div>
              <dt>Research depth</dt>
              <dd>{p.research_depth}</dd>
            </div>
          </dl>
          <SafeMarkdown>{p.description}</SafeMarkdown>
          <nav
            aria-label="Project administration"
            className="mt-5 flex flex-wrap gap-3"
          >
            {[
              ["Sources", `/projects/${p.id}/sources`],
              ["Research", `/projects/${p.id}/research`],
              ["Claims", `/projects/${p.id}/claims`],
              ["Knowledge gaps", `/projects/${p.id}/knowledge-gaps`],
            ].map(([n, h]) => (
              <Link className="rounded border px-3 py-2" href={h} key={h}>
                {n}
              </Link>
            ))}
          </nav>
          <p className="mt-5 text-sm text-slate-600">
            Course, question-bank, and evaluation administration are reserved
            for Phase 10C.
          </p>
        </section>
      )}
    </State>
  );
}
export function Sources({ projectId }: { projectId: string }) {
  const q = useQuery({
    queryKey: ["sources", projectId],
    queryFn: () => api<Source[]>(apiPaths.sources(projectId)),
  });
  return (
    <>
      <AddSource projectId={projectId} />
      <State query={q} empty="No sources yet">
        {(data: Source[]) => (
          <Table
            headers={["Title", "Type", "Publisher", "Canonical URL", "Updated"]}
          >
            {data.map((s) => (
              <tr key={s.id} className="border-t">
                <td className="p-3">
                  <Link href={`/projects/${projectId}/sources/${s.id}`}>
                    {s.title}
                  </Link>
                </td>
                <td className="p-3">
                  <StatusBadge value={s.source_type} />
                </td>
                <td className="p-3">{s.publisher ?? "—"}</td>
                <td className="p-3 break-all">{s.canonical_url ?? "—"}</td>
                <td className="p-3">
                  {new Date(s.updated_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </State>
    </>
  );
}
function AddSource({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const text = useMutation({
    mutationFn: ({ title, content }: { title: string; content: string }) =>
      api(`/projects/${projectId}/sources/text`, {
        method: "POST",
        body: { title, text: content },
        idempotencyKey: idempotencyKey(),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", projectId] }),
  });
  const url = useMutation({
    mutationFn: ({ title, value }: { title: string; value: string }) =>
      api(`/projects/${projectId}/sources/url`, {
        method: "POST",
        body: { title: title || undefined, url: value },
        idempotencyKey: idempotencyKey(),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources", projectId] }),
  });
  return (
    <section className="mb-5 rounded border bg-white p-4">
      <h2 className="font-bold">Add source</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          text.mutate({
            title: String(f.get("text-title")),
            content: String(f.get("text")),
          });
        }}
      >
        <h3 className="mt-3 font-semibold">Pasted text</h3>
        <label className="block">
          Title
          <input required name="text-title" className="ml-2 border" />
        </label>
        <label className="mt-2 block">
          Text
          <textarea required name="text" className="block w-full border" />
        </label>
        {text.isError && <ErrorState error={text.error} />}
        <button
          disabled={text.isPending}
          className="mt-2 rounded bg-blue-700 px-3 py-2 text-white"
        >
          {text.isPending ? "Submitting…" : "Ingest text"}
        </button>
      </form>
      <form
        className="mt-5"
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          url.mutate({
            title: String(f.get("url-title")),
            value: String(f.get("url")),
          });
        }}
      >
        <h3 className="font-semibold">Register URL</h3>
        <label className="block">
          Title (optional)
          <input name="url-title" className="ml-2 border" />
        </label>
        <label className="mt-2 block">
          URL
          <input required type="url" name="url" className="ml-2 w-2/3 border" />
        </label>
        {url.isError && <ErrorState error={url.error} />}
        <button
          disabled={url.isPending}
          className="mt-2 rounded bg-blue-700 px-3 py-2 text-white"
        >
          {url.isPending ? "Submitting…" : "Register URL"}
        </button>
      </form>
      <p className="mt-2 text-sm">
        File upload is not available because the documented API has no upload
        contract. Browser upload progress is therefore not simulated.
      </p>
    </section>
  );
}
export function SourceDetail({ sourceId }: { sourceId: string }) {
  const q = useQuery({
    queryKey: ["source", sourceId],
    queryFn: () => api<Source>(apiPaths.source(sourceId)),
  });
  return (
    <State query={q} empty="Source not found">
      {(s: Source) => (
        <section className="rounded border bg-white p-5">
          <h2 className="text-xl font-bold">{s.title}</h2>
          <p>
            Type: <StatusBadge value={s.source_type} />
          </p>
          <p className="break-all">
            Canonical URL: {s.canonical_url ?? "Not supplied"}
          </p>
          <SafeMarkdown>{`Publisher: ${s.publisher ?? "Not supplied"}\nSource-supplied content is shown as safe text only.`}</SafeMarkdown>
          <Unavailable
            feature="Snapshots, chunks, fetch history, observations, lineage, and related reported questions"
            endpoint="documented paginated source-detail reads"
          />
        </section>
      )}
    </State>
  );
}
export function ResearchDetail({ jobId }: { jobId: string }) {
  const q = useQuery({
    queryKey: ["research", jobId],
    queryFn: () => api<ResearchJob>(apiPaths.research(jobId)),
    refetchInterval: (data) =>
      ["COMPLETED", "FAILED", "CANCELLED"].includes(
        data.state.data?.status ?? "",
      )
        ? false
        : 5000,
  });
  const qc = useQueryClient();
  const action = useMutation({
    mutationFn: (a: string) =>
      api(`/research-jobs/${jobId}/${a}`, {
        method: "POST",
        idempotencyKey: a === "build-evidence" ? idempotencyKey() : undefined,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["research", jobId] }),
  });
  return (
    <State query={q} empty="Research job not found">
      {(j: ResearchJob) => (
        <section className="rounded border bg-white p-5">
          <h2 className="text-xl font-bold">Research job</h2>
          <p>
            <StatusBadge value={`${j.status} · ${j.current_phase}`} /> Progress:{" "}
            {j.progress_percent}%
          </p>
          <p>
            Queries {j.budgets.queries_used}/{j.budgets.query_budget}; sources{" "}
            {j.budgets.sources_selected}/{j.budgets.source_budget}; model calls{" "}
            {j.budgets.model_calls_used}/{j.budgets.model_call_budget}.
          </p>
          <div className="mt-4 flex gap-2">
            {["cancel", "resume", "retry", "build-evidence"].map((a) => (
              <ConfirmButton
                key={a}
                label={a.replace("-", " ")}
                disabled={action.isPending}
                onConfirm={() => action.mutate(a)}
              />
            ))}
          </div>
          {action.isError && <ErrorState error={action.error} />}
          <Unavailable
            feature="Research artifact history"
            endpoint={`/research-jobs/${jobId}/{brief,queries,sources,observations,coverage,gaps,result}`}
          />
        </section>
      )}
    </State>
  );
}
export function Claims({ projectId }: { projectId: string }) {
  const q = useQuery({
    queryKey: ["claims", projectId],
    queryFn: () => api<Claim[]>(apiPaths.claims(projectId)),
  });
  return (
    <State query={q} empty="No claims yet">
      {(data: Claim[]) => (
        <Table
          headers={["Statement", "Type", "Status", "Review", "Confidence"]}
        >
          {data.map((c) => (
            <tr className="border-t" key={c.id}>
              <td className="p-3">
                <Link href={`/claims/${c.id}`}>{c.normalized_statement}</Link>
              </td>
              <td className="p-3">{c.claim_type}</td>
              <td className="p-3">
                <StatusBadge value={c.status} />
              </td>
              <td className="p-3">{c.review_status}</td>
              <td className="p-3">{Math.round(c.confidence * 100)}%</td>
            </tr>
          ))}
        </Table>
      )}
    </State>
  );
}
export function ClaimDetail({ claimId }: { claimId: string }) {
  const q = useQuery({
    queryKey: ["claim", claimId],
    queryFn: () => api<Claim>(apiPaths.claim(claimId)),
  });
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: ({
      decision,
      reason,
    }: {
      decision: ReviewDecision;
      reason: string;
    }) =>
      api(`/claims/${claimId}/review`, {
        method: "POST",
        body: {
          reviewer_id: "00000000-0000-0000-0000-000000000001",
          decision,
          reason,
        },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claim", claimId] }),
  });
  const reviewForm = useRef<HTMLFormElement>(null);
  return (
    <State query={q} empty="Claim not found">
      {(c: Claim) => (
        <section className="rounded border bg-white p-5">
          <h2 className="text-xl font-bold">{c.normalized_statement}</h2>
          <p>
            <StatusBadge value={c.status} /> {c.claim_type} · {c.review_status}
          </p>
          <h3 className="mt-4 font-bold">Confidence components</h3>
          <ul>
            {Object.entries(c.confidence_components).map(([k, v]) => (
              <li key={k}>
                {k}: {Math.round(v * 100)}%
              </li>
            ))}
          </ul>
          <form
            ref={reviewForm}
            className="mt-4"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              m.mutate({
                decision: String(f.get("decision")) as ReviewDecision,
                reason: String(f.get("reason")),
              });
            }}
          >
            <label>
              Review decision{" "}
              <select name="decision">
                <option>APPROVE</option>
                <option>REJECT</option>
                <option>REQUEST_CHANGES</option>
                <option>MARK_DISPUTED</option>
                <option>MARK_OBSOLETE</option>
              </select>
            </label>
            <label className="block">
              Reason <input name="reason" required className="border" />
            </label>
            <ConfirmButton
              label="submit review"
              disabled={m.isPending}
              onConfirm={() => reviewForm.current?.requestSubmit()}
            />
          </form>
          {m.isError && <ErrorState error={m.error} />}
          <Unavailable
            feature="Evidence, contradictions, source clusters, and history"
            endpoint={`/claims/${claimId}/evidence, /contradictions, and documented history reads`}
          />
        </section>
      )}
    </State>
  );
}
function Table({
  headers,
  children,
}: {
  headers: string[];
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded border bg-white">
      <table className="w-full text-left">
        <thead>
          <tr>
            {headers.map((h) => (
              <th className="p-3" key={h}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
