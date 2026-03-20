import axios, { AxiosError } from "axios";
import chalk from "chalk";

export class ScopeformClientError extends Error {}
export class ScopeformAuthError extends ScopeformClientError {}
export class ScopeformForbiddenError extends ScopeformClientError {}
export class ScopeformNotFoundError extends ScopeformClientError {}
export class ScopeformConflictError extends ScopeformClientError {}
export class ScopeformAPIError extends ScopeformClientError {}

export class ScopeformClient {
  private readonly baseUrl: string;
  private readonly token?: string;

  constructor(baseUrl: string, token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.token = token;
  }

  private extractDetail(error: AxiosError): string {
    const payload = error.response?.data;
    if (payload && typeof payload === "object") {
      const detail = (payload as { detail?: unknown; title?: unknown }).detail;
      if (detail && typeof detail === "object") {
        const nested = detail as { detail?: unknown; title?: unknown };
        if (typeof nested.detail === "string") return nested.detail;
        if (typeof nested.title === "string") return nested.title;
      }
      if (typeof detail === "string") return detail;
      const title = (payload as { title?: unknown }).title;
      if (typeof title === "string") return title;
    }
    return "Request failed.";
  }

  private handleError(error: unknown): never {
    if (!axios.isAxiosError(error)) {
      throw new ScopeformAPIError("Unexpected API client error.");
    }

    const detail = this.extractDetail(error);
    const status = error.response?.status;
    if (status === 401) {
      console.error(chalk.bold.red(`Authentication failed: ${detail}`));
      throw new ScopeformAuthError(detail);
    }
    if (status === 403) {
      console.error(chalk.bold.red(`Permission denied: ${detail}`));
      throw new ScopeformForbiddenError(detail);
    }
    if (status === 404) {
      console.error(chalk.bold.red(`Not found: ${detail}`));
      throw new ScopeformNotFoundError(detail);
    }
    if (status === 409) {
      console.error(chalk.bold.yellow(`Conflict: ${detail}`));
      throw new ScopeformConflictError(detail);
    }

    console.error(chalk.bold.red(`API request failed (${status ?? "unknown"}): ${detail}`));
    throw new ScopeformAPIError(detail);
  }

  private async request<T>(method: "GET" | "POST", path: string, config?: Record<string, unknown>): Promise<T> {
    try {
      const response = await axios.request<T>({
        method,
        baseURL: this.baseUrl,
        url: path,
        timeout: 30_000,
        headers: {
          "Content-Type": "application/json",
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
        },
        ...config,
      });
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async exchangeAuthToken(clerkSessionToken: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("POST", "/api/v1/auth/token", {
      data: { clerk_session_token: clerkSessionToken },
    });
  }

  async registerAgent(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("POST", "/api/v1/agents", { data: payload });
  }

  async listAgents(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("GET", "/api/v1/agents");
  }

  async getAgent(agentId: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("GET", `/api/v1/agents/${agentId}`);
  }

  async issueToken(agentId: string, ttl: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("POST", "/api/v1/tokens/issue", {
      data: { agent_id: agentId, ttl },
    });
  }

  async revokeToken(params: { jti?: string; agent_id?: string }): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("POST", "/api/v1/tokens/revoke", { data: params });
  }

  async getLogs(params: {
    agentId?: string;
    limit?: number;
    offset?: number;
    allowed?: boolean;
    service?: string;
  }): Promise<Record<string, unknown>> {
    const query: Record<string, string | number> = {
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    };
    if (typeof params.allowed === "boolean") {
      query.allowed = String(params.allowed);
    }
    if (params.service) {
      query.service = params.service;
    }

    return params.agentId
      ? this.request<Record<string, unknown>>("GET", `/api/v1/agents/${params.agentId}/logs`, {
          params: query,
        })
      : this.request<Record<string, unknown>>("GET", "/api/v1/logs", { params: query });
  }
}
