import { Command } from "commander";

import { deployCommand } from "./commands/deploy";
import { initCommand } from "./commands/init";
import { loginCommand } from "./commands/login";
import { logsCommand } from "./commands/logs";
import { revokeCommand } from "./commands/revoke";

const program = new Command();

program
  .name("scopeform")
  .description("Identity and access management for AI agents")
  .version("0.1.0")
  .option("--api-url <url>", "Scopeform API base URL", process.env.SCOPEFORM_API_URL ?? "https://api.scopeform.dev");

program
  .command("login")
  .description("Authenticate via browser login")
  .action(async () => {
    const apiUrl = program.opts<{ apiUrl: string }>().apiUrl;
    await loginCommand(apiUrl);
  });

program
  .command("init")
  .description("Create a scopeform.yml file in the current directory")
  .action(async () => {
    await initCommand();
  });

program
  .command("deploy")
  .description("Register the current project and issue a scoped token")
  .action(async () => {
    const apiUrl = program.opts<{ apiUrl: string }>().apiUrl;
    await deployCommand(apiUrl);
  });

program
  .command("revoke")
  .description("Revoke all active tokens for an agent")
  .argument("<agent-name>")
  .action(async (agentName: string) => {
    const apiUrl = program.opts<{ apiUrl: string }>().apiUrl;
    await revokeCommand(agentName, apiUrl);
  });

program
  .command("logs")
  .description("Show recent logs for an agent")
  .argument("<agent-name>")
  .option("--limit <number>", "Maximum number of log entries to show", (value) => parseInt(value, 10), 20)
  .option("--service <service>", "Filter by service")
  .option("--blocked-only", "Show only blocked calls")
  .action(
    async (
      agentName: string,
      options: { limit: number; service?: string; blockedOnly?: boolean },
    ) => {
      const apiUrl = program.opts<{ apiUrl: string }>().apiUrl;
      await logsCommand(agentName, apiUrl, options);
    },
  );

void program.parseAsync(process.argv);
