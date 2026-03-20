import Link from "next/link";
import type { Metadata } from "next";
import type { Route } from "next";
import { notFound } from "next/navigation";

import { ActivityMiniTable } from "@/components/detail/ActivityMiniTable";
import { IdentityCard } from "@/components/detail/IdentityCard";
import { ScopesCard } from "@/components/detail/ScopesCard";
import { TokenCard } from "@/components/detail/TokenCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ApiError, api } from "@/lib/api";

type AgentDetailPageProps = {
  params: {
    id: string;
  };
};

export const metadata: Metadata = {
  title: "Agent Detail - Scopeform"
};

export default async function AgentDetailPage({ params }: AgentDetailPageProps) {
  let agent;

  try {
    agent = await api.getAgent(params.id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }

    throw error;
  }

  const recentLogs = await api
    .getAgentLogs(params.id, { limit: 5 })
    .then((response) => response.items)
    .catch(() => []);

  return (
    <section>
      <Link
        href={"/dashboard" as Route}
        className="text-[13px] text-[#a1a1aa] transition-colors hover:text-white"
      >
        ← Agents
      </Link>
      <div className="mt-3 flex items-center gap-3">
        <h1 className="font-mono text-[24px] text-white">{agent.name}</h1>
        <StatusBadge tone={agent.status as "active" | "suspended" | "decommissioned"} label={agent.status} withDot />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,55%)_minmax(0,45%)]">
        <div className="space-y-5">
          <IdentityCard agent={agent} />
          <ScopesCard scopes={agent.scopes} />
        </div>
        <div className="space-y-5">
          <TokenCard agent={agent} />
          <ActivityMiniTable agentId={agent.id} logs={recentLogs} />
        </div>
      </div>
    </section>
  );
}
