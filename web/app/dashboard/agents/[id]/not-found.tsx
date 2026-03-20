import Link from "next/link";
import type { Route } from "next";

export default function AgentNotFound() {
  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-6 py-10">
      <p className="text-[20px] font-semibold text-white">Agent not found</p>
      <p className="mt-2 text-[13px] text-[#a1a1aa]">
        This agent does not exist or is not accessible within your organisation.
      </p>
      <Link
        href={"/dashboard" as Route}
        className="mt-5 inline-flex h-8 items-center rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white"
      >
        Back to agents
      </Link>
    </section>
  );
}
