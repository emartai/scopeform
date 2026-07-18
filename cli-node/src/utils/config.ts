import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const CONFIG_PATH = path.join(os.homedir(), ".scopeform", "config.json");

// Scopeform is local-first: the CLI targets your own instance by default.
export const DEFAULT_API_URL = "http://localhost:8000";

type ScopeformConfig = {
  token: string;
  email: string;
  expires_at?: string;
  api_url?: string;
};

/**
 * Resolve the API base URL: --api-url flag > SCOPEFORM_API_URL env >
 * api_url saved at login > local default.
 */
export function resolveApiUrl(flagValue?: string): string {
  if (flagValue) {
    return flagValue;
  }
  const envUrl = process.env.SCOPEFORM_API_URL;
  if (envUrl) {
    return envUrl;
  }
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const saved = (JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8")) as ScopeformConfig).api_url;
      if (saved) {
        return saved;
      }
    }
  } catch {
    // fall through to default
  }
  return DEFAULT_API_URL;
}

function parseExpiresAt(value: string): Date {
  return new Date(value);
}

export function saveConfig(data: ScopeformConfig): void {
  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  fs.chmodSync(CONFIG_PATH, 0o600);
}

export function loadConfig(): ScopeformConfig | null {
  const envToken = process.env.SCOPEFORM_TOKEN;
  if (envToken) {
    return { token: envToken, email: "ci" };
  }

  if (!fs.existsSync(CONFIG_PATH)) {
    return null;
  }

  const data = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8")) as ScopeformConfig;
  if (!data.expires_at) {
    return data;
  }

  if (parseExpiresAt(data.expires_at).getTime() <= Date.now()) {
    clearConfig();
    return null;
  }

  return data;
}

export function clearConfig(): void {
  if (fs.existsSync(CONFIG_PATH)) {
    fs.unlinkSync(CONFIG_PATH);
  }
}
