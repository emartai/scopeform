import fs from "node:fs";
import path from "node:path";

import { ScopeformClient, ScopeformNotFoundError } from "../utils/api-client";
import { loadConfig } from "../utils/config";

export type ScopeformConfigFile = {
  token: string;
  email: string;
  expires_at?: string;
};

export function requireLogin(logger: Pick<Console, "log">): ScopeformConfigFile {
  const config = loadConfig();
  if (!config) {
    logger.log("Run `scopeform login` first");
    throw new Error("NOT_LOGGED_IN");
  }
  return config;
}

export function requireScopeformYaml(logger: Pick<Console, "log">): Record<string, any> {
  const configPath = path.join(process.cwd(), "scopeform.yml");
  if (!fs.existsSync(configPath)) {
    logger.log("Run `scopeform init` first");
    throw new Error("MISSING_SCOPEFORM_YML");
  }
  return JSON.parse(JSON.stringify(require("js-yaml").load(fs.readFileSync(configPath, "utf8")) ?? {}));
}

export async function findAgentByName(client: ScopeformClient, agentName: string): Promise<Record<string, unknown>> {
  const response = await client.listAgents();
  const items = Array.isArray(response.items) ? response.items : [];
  const agent = items.find(
    (entry): entry is Record<string, unknown> => !!entry && typeof entry === "object" && entry.name === agentName,
  );
  if (!agent) {
    throw new ScopeformNotFoundError(`Agent '${agentName}' not found.`);
  }
  return agent;
}

export function writeEnvToken(token: string): void {
  const envPath = path.join(process.cwd(), ".env");
  const line = `SCOPEFORM_TOKEN=${token}`;
  if (!fs.existsSync(envPath)) {
    fs.writeFileSync(envPath, `${line}\n`, "utf8");
    return;
  }

  const lines = fs.readFileSync(envPath, "utf8").split(/\r?\n/).filter((lineItem) => lineItem.length > 0);
  let replaced = false;
  const updated = lines.map((existing) => {
    if (existing.startsWith("SCOPEFORM_TOKEN=")) {
      replaced = true;
      return line;
    }
    return existing;
  });
  if (!replaced) {
    updated.push(line);
  }
  fs.writeFileSync(envPath, `${updated.join("\n")}\n`, "utf8");
}

export function ensureGitignoreHasEnv(): void {
  const gitignorePath = path.join(process.cwd(), ".gitignore");
  if (!fs.existsSync(gitignorePath)) {
    fs.writeFileSync(gitignorePath, ".env\n", "utf8");
    return;
  }

  const contents = fs.readFileSync(gitignorePath, "utf8");
  const lines = contents.split(/\r?\n/).map((line) => line.trim());
  if (!lines.includes(".env")) {
    fs.writeFileSync(gitignorePath, `${contents.replace(/\s*$/, "")}\n.env\n`, "utf8");
  }
}
