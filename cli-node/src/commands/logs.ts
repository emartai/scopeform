import chalk from "chalk";

import { ScopeformClient, ScopeformNotFoundError } from "../utils/api-client";
import { findAgentByName, requireLogin } from "./shared";

type LogsOptions = {
  limit?: number;
  service?: string;
  blockedOnly?: boolean;
};

export async function logsCommand(agentName: string, apiUrl: string, options: LogsOptions = {}): Promise<void> {
  const config = requireLogin(console);

  try {
    const client = new ScopeformClient(apiUrl, config.token);
    const agent = await findAgentByName(client, agentName);
    const response = await client.getLogs({
      agentId: String(agent.id),
      limit: options.limit ?? 20,
      service: options.service,
      allowed: options.blockedOnly ? false : undefined,
    });
    const items = Array.isArray(response.items) ? response.items : [];
    if (items.length === 0) {
      console.log(`No logs yet for ${agentName}.`);
      return;
    }

    console.log(`Logs for ${agentName}`);
    console.log("Timestamp | Service | Action | Status");
    for (const entry of items as Array<Record<string, unknown>>) {
      const status = entry.allowed ? chalk.green("✓ allowed") : chalk.red("✗ blocked");
      console.log(`${entry.called_at} | ${entry.service} | ${entry.action} | ${status}`);
    }
  } catch (error) {
    if (error instanceof ScopeformNotFoundError) {
      console.log(`Agent '${agentName}' not found in your organisation.`);
      throw error;
    }
    throw error;
  }
}
