import fs from "node:fs";
import path from "node:path";

import axios from "axios";
import MockAdapter from "axios-mock-adapter";

import { deployCommand } from "../src/commands/deploy";
import { logsCommand } from "../src/commands/logs";
import { revokeCommand } from "../src/commands/revoke";

jest.mock("../src/utils/config", () => ({
  loadConfig: jest.fn(() => ({
    token: "user-token",
    email: "user@example.com",
    expires_at: "2099-01-01T00:00:00Z",
  })),
}));

jest.mock("ora", () => () => ({
  start() {
    return this;
  },
  succeed() {
    return this;
  },
  stop() {
    return this;
  },
}));

jest.mock("inquirer", () => ({
  prompt: jest.fn(),
}));

const inquirer = jest.requireMock("inquirer") as { prompt: jest.Mock };

describe("node cli commands", () => {
  let mock: InstanceType<typeof MockAdapter>;
  let cwd: string;
  let consoleLogSpy: jest.SpyInstance;
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    mock = new MockAdapter(axios);
    cwd = fs.mkdtempSync(path.join(process.cwd(), "tmp-scopeform-node-"));
    process.chdir(cwd);
    consoleLogSpy = jest.spyOn(console, "log").mockImplementation(() => undefined);
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    mock.restore();
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    process.chdir(path.resolve(__dirname, ".."));
    fs.rmSync(cwd, { recursive: true, force: true });
  });

  test("deploy writes .env and handles already-registered agent flow", async () => {
    fs.writeFileSync(
      path.join(cwd, "scopeform.yml"),
      [
        "identity:",
        "  name: alpha-agent",
        "  owner: owner@example.com",
        "  environment: production",
        "scopes:",
        "  - service: openai",
        "    actions:",
        "      - chat.completions",
        "ttl: 24h",
        "integrations:",
        "  ci: github-actions",
        "",
      ].join("\n"),
      "utf8",
    );

    mock.onPost("http://localhost:8000/api/v1/agents").reply(409, {
      detail: { detail: "exists" },
    });
    mock.onGet("http://localhost:8000/api/v1/agents").reply(200, {
      items: [{ id: "agent-123", name: "alpha-agent" }],
      total: 1,
    });
    mock.onPost("http://localhost:8000/api/v1/tokens/issue").reply(200, {
      token: "replacement-token",
      jti: "jti-123",
      expires_at: "2026-03-21T12:00:00Z",
    });

    await deployCommand("http://localhost:8000");

    expect(fs.readFileSync(path.join(cwd, ".env"), "utf8")).toContain("SCOPEFORM_TOKEN=replacement-token");
    expect(fs.readFileSync(path.join(cwd, ".gitignore"), "utf8")).toContain(".env");
    expect(consoleLogSpy).toHaveBeenCalledWith("Agent already registered. Issuing new token...");
    expect(consoleLogSpy).toHaveBeenCalledWith("Add SCOPEFORM_API_KEY to your GitHub Actions secrets");
  });

  test("revoke confirms and revokes by agent id", async () => {
    inquirer.prompt.mockResolvedValue({ confirmed: true });
    mock.onGet("http://localhost:8000/api/v1/agents").reply(200, {
      items: [{ id: "agent-123", name: "alpha-agent" }],
      total: 1,
    });
    mock.onPost("http://localhost:8000/api/v1/tokens/revoke").reply((config) => {
      expect(JSON.parse(config.data)).toEqual({ agent_id: "agent-123" });
      return [200, { revoked: true, count: 2 }];
    });

    await revokeCommand("alpha-agent", "http://localhost:8000");

    expect(consoleLogSpy).toHaveBeenCalledWith("✓ Tokens revoked for alpha-agent. All active sessions terminated.");
  });

  test("logs renders entries and uses blocked filter", async () => {
    mock.onGet("http://localhost:8000/api/v1/agents").reply(200, {
      items: [{ id: "agent-123", name: "alpha-agent" }],
      total: 1,
    });
    mock.onGet("http://localhost:8000/api/v1/agents/agent-123/logs").reply((config) => {
      expect(config.params).toEqual({ limit: 20, offset: 0, allowed: "false", service: "openai" });
      return [
        200,
        {
          items: [
            {
              called_at: "2026-03-20T12:00:00Z",
              service: "openai",
              action: "chat.completions",
              allowed: true,
            },
            {
              called_at: "2026-03-20T12:05:00Z",
              service: "openai",
              action: "responses.create",
              allowed: false,
            },
          ],
          total: 2,
        },
      ];
    });

    await logsCommand("alpha-agent", "http://localhost:8000", {
      limit: 20,
      service: "openai",
      blockedOnly: true,
    });

    expect(consoleLogSpy).toHaveBeenCalledWith("Logs for alpha-agent");
  });
});
