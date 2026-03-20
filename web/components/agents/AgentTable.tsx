"use client";

import { AgentEmptyState } from "@/components/agents/AgentEmptyState";
import { AgentRow } from "@/components/agents/AgentRow";
import { SkeletonRow } from "@/components/ui/SkeletonRow";

type AgentTableProps = {
  agents: Array<{
    id: string;
    name: string;
    owner_email: string;
    environment: string;
    status: string;
    created_at: string;
    updated_at: string;
    token_expires_at?: string | null;
    last_active_at?: string | null;
    isRevoked?: boolean;
  }>;
  loading: boolean;
  onRevoke: (agentId: string, agentName: string) => Promise<void>;
};

const headers = [
  { label: "Agent Name", width: "w-[220px]" },
  { label: "Owner", width: "w-[180px]" },
  { label: "Environment", width: "w-[120px]" },
  { label: "Status", width: "w-[110px]" },
  { label: "Token Expiry", width: "w-[140px]" },
  { label: "Last Active", width: "w-[130px]" },
  { label: "Actions", width: "w-[100px] text-right" }
];

export function AgentTable({ agents, loading, onRevoke }: AgentTableProps) {
  return (
    <div className="overflow-hidden rounded-[8px] border border-brand-border">
      <div className="flex h-9 items-center border-b border-brand-border bg-brand-card text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">
        {headers.map((header) => (
          <div key={header.label} className={`${header.width} px-4`}>
            {header.label}
          </div>
        ))}
      </div>
      {loading ? (
        <>
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </>
      ) : agents.length === 0 ? (
        <AgentEmptyState />
      ) : (
        agents.map((agent, index) => (
          <div key={agent.id} className={index === agents.length - 1 ? "[&>div]:border-b-0" : undefined}>
            <AgentRow agent={agent} onRevoke={onRevoke} />
          </div>
        ))
      )}
    </div>
  );
}
