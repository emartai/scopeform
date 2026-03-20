"use client";

import Link from "next/link";
import type { Route } from "next";

import { RevokeButton } from "@/components/ui/RevokeButton";
import { StatusBadge } from "@/components/ui/StatusBadge";

type AgentRowProps = {
  agent: {
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
  };
  onRevoke: (agentId: string, agentName: string) => Promise<void>;
};

const environmentToneMap = {
  production: "production",
  staging: "staging",
  development: "development"
} as const;

function formatRelativeTime(value?: string | null) {
  if (!value) {
    return { label: "—", urgent: false };
  }

  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) {
    return { label: "—", urgent: false };
  }

  const now = Date.now();
  const diff = timestamp - now;
  const absDiff = Math.abs(diff);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (absDiff < minute) {
    return { label: diff >= 0 ? "in <1m" : "just now", urgent: diff >= 0 };
  }

  const unit =
    absDiff < hour ? "minute" : absDiff < day ? "hour" : "day";
  const unitSize = unit === "minute" ? minute : unit === "hour" ? hour : day;
  const amount = Math.floor(absDiff / unitSize);
  const suffix = amount === 1 ? unit : `${unit}s`;

  return {
    label: diff >= 0 ? `in ${amount} ${suffix}` : `${amount} ${suffix} ago`,
    urgent: diff > 0 && diff <= day
  };
}

export function AgentRow({ agent, onRevoke }: AgentRowProps) {
  const tokenExpiry = formatRelativeTime(agent.token_expires_at);
  const lastActive = formatRelativeTime(agent.last_active_at ?? agent.updated_at);
  const statusTone =
    agent.isRevoked ? "revoked" : ((agent.status as "active" | "suspended" | "decommissioned") ?? "active");
  const statusLabel = agent.isRevoked ? "revoked" : agent.status;
  const revokeDisabled = agent.isRevoked || agent.status === "decommissioned";

  return (
    <div className="group flex min-h-12 items-center border-b border-brand-border text-[13px] text-[#a1a1aa] transition-colors hover:bg-brand-elevated">
      <div className="w-[220px] px-4">
        <Link
          href={`/dashboard/agents/${agent.id}` as Route}
          className="font-mono text-[13px] font-medium text-white"
        >
          {agent.name}
        </Link>
      </div>
      <div className="w-[180px] truncate px-4">{agent.owner_email}</div>
      <div className="w-[120px] px-4">
        <StatusBadge
          tone={environmentToneMap[agent.environment as keyof typeof environmentToneMap] ?? "development"}
          label={agent.environment}
        />
      </div>
      <div className="w-[110px] px-4">
        <StatusBadge tone={statusTone} label={statusLabel} withDot />
      </div>
      <div className={`w-[140px] px-4 ${tokenExpiry.urgent ? "text-[#eab308]" : ""}`}>{tokenExpiry.label}</div>
      <div className="w-[130px] px-4">{lastActive.label}</div>
      <div className="flex w-[100px] justify-end px-4">
        <RevokeButton
          agentName={agent.name}
          disabled={revokeDisabled}
          onConfirm={() => onRevoke(agent.id, agent.name)}
        />
      </div>
    </div>
  );
}
