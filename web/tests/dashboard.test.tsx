import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AgentNotFound from "@/app/dashboard/agents/[id]/not-found";
import { AgentsPageClient } from "@/components/dashboard/AgentsPageClient";
import { Logo } from "@/components/brand/Logo";
import { LogRow } from "@/components/logs/LogRow";
import { LogsPageClient } from "@/components/logs/LogsPageClient";
import { RevokeButton } from "@/components/ui/RevokeButton";
import { StatusBadge } from "@/components/ui/StatusBadge";

const listAgentsMock = vi.fn();
const revokeAgentTokensMock = vi.fn();
const getLogsMock = vi.fn();
const replaceMock = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    listAgents: (...args: unknown[]) => listAgentsMock(...args),
    revokeAgentTokens: (...args: unknown[]) => revokeAgentTokensMock(...args),
    getLogs: (...args: unknown[]) => getLogsMock(...args)
  }
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/dashboard/logs",
  useSearchParams: () => new URLSearchParams("range=24h")
}));

describe("dashboard polish", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders status badges with exact design colors", () => {
    render(<StatusBadge tone="active" label="active" withDot />);

    const badge = screen.getByText("active");
    const styles = getComputedStyle(badge);

    expect(styles.backgroundColor).toBe("rgb(5, 46, 22)");
    expect(styles.borderColor).toBe("rgb(22, 101, 52)");
    expect(styles.color).toBe("rgb(34, 197, 94)");
  });

  it("shows confirmation dialog before revoke callback", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(<RevokeButton agentName="crm-agent" onConfirm={onConfirm} />);

    await user.click(screen.getByRole("button", { name: "Revoke" }));
    expect(screen.getByText("Revoke token for crm-agent?")).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Revoke Token" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("applies optimistic revoked state immediately on confirm", async () => {
    const user = userEvent.setup();
    listAgentsMock.mockResolvedValue({
      items: [
        {
          id: "agent-1",
          org_id: "org-1",
          name: "crm-agent",
          owner_email: "ops@example.com",
          environment: "production",
          status: "active",
          scopes: [],
          created_at: "2026-03-20T10:00:00Z",
          updated_at: "2026-03-20T10:00:00Z"
        }
      ],
      total: 1
    });
    revokeAgentTokensMock.mockReturnValue(new Promise(() => {}));

    render(<AgentsPageClient />);

    await screen.findByText("crm-agent");
    await user.click(screen.getByRole("button", { name: "Revoke" }));
    await user.click(screen.getByRole("button", { name: "Revoke Token" }));

    expect(await screen.findByText("revoked")).toBeInTheDocument();
  });

  it("renders the agent detail 404 state", () => {
    render(<AgentNotFound />);

    expect(screen.getByText("Agent not found")).toBeInTheDocument();
    expect(screen.getByText(/does not exist or is not accessible/i)).toBeInTheDocument();
  });

  it("persists logs filter changes into the URL params", async () => {
    const user = userEvent.setup();
    listAgentsMock.mockResolvedValue({
      items: [
        {
          id: "agent-1",
          org_id: "org-1",
          name: "crm-agent",
          owner_email: "ops@example.com",
          environment: "production",
          status: "active",
          scopes: [],
          created_at: "2026-03-20T10:00:00Z",
          updated_at: "2026-03-20T10:00:00Z"
        }
      ],
      total: 1
    });
    getLogsMock.mockResolvedValue({ items: [], total: 0 });

    render(<LogsPageClient />);

    await waitFor(() => expect(listAgentsMock).toHaveBeenCalled());
    await user.selectOptions(screen.getByDisplayValue("All agents"), "agent-1");

    expect(replaceMock).toHaveBeenCalledWith("/dashboard/logs?range=24h&agent=agent-1");
  });

  it("renders blocked log rows with the red tint and left border", () => {
    render(
      <div>
        <LogRow
          agentName="crm-agent"
          log={{
            id: "log-1",
            agent_id: "agent-1",
            token_id: "token-1",
            service: "openai",
            action: "chat.completions",
            allowed: false,
            called_at: "2026-03-20T10:00:00Z"
          }}
        />
      </div>
    );

    const row = screen.getByText("crm-agent").closest("div[data-allowed='false']");
    expect(row).toHaveStyle({ backgroundColor: "#1a0505", borderLeft: "2px solid #ef4444" });
  });

  it("renders logo sizes for sidebar and topbar contexts", () => {
    const { rerender } = render(<Logo size="lg" showWordmark />);

    let svg = document.querySelector("svg");
    expect(svg).toHaveAttribute("width", "40");
    expect(svg).toHaveAttribute("height", "40");

    rerender(<Logo size="md" showWordmark />);
    svg = document.querySelector("svg");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
  });
});
