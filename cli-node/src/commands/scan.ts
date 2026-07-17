import fs from "node:fs";
import path from "node:path";

import chalk from "chalk";
import yaml from "js-yaml";

/**
 * scopeform scan — free, local shadow-agent / raw-credential detector.
 *
 * Runs fully locally: nothing is sent anywhere and no login is required.
 */

export type Finding = {
  file: string;
  line: number;
  kind: string;
  service: string | null;
  risk: "high" | "medium";
  detail: string;
};

// Provider-accurate secret patterns; each maps to the service we can scope.
const SECRET_PATTERNS: Array<[string, string, "high" | "medium", RegExp]> = [
  ["Anthropic API key", "anthropic", "high", /sk-ant-[A-Za-z0-9_-]{20,}/],
  ["OpenAI API key", "openai", "high", /sk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}/],
  ["GitHub token", "github", "high", /(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})/],
  ["Slack token", "slack", "high", /xox[baprs]-[A-Za-z0-9-]{10,}/],
  ["AWS access key", "aws", "high", /AKIA[0-9A-Z]{16}/],
  ["Stripe live key", "stripe", "high", /[sr]k_live_[A-Za-z0-9]{24,}/],
  ["Google API key", "google", "medium", /AIza[0-9A-Za-z_-]{35}/],
];

const ENV_ASSIGNMENT = /^\s*(?<name>[A-Z0-9_]*(?:API_KEY|APIKEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*)\s*=\s*(?<value>[^\s#]{12,})/;

const PLACEHOLDER_HINTS = ["placeholder", "your", "xxx", "changeme", "example", "dummy", "<", "${", "replace", "todo"];

const WORKFLOW_SECRET = /\$\{\{\s*secrets\.(?<name>[A-Za-z0-9_]+)\s*\}\}/g;

const SOURCE_SUFFIXES = new Set([".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"]);
const CONFIG_SUFFIXES = new Set([".json", ".yml", ".yaml", ".toml", ".cfg", ".ini"]);

const SKIP_DIRS = new Set([
  ".git", "node_modules", "dist", "build", "out", ".next", "coverage",
  ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
  ".ruff_cache", "target", "vendor", ".turbo",
]);

const MAX_FILE_BYTES = 1_000_000;

const DEFAULT_ACTIONS: Record<string, string[]> = {
  openai: ["chat.completions"],
  anthropic: ["messages"],
  github: ["repos.read"],
};

function redact(value: string): string {
  return value.length > 8 ? `${value.slice(0, 8)}…` : "…";
}

function looksPlaceholder(value: string): boolean {
  const lowered = value.toLowerCase();
  return PLACEHOLDER_HINTS.some((hint) => lowered.includes(hint));
}

function* iterFiles(root: string): Generator<string> {
  const stack = [root];
  while (stack.length > 0) {
    const dir = stack.pop() as string;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(entry.name)) {
          stack.push(full);
        }
      } else if (entry.isFile()) {
        try {
          if (fs.statSync(full).size <= MAX_FILE_BYTES) {
            yield full;
          }
        } catch {
          // unreadable — skip
        }
      }
    }
  }
}

function scanLineForSecrets(rel: string, lineNo: number, line: string): Finding[] {
  const findings: Finding[] = [];
  for (const [kind, service, risk, pattern] of SECRET_PATTERNS) {
    const match = pattern.exec(line);
    if (match && !looksPlaceholder(match[0])) {
      findings.push({
        file: rel,
        line: lineNo,
        kind,
        service,
        risk,
        detail: `${kind} (${redact(match[0])}) — unscoped, unrevocable, unaudited`,
      });
    }
  }
  return findings;
}

function readLines(file: string): string[] {
  try {
    return fs.readFileSync(file, "utf8").split("\n");
  } catch {
    return [];
  }
}

function scanEnvFile(file: string, rel: string): Finding[] {
  const findings: Finding[] = [];
  readLines(file).forEach((line, idx) => {
    const specific = scanLineForSecrets(rel, idx + 1, line);
    if (specific.length > 0) {
      findings.push(...specific);
      return;
    }
    const match = ENV_ASSIGNMENT.exec(line);
    const name = match?.groups?.name;
    const value = match?.groups?.value;
    if (name && value && !looksPlaceholder(value) && name !== "SCOPEFORM_TOKEN") {
      findings.push({
        file: rel,
        line: idx + 1,
        kind: "Credential in .env",
        service: null,
        risk: "medium",
        detail: `${name}=${redact(value)} — long-lived credential in plain text`,
      });
    }
  });
  return findings;
}

