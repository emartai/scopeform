import chalk from "chalk";
import inquirer from "inquirer";

import { ScopeformClient, ScopeformNotFoundError } from "../utils/api-client";
import { findAgentByName, requireLogin } from "./shared";

export async function revokeCommand(agentName: string, apiUrl: string): Promise<void> {
  const config = requireLogin(console);
  const { confirmed } = await inquirer.prompt<{ confirmed: boolean }>([
    {
      type: "confirm",
      name: "confirmed",
      message: `Revoke all tokens for ${agentName}? This cannot be undone. [y/N]`,
      default: false,
    },
  ]);

  if (!confirmed) {
    console.log("Revocation cancelled.");
    return;
  }

  try {
    const client = new ScopeformClient(apiUrl, config.token);
    const agent = await findAgentByName(client, agentName);
    await client.revokeToken({ agent_id: String(agent.id) });
    console.log(chalk.green(`✓ Tokens revoked for ${agentName}. All active sessions terminated.`));
  } catch (error) {
    if (error instanceof ScopeformNotFoundError) {
      console.log(`Agent '${agentName}' not found in your organisation.`);
      throw error;
    }
    throw error;
  }
}
