export type Agent = {
  id: string;
  org_id: string;
  name: string;
  owner_email: string;
  environment: string;
  status: string;
  scopes: Array<{ service: string; actions: string[] }>;
  created_at: string;
  updated_at: string;
};

export type LogEntry = {
  id: string;
  agent_id: string;
  token_id: string;
  service: string;
  action: string;
  allowed: boolean;
  called_at: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/proxy${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type ScopeDefinition = {
  service: "openai" | "anthropic" | "github";
  actions: string[];
};

export type AgentCreatePayload = {
  name: string;
  owner_email: string;
  environment: "production" | "staging" | "development";
  scopes: ScopeDefinition[];
};

export const api = {
  health: () => apiFetch<{ status: string; db: boolean; redis: boolean }>("/health"),
  listAgents: () => apiFetch<{ items: Agent[]; total: number }>("/agents"),
  getAgent: (agentId: string) => apiFetch<Agent>(`/agents/${agentId}`),
  createAgent: (payload: AgentCreatePayload) =>
    apiFetch<Agent>("/agents", { method: "POST", body: JSON.stringify(payload) }),
  revokeAgentTokens: (agentId: string) =>
    apiFetch<{ revoked: boolean; count: number }>("/tokens/revoke", {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId })
    }),
  getAgentLogs: (agentId: string, params?: Record<string, string | number | boolean>) => {
    const search = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([key, value]) => search.set(key, String(value)));
    const suffix = search.toString() ? `?${search.toString()}` : "";
    return apiFetch<{ items: LogEntry[]; total: number }>(`/agents/${agentId}/logs${suffix}`);
  },
  getLogs: (params?: Record<string, string | number | boolean>) => {
    const search = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([key, value]) => search.set(key, String(value)));
    const suffix = search.toString() ? `?${search.toString()}` : "";
    return apiFetch<{ items: LogEntry[]; total: number }>(`/logs${suffix}`);
  }
};
