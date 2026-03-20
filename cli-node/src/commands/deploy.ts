import chalk from "chalk";
import ora from "ora";

import { ScopeformClient, ScopeformConflictError, ScopeformNotFoundError } from "../utils/api-client";
import { ensureGitignoreHasEnv, findAgentByName, requireLogin, requireScopeformYaml, writeEnvToken } from "./shared";

function formatExpiry(expiresAt: string): string {
  return new Date(expiresAt).toISOString().replace("T", " ").replace(".000Z", " UTC");
}

export async function deployCommand(apiUrl: string): Promise<void> {
  const config = requireLogin(console);
  const scopeformConfig = requireScopeformYaml(console);
  const identity = scopeformConfig.identity as Record<string, string>;
  const agentPayload = {
    name: identity.name,
    owner_email: identity.owner,
    environment: identity.environment,
    scopes: scopeformConfig.scopes,
  };

  const client = new ScopeformClient(apiUrl, config.token);
  let agent: Record<string, unknown>;

  const registerSpinner = ora("Registering agent...").start();
  try {
    agent = await client.registerAgent(agentPayload);
    registerSpinner.succeed("Registering agent...");
  } catch (error) {
    registerSpinner.stop();
    if (error instanceof ScopeformConflictError) {
      console.log("Agent already registered. Issuing new token...");
      try {
        agent = await findAgentByName(client, identity.name);
      } catch (lookupError) {
        if (lookupError instanceof ScopeformNotFoundError) {
          throw lookupError;
        }
        throw lookupError;
      }
    } else {
      throw error;
    }
  }

  const tokenSpinner = ora("Issuing scoped token...").start();
  const tokenResponse = await client.issueToken(String(agent.id), String(scopeformConfig.ttl));
  tokenSpinner.succeed("Issuing scoped token...");

  writeEnvToken(String(tokenResponse.token));
  ensureGitignoreHasEnv();

  console.log(chalk.green("Deploy successful."));
  console.log("Scopeform Deploy");
  console.log(`Agent: ${identity.name}`);
  console.log(`Environment: ${identity.environment}`);
  console.log(`Token expires: ${formatExpiry(String(tokenResponse.expires_at))}`);
  console.log("Token written to: .env");
  console.log("Token: ****");
  if ((scopeformConfig.integrations as Record<string, string>).ci === "github-actions") {
    console.log("Add SCOPEFORM_API_KEY to your GitHub Actions secrets");
  }
}
