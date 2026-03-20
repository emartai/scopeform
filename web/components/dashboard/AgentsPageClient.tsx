"use client";

import { useEffect, useState } from "react";

import { AgentTable } from "@/components/agents/AgentTable";
import { Toast } from "@/components/ui/Toast";
import { api, type Agent } from "@/lib/api";

type ToastState = {
  message: string;
  tone: "success" | "error";
} | null;

type AgentListItem = Agent & {
  token_expires_at?: string | null;
  last_active_at?: string | null;
  isRevoked?: boolean;
};

export function AgentsPageClient() {
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<ToastState>(null);

  useEffect(() => {
    let cancelled = false;

    const loadAgents = async () => {
      try {
        const response = await api.listAgents();
        if (!cancelled) {
          setAgents(response.items);
        }
      } catch {
        if (!cancelled) {
          setToast({
            message: "Failed to load agents.",
            tone: "error"
          });
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadAgents();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeout = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const handleRevoke = async (agentId: string, agentName: string) => {
    const previousAgents = agents;

    setAgents((currentAgents) =>
      currentAgents.map((agent) =>
        agent.id === agentId ? { ...agent, isRevoked: true } : agent
      )
    );

    try {
      await api.revokeAgentTokens(agentId);
      setToast({
        message: `Token revoked for ${agentName}`,
        tone: "success"
      });
    } catch {
      setAgents(previousAgents);
      setToast({
        message: "Failed to revoke token",
        tone: "error"
      });
    }
  };

  return (
    <section>
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-[20px] font-semibold text-white">Agents</h1>
          <span className="inline-flex h-6 items-center rounded-full bg-[#18181b] px-3 text-[12px] text-[#52525b]">
            {loading ? "Loading..." : `${agents.length} ${agents.length === 1 ? "agent" : "agents"}`}
          </span>
        </div>
        <button className="inline-flex h-8 items-center rounded-[6px] bg-white px-3 text-[13px] font-medium text-brand-bg">
          Register Agent
        </button>
      </div>
      <AgentTable agents={agents} loading={loading} onRevoke={handleRevoke} />
      {toast ? <Toast message={toast.message} tone={toast.tone} /> : null}
    </section>
  );
}
