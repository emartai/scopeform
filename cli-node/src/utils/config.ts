import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const CONFIG_PATH = path.join(os.homedir(), ".scopeform", "config.json");

type ScopeformConfig = {
  token: string;
  email: string;
  expires_at?: string;
};

function parseExpiresAt(value: string): Date {
  return new Date(value);
}

export function saveConfig(data: ScopeformConfig): void {
  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  fs.chmodSync(CONFIG_PATH, 0o600);
}

export function loadConfig(): ScopeformConfig | null {
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
