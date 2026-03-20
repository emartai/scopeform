"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";

import { api, type AgentCreatePayload, type ScopeDefinition } from "@/lib/api";

const SERVICES: { id: ScopeDefinition["service"]; label: string; actions: string[] }[] = [
  {
    id: "openai",
    label: "OpenAI",
    actions: ["chat.completions", "embeddings", "images.generations"]
  },
  {
    id: "anthropic",
    label: "Anthropic",
    actions: ["messages"]
  },
  {
    id: "github",
    label: "GitHub",
    actions: ["repos.read", "repos.write", "issues.read", "issues.write", "pulls.read"]
  }
];

type ScopeState = Record<ScopeDefinition["service"], Set<string>>;

const emptyScopes = (): ScopeState => ({
  openai: new Set(),
  anthropic: new Set(),
  github: new Set()
});

type Props = {
  onCreated: (agent: AgentCreatePayload & { id: string }) => void;
};

export function RegisterAgentModal({ onCreated }: Props) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [environment, setEnvironment] = useState<AgentCreatePayload["environment"]>("production");
  const [scopes, setScopes] = useState<ScopeState>(emptyScopes());
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function toggleAction(service: ScopeDefinition["service"], action: string) {
    setScopes((prev) => {
      const next = new Set(prev[service]);
      if (next.has(action)) {
        next.delete(action);
      } else {
        next.add(action);
      }
      return { ...prev, [service]: next };
    });
  }

  function buildScopes(): ScopeDefinition[] {
    return SERVICES.filter((s) => scopes[s.id].size > 0).map((s) => ({
      service: s.id,
      actions: Array.from(scopes[s.id])
    }));
  }

  function reset() {
    setName("");
    setOwnerEmail("");
    setEnvironment("production");
    setScopes(emptyScopes());
    setError("");
    setLoading(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const builtScopes = buildScopes();
    if (builtScopes.length === 0) {
      setError("Select at least one action from any service.");
      return;
    }

    setLoading(true);
    try {
      const agent = await api.createAgent({
        name,
        owner_email: ownerEmail,
        environment,
        scopes: builtScopes
      });
      onCreated(agent as AgentCreatePayload & { id: string });
      setOpen(false);
      reset();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to register agent.";
      setError(msg.includes("409") || msg.toLowerCase().includes("conflict")
        ? "An agent with this name already exists."
        : "Failed to register agent. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { setOpen(v); if (!v) reset(); }}>
      <Dialog.Trigger asChild>
        <button className="inline-flex h-8 items-center rounded-[6px] bg-white px-3 text-[13px] font-medium text-brand-bg hover:bg-white/90">
          Register Agent
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(95vw,520px)] -translate-x-1/2 -translate-y-1/2 rounded-[10px] border border-brand-border bg-brand-card p-6 text-white">
          <Dialog.Title className="text-[15px] font-semibold">Register Agent</Dialog.Title>
          <Dialog.Description className="mt-1 text-[13px] text-[#a1a1aa]">
            Register a new AI agent and assign it scoped access.
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            {/* Name */}
            <div>
              <label htmlFor="agent-name" className="mb-1 block text-[12px] text-[#a1a1aa]">
                Agent name <span className="text-[#52525b]">(letters, numbers, - _)</span>
              </label>
              <input
                id="agent-name"
                name="agent-name"
                type="text"
                required
                pattern="^[a-zA-Z0-9_-]{1,64}$"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="support-agent"
                className="h-9 w-full rounded-[6px] border border-brand-border bg-[#111] px-3 text-[13px] text-white placeholder:text-[#52525b] focus:outline-none focus:ring-1 focus:ring-brand-green"
              />
            </div>

            {/* Owner email */}
            <div>
              <label htmlFor="owner-email" className="mb-1 block text-[12px] text-[#a1a1aa]">Owner email</label>
              <input
                id="owner-email"
                name="owner-email"
                type="email"
                required
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
                placeholder="owner@example.com"
                className="h-9 w-full rounded-[6px] border border-brand-border bg-[#111] px-3 text-[13px] text-white placeholder:text-[#52525b] focus:outline-none focus:ring-1 focus:ring-brand-green"
              />
            </div>

            {/* Environment */}
            <div>
              <label htmlFor="environment" className="mb-1 block text-[12px] text-[#a1a1aa]">Environment</label>
              <select
                id="environment"
                name="environment"
                value={environment}
                onChange={(e) => setEnvironment(e.target.value as AgentCreatePayload["environment"])}
                className="h-9 w-full rounded-[6px] border border-brand-border bg-[#111] px-3 text-[13px] text-white focus:outline-none focus:ring-1 focus:ring-brand-green"
              >
                <option value="production">production</option>
                <option value="staging">staging</option>
                <option value="development">development</option>
              </select>
            </div>

            {/* Scopes */}
            <div>
              <p className="mb-2 text-[12px] text-[#a1a1aa]">Scopes <span className="text-[#52525b]">(select at least one action)</span></p>
              <div className="space-y-3 rounded-[6px] border border-brand-border p-3">
                {SERVICES.map((svc) => (
                  <div key={svc.id}>
                    <p className="mb-1.5 text-[12px] font-medium text-white">{svc.label}</p>
                    <div className="flex flex-wrap gap-2">
                      {svc.actions.map((action) => {
                        const checked = scopes[svc.id].has(action);
                        return (
                          <label
                            key={action}
                            className={`flex cursor-pointer items-center gap-1.5 rounded-[4px] border px-2 py-1 text-[12px] transition-colors ${
                              checked
                                ? "border-brand-green bg-brand-green/10 text-brand-green"
                                : "border-brand-border text-[#a1a1aa] hover:border-white/30"
                            }`}
                          >
                            <input
                              type="checkbox"
                              className="sr-only"
                              checked={checked}
                              onChange={() => toggleAction(svc.id, action)}
                            />
                            {action}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {error && <p className="text-[12px] text-red-400">{error}</p>}

            <div className="flex justify-end gap-3 pt-1">
              <Dialog.Close asChild>
                <button
                  type="button"
                  className="h-8 rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa] hover:text-white"
                >
                  Cancel
                </button>
              </Dialog.Close>
              <button
                type="submit"
                disabled={loading}
                className="h-8 rounded-[6px] bg-white px-4 text-[13px] font-medium text-brand-bg hover:bg-white/90 disabled:opacity-50"
              >
                {loading ? "Registering…" : "Register"}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
