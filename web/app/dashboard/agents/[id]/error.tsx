"use client";

type AgentDetailErrorProps = {
  error: Error;
  reset: () => void;
};

export default function AgentDetailError({ error, reset }: AgentDetailErrorProps) {
  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-6 py-10">
      <h1 className="text-[20px] font-semibold text-white">Unable to load agent</h1>
      <p className="mt-2 text-[13px] text-[#a1a1aa]">{error.message || "The agent detail view failed to load."}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-5 inline-flex h-8 items-center rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white"
      >
        Retry
      </button>
    </section>
  );
}
