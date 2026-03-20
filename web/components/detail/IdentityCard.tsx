import { CopyButton } from "@/components/detail/CopyButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Agent } from "@/lib/api";

const environmentToneMap = {
  production: "production",
  staging: "staging",
  development: "development"
} as const;

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

type IdentityCardProps = {
  agent: Agent;
};

export function IdentityCard({ agent }: IdentityCardProps) {
  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-5 py-4">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Identity</h2>
      <div className="mt-4 space-y-4">
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Name</span>
          <span className="font-mono text-[13px] text-white">{agent.name}</span>
        </div>
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Owner</span>
          <span className="text-[13px] text-white">{agent.owner_email}</span>
        </div>
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Environment</span>
          <div>
            <StatusBadge
              tone={environmentToneMap[agent.environment as keyof typeof environmentToneMap] ?? "development"}
              label={agent.environment}
            />
          </div>
        </div>
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Status</span>
          <div>
            <StatusBadge tone={agent.status as "active" | "suspended" | "decommissioned"} label={agent.status} withDot />
          </div>
        </div>
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Created</span>
          <span className="text-[13px] text-white">{formatDateTime(agent.created_at)}</span>
        </div>
        <div className="grid grid-cols-[96px_1fr] gap-4">
          <span className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Agent ID</span>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] text-white">{agent.id}</span>
            <CopyButton value={agent.id} />
          </div>
        </div>
      </div>
    </section>
  );
}