function scanTextFile(file: string, rel: string): Finding[] {
  const findings: Finding[] = [];
  readLines(file).forEach((line, idx) => {
    findings.push(...scanLineForSecrets(rel, idx + 1, line));
  });
  return findings;
}

function scanWorkflow(file: string, rel: string): Finding[] {
  const findings: Finding[] = [];
  readLines(file).forEach((line, idx) => {
    for (const match of line.matchAll(WORKFLOW_SECRET)) {
      const name = match.groups?.name;
      if (name && name !== "SCOPEFORM_TOKEN" && name !== "GITHUB_TOKEN") {
        findings.push({
          file: rel,
          line: idx + 1,
          kind: "Secret in CI workflow",
          service: null,
          risk: "medium",
          detail: `secrets.${name} passed directly to a workflow step — prefer a fresh scoped token per run`,
        });
      }
    }
  });
  return findings;
}

export function scanDirectory(root: string): Finding[] {
  const findings: Finding[] = [];
  for (const file of iterFiles(root)) {
    const rel = path.relative(root, file).split(path.sep).join("/");
    const base = path.basename(file);
    const suffix = path.extname(file);

    if (base === "scopeform.yml") {
      continue;
    }
    if (base.startsWith(".env")) {
      findings.push(...scanEnvFile(file, rel));
    } else if (rel.includes(".github/workflows/") && (suffix === ".yml" || suffix === ".yaml")) {
      findings.push(...scanWorkflow(file, rel));
    } else if (SOURCE_SUFFIXES.has(suffix) || CONFIG_SUFFIXES.has(suffix)) {
      findings.push(...scanTextFile(file, rel));
    }
  }
  return findings;
}

export function buildSuggestedConfig(findings: Finding[]): Record<string, unknown> | null {
  const services = [...new Set(findings.map((f) => f.service).filter((s): s is string => !!s && s in DEFAULT_ACTIONS))].sort();
  if (services.length === 0) {
    return null;
  }
  return {
    identity: { name: "my-agent", owner: "you@example.com", environment: "production" },
    ttl: "24h",
    scopes: services.map((service) => ({ service, actions: DEFAULT_ACTIONS[service] })),
  };
}

export async function scanCommand(target: string, options: { json?: string }): Promise<void> {
  const root = path.resolve(target);
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    console.error(chalk.bold.red(`Not a directory: ${root}`));
    process.exitCode = 2;
    return;
  }

  const findings = scanDirectory(root);

  if (options.json) {
    fs.writeFileSync(options.json, JSON.stringify({ root, findings }, null, 2), "utf8");
  }

  if (findings.length === 0) {
    console.log(chalk.green("✓ No raw agent credentials found."));
    console.log("Nothing to fix — or your keys are already behind scoped tokens.");
    return;
  }

  console.log(chalk.bold(`Scopeform Scan — ${findings.length} finding(s)`));
  const sorted = [...findings].sort((a, b) =>
    a.risk === b.risk ? a.file.localeCompare(b.file) || a.line - b.line : a.risk === "high" ? -1 : 1,
  );
  for (const finding of sorted) {
    const risk = finding.risk === "high" ? chalk.red("HIGH") : chalk.yellow("MED ");
    console.log(`${risk}  ${finding.file}:${finding.line}  ${finding.detail}`);
  }

  const suggestion = buildSuggestedConfig(findings);
  if (suggestion) {
    console.log(chalk.bold("\nSuggested scopeform.yml — scoped, short-lived, revocable:"));
    console.log(yaml.dump(suggestion, { sortKeys: false }).trimEnd());
    console.log(`\nRun ${chalk.cyan("scopeform init")} then ${chalk.cyan("scopeform deploy")} to replace these keys with a scoped token.`);
  }

  if (options.json) {
    console.log(`\nReport written to ${chalk.cyan(options.json)}`);
  }

  process.exitCode = 1;
}
