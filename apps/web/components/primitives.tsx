"use client";
import { useState } from "react";
export function StatusBadge({ value }: { value: string }) {
  return (
    <span
      className="inline-flex rounded-full border border-slate-300 px-2 py-1 text-xs font-semibold"
      aria-label={`Status: ${value}`}
    >
      {value}
    </span>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  const e = error as {
    body?: { error?: { code?: string; trace_id?: string } };
  };
  return (
    <section
      role="alert"
      className="rounded border border-red-300 bg-red-50 p-4"
    >
      <h2 className="font-bold">Unable to load this data</h2>
      <p>
        {error instanceof Error
          ? error.message
          : "An unexpected error occurred."}
      </p>
      <details>
        <summary>Technical details</summary>
        <p>
          Code: {e.body?.error?.code ?? "UNKNOWN"}
          <br />
          Trace ID: {e.body?.error?.trace_id ?? "not supplied"}
        </p>
      </details>
      {retry && (
        <button
          className="mt-2 rounded bg-slate-900 px-3 py-2 text-white"
          onClick={retry}
        >
          Retry
        </button>
      )}
    </section>
  );
}
export function LoadingSkeleton() {
  return (
    <div aria-label="Loading" className="animate-pulse space-y-3">
      <div className="h-8 rounded bg-slate-200" />
      <div className="h-32 rounded bg-slate-200" />
    </div>
  );
}
export function EmptyState({
  title,
  detail,
}: {
  title: string;
  detail: string;
}) {
  return (
    <section className="rounded border border-dashed p-8 text-center">
      <h2 className="font-bold">{title}</h2>
      <p>{detail}</p>
    </section>
  );
}
export function ConfirmButton({
  label,
  onConfirm,
  disabled,
}: {
  label: string;
  onConfirm: () => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open ? (
        <span className="inline-flex gap-2 rounded border p-2">
          <span>Confirm {label}?</span>
          <button
            onClick={() => {
              onConfirm();
              setOpen(false);
            }}
            className="rounded bg-red-700 px-2 text-white"
          >
            Confirm
          </button>
          <button onClick={() => setOpen(false)}>Cancel</button>
        </span>
      ) : (
        <button
          disabled={disabled}
          onClick={() => setOpen(true)}
          className="rounded border px-3 py-2 disabled:opacity-50"
        >
          {label}
        </button>
      )}
    </>
  );
}
export function SafeMarkdown({ children }: { children: string }) {
  return (
    <div className="whitespace-pre-wrap" aria-label="Sanitized text">
      {children}
    </div>
  );
}
