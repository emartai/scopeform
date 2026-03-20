import fs from "node:fs";
import path from "node:path";

import chalk from "chalk";
import inquirer from "inquirer";
import yaml from "js-yaml";

const AGENT_NAME_PATTERN = /^[a-zA-Z0-9_-]{1,64}$/;
const TTL_PATTERN = /^\d+[smhd]$/;
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const ENVIRONMENTS = ["production", "staging", "development"] as const;
const CI_OPTIONS = ["github-actions", "none"] as const;
const SERVICE_ACTIONS: Record<string, string[]> = {
  openai: ["chat.completions", "responses.create", "embeddings.create"],
  anthropic: ["messages.create", "messages.stream"],
  github: ["issues.read", "issues.write", "contents.read", "pull_requests.write"],
};

function buildSummary(config: Record<string, unknown>): string[] {
  const identity = config.identity as Record<string, string>;
  const scopes = config.scopes as Array<Record<string, unknown>>;
  const integrations = config.integrations as Record<string, string>;
  return [
    "Scopeform Agent Config",
    `Agent name: ${identity.name}`,
    `Owner email: ${identity.owner}`,
    `Environment: ${identity.environment}`,
    `Services: ${scopes.map((scope) => scope.service).join(", ")}`,
    `TTL: ${String(config.ttl)}`,
    `CI integration: ${integrations.ci}`,
  ];
}

export async function initCommand(): Promise<void> {
  const configPath = path.join(process.cwd(), "scopeform.yml");
  if (fs.existsSync(configPath)) {
    const { overwrite } = await inquirer.prompt<{ overwrite: boolean }>([
      {
        type: "confirm",
        name: "overwrite",
        message: "Overwrite? [y/N]",
        default: false,
      },
    ]);

    if (!overwrite) {
      console.log("Keeping the existing scopeform.yml.");
      return;
    }
  }

  const { agentName } = await inquirer.prompt<{ agentName: string }>([
    {
      type: "input",
      name: "agentName",
      message: "Agent name",
      validate: (value: string) =>
        AGENT_NAME_PATTERN.test(value) || "Agent name must match ^[a-zA-Z0-9_-]{1,64}$.",
    },
  ]);

  const { ownerEmail } = await inquirer.prompt<{ ownerEmail: string }>([
    {
      type: "input",
      name: "ownerEmail",
      message: "Owner email",
      validate: (value: string) => EMAIL_PATTERN.test(value) || "Enter a valid email address.",
    },
  ]);

  const { environment } = await inquirer.prompt<{ environment: string }>([
    {
      type: "list",
      name: "environment",
      message: "Environment",
      choices: ENVIRONMENTS,
      default: "development",
    },
  ]);

  const { services } = await inquirer.prompt<{ services: string[] }>([
    {
      type: "checkbox",
      name: "services",
      message: "Services",
      choices: Object.keys(SERVICE_ACTIONS),
      validate: (value: string[]) => value.length > 0 || "Select at least one service.",
    },
  ]);

  const scopes: Array<{ service: string; actions: string[] }> = [];
  for (const service of services) {
    const { actions } = await inquirer.prompt<{ actions: string[] }>([
      {
        type: "checkbox",
        name: "actions",
        message: `Actions for ${service}`,
        choices: SERVICE_ACTIONS[service],
        validate: (value: string[]) => value.length > 0 || "Select at least one action.",
      },
    ]);
    scopes.push({ service, actions });
  }

  const { ttl } = await inquirer.prompt<{ ttl: string }>([
    {
      type: "input",
      name: "ttl",
      message: "TTL",
      default: "24h",
      validate: (value: string) => TTL_PATTERN.test(value) || "TTL must match ^\\d+[smhd]$.",
    },
  ]);

  const { ci } = await inquirer.prompt<{ ci: string }>([
    {
      type: "list",
      name: "ci",
      message: "CI integration",
      choices: CI_OPTIONS,
      default: "github-actions",
    },
  ]);

  const config = {
    identity: {
      name: agentName,
      owner: ownerEmail,
      environment,
    },
    scopes,
    ttl,
    integrations: {
      ci,
    },
  };

  fs.writeFileSync(configPath, yaml.dump(config, { noRefs: true, sortKeys: false }), "utf8");
  console.log(chalk.green("scopeform.yml created successfully."));
  for (const line of buildSummary(config)) {
    console.log(line);
  }
  console.log("Run `scopeform deploy` to register your agent");
}
