import http from "node:http";
import { exec } from "node:child_process";

import chalk from "chalk";

import { ScopeformClient, ScopeformClientError } from "../utils/api-client";
import { saveConfig } from "../utils/config";

const CALLBACK_PORT = 9876;
const CALLBACK_URL = `http://localhost:${CALLBACK_PORT}`;
const SIGN_IN_URL = `https://app.scopeform.dev/sign-in?cli=true&callback=${CALLBACK_URL}`;
const LOGIN_TIMEOUT_MS = 120_000;

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

function tryOpenBrowser(url: string): boolean {
  try {
    const command =
      process.platform === "win32"
        ? `cmd /c start "" "${url}"`
        : process.platform === "darwin"
          ? `open "${url}"`
          : `xdg-open "${url}"`;
    exec(command);
    return true;
  } catch {
    return false;
  }
}

export async function loginCommand(apiUrl: string): Promise<void> {
  console.log("Opening browser for authentication...");

  let resolveToken: ((token: string) => void) | null = null;
  const tokenPromise = new Promise<string>((resolve) => {
    resolveToken = resolve;
  });

  const server = http.createServer((req, res) => {
    const url = new URL(req.url ?? "/", CALLBACK_URL);
    const clerkSessionToken =
      url.searchParams.get("clerk_session_token") ??
      url.searchParams.get("session_token") ??
      url.searchParams.get("token");

    if (!clerkSessionToken) {
      res.writeHead(400, { "Content-Type": "text/html; charset=utf-8" });
      res.end("<h1>Missing token</h1><p>You can close this window.</p>");
      return;
    }

    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end("<h1>Login complete</h1><p>You can return to the CLI.</p>");
    resolveToken?.(clerkSessionToken);
    setTimeout(() => server.close(), 0);
  });

  try {
    await new Promise<void>((resolve, reject) => {
      server.once("error", reject);
      server.listen(CALLBACK_PORT, "127.0.0.1", () => resolve());
    });

    if (!tryOpenBrowser(SIGN_IN_URL)) {
      console.log("Could not open your browser automatically.");
      console.log("Open this URL in your browser to continue:");
      console.log(SIGN_IN_URL);
    }

    const clerkSessionToken = await Promise.race<string>([
      tokenPromise,
      new Promise<string>((_, reject) =>
        setTimeout(
          () => reject(new Error("Timed out waiting for authentication callback after 120 seconds.")),
          LOGIN_TIMEOUT_MS,
        ),
      ),
    ]);

    const client = new ScopeformClient(apiUrl);
    const authResponse = await client.exchangeAuthToken(clerkSessionToken);
    const token = String(authResponse.token);
    const email = String(authResponse.email);

    saveConfig({
      token,
      email,
      expires_at: decodeTokenExpiry(token),
    });
    console.log(chalk.green(`✓ Logged in as ${email}`));
  } catch (error) {
    if (error instanceof ScopeformClientError) {
      process.exitCode = 1;
      return;
    }
    console.error(chalk.bold.red((error as Error).message));
    process.exitCode = 1;
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}
