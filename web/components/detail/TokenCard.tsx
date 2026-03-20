"use client";

import { useState } from "react";

import { RevokeButton } from "@/components/ui/RevokeButton";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Toast } from "@/components/ui/Toast";
import { api, type Agent } from "@/lib/api";

type ToastState = {
  message: string;
  tone: "success" | "error";
} | null;

type TokenCardProps = {
  agent: Agent;
};

function getTokenState(agent: Agent) {
  if (agent.status === "decommissioned") {
    return { tone: "revoked" as const, label: "revoked", expiry: "Expired" };
  }

  if (agent.status === "suspended") {
    return { tone: "suspended" as const, label: "suspended", expiry: "Unavailable while suspended" };
  }

  return { tone: "active" as const, label: "active", expiry: "Expiry available after token issuance" };
}

export function TokenCard({ agent }: TokenCardProps) {
  const [revoked, setRevoked] = useState(agent.status === "decommissioned");
  const [toast, setToast] = useState<ToastState>(null);

  const tokenState = revoked
    ? { tone: "revoked" as const, label: "revoked", expiry: "Expired" }
    : getTokenState(agent);

  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-5 py-5">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Current token</h2>
      <div className="mt-4">
        <StatusBadge tone={tokenState.tone} label={tokenState.label} withDot className="h-6 px-3 text-[12px]" />
      </div>
      <p className={`mt-4 text-[13px] ${tokenState.expiry === "Expired" ? "text-[#ef4444]" : "text-[#a1a1aa]"}`}>
        {tokenState.expiry}
      </p>
      <div className="mt-6 [&_button]:h-10 [&_button]:w-full [&_button]:justify-center [&_button]:text-[13px]">
        <RevokeButton
          agentName={agent.name}
          disabled={revoked}
          onConfirm={async () => {
            if (revoked) {
              return;
            }

            setRevoked(true);
            try {
              await api.revokeAgentTokens(agent.id);
              setToast({ message: `Token revoked for ${agent.name}`, tone: "success" });
            } catch {
              setRevoked(false);
              setToast({ message: "Failed to revoke token", tone: "error" });
            }
          }}
        />
      </div>
      {toast ? <Toast message={toast.message} tone={toast.tone} /> : null}
    </section>
  );
}
