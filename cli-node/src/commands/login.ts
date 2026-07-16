import chalk from "chalk";
import inquirer from "inquirer";

import { ScopeformClient, ScopeformClientError } from "../utils/api-client";
import { saveConfig } from "../utils/config";

function decodeTokenExpiry(token: string): string {
  const payloadPart = token.split(".")[1];
  if (!payloadPart) {
    throw new Error("Could not parse token expiry from API response.");
  }
  const payload = JSON.parse(Buffer.from(payloadPart, "base64url").toString("utf8")) as { exp?: number };
  if (typeof payload.exp !== "number") {
    throw new Error("Could not parse token expiry from API response.");
  }
  return new Date(payload.exp * 1000).toISOString();
}

export async function loginCommand(apiUrl: string): Promise<void> {
  const { email, password } = await inquirer.prompt([
    {
      type: "input",
      name: "email",
      message: "Email:",
      validate: (v: string) => (v.includes("@") ? true : "Enter a valid email address.")
    },
    {
      type: "password",
      name: "password",
      message: "Password:",
      mask: "*"
    }
  ]);

  try {
    const client = new ScopeformClient(apiUrl);
    const authResponse = await client.login(String(email), String(password));
    const token = String(authResponse.token);
    const userEmail = String(authResponse.email);

    saveConfig({
      token,
      email: userEmail,
      expires_at: decodeTokenExpiry(token),
      // Remember which instance we logged into so later commands target it.
      api_url: apiUrl
    });

    console.log(chalk.green(`✓ Logged in as ${userEmail}`));
  } catch (error) {
    if (error instanceof ScopeformClientError) {
      process.exitCode = 1;
      return;
    }
    console.error(chalk.bold.red((error as Error).message));
    process.exitCode = 1;
  }
}
