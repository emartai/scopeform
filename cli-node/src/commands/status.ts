import chalk from "chalk";

import { ScopeformClient, ScopeformNotFoundError } from "../utils/api-client";
import { findAgentByName, requireLogin, requireScopeformYaml } from "./shared";

export async function statusCommand(apiUrl: string): Promise<void> {
  const config = requireLogin(console);
  const scopeformConfig = requireScopeformYaml(console);
  const identity = scopeformConfig.identity as Record<string, string>;
  const agentName = identity.name;

  const client = new ScopeformClient(apiUrl, config.token);

  let agent: Record<string, unknown>;
  try {
    agent = await findAgentByName(client, agentName);
  } catch (error) {
    if (error instanceof ScopeformNotFoundError) {
      console.log(chalk.yellow(`Agent '${agentName}' is not registered yet.`) + ` Run ${chalk.cyan("scopeform deploy")} first.`);
      process.exitCode = 1;
      return;
    }
    throw error;
  }

  const logsResponse = await client.getLogs({ agentId: String(agent.id), limit: 50 });
  const items = Array.isArray(logsResponse.items) ? (logsResponse.items as Array<Record<string, unknown>>) : [];
  const total = items.length;
  const blocked = items.filter((entry) => entry.allowed === false).length;
  const lastCall = items[0]?.called_at;

  const scopes = Array.isArray(agent.scopes) ? (agent.scopes as Array<Record<string, unknown>>) : [];
  const scopeSummary =
    scopes
      .map((scope) => `${String(scope.service)}:${(Array.isArray(scope.actions) ? scope.actions : []).join("|")}`)
      .join(", ") || "(none)";

  console.log(chalk.bold(`Scopeform Status — ${agentName}`));
  console.log(`Status: ${String(agent.status ?? "unknown")}`);
  console.log(`Environment: ${String(agent.environment ?? "unknown")}`);
  console.log(`Owner: ${String(agent.owner_email ?? "unknown")}`);
  console.log(`Scopes: ${scopeSummary}`);
  console.log(`Last seen: ${String(agent.last_seen_at ?? "never")}`);
  console.log(`Recent calls (last 50): ${total}`);
  console.log(`Blocked calls (last 50): ${blocked}`);
  if (lastCall) {
    console.log(`Most recent call: ${String(lastCall)}`);
  }

  if (blocked > 0) {
    console.log(
      chalk.yellow(`${blocked} recent call(s) were blocked.`) +
        ` Run ${chalk.cyan(`scopeform logs ${agentName} --blocked-only`)} to inspect.`,
    );
  }
}
