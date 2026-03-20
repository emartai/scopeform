"use client";

import { useEffect, useMemo, useState } from "react";
import type { Route } from "next";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { LogsFilterBar } from "@/components/logs/LogsFilterBar";
import { LogsTable } from "@/components/logs/LogsTable";
import { Toast } from "@/components/ui/Toast";
import { api, type Agent, type LogEntry } from "@/lib/api";

type RangeValue = "1h" | "6h" | "24h" | "7d";

const PAGE_SIZE = 50;
const rangeMap: Record<RangeValue, number> = {
  "1h": 60 * 60 * 1000,
  "6h": 6 * 60 * 60 * 1000,
  "24h": 24 * 60 * 60 * 1000,
  "7d": 7 * 24 * 60 * 60 * 1000
};

type ToastState = {
  message: string;
  tone: "success" | "error";
} | null;

function parseFilters(searchParams: URLSearchParams) {
  const page = Number(searchParams.get("page") ?? "1");

  return {
    agent: searchParams.get("agent") ?? "",
    status: searchParams.get("status") ?? "",
    service: searchParams.get("service") ?? "",
    range: (searchParams.get("range") as RangeValue | null) ?? "24h",
    page: Number.isFinite(page) && page > 0 ? page : 1
  };
}

function applyDateRange(logs: LogEntry[], range: RangeValue) {
  const cutoff = Date.now() - rangeMap[range];
  return logs.filter((log) => {
    const timestamp = new Date(log.called_at).getTime();
    return !Number.isNaN(timestamp) && timestamp >= cutoff;
  });
}

function formatLastUpdated(seconds: number) {
  if (seconds < 5) {
    return "just now";
  }

  if (seconds < 60) {
    return `${seconds}s ago`;
  }

  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ago`;
}

export function LogsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const filters = useMemo(() => parseFilters(new URLSearchParams(searchParams.toString())), [searchParams]);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<ToastState>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number>(Date.now());
  const [refreshAgeSeconds, setRefreshAgeSeconds] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadData = async () => {
      try {
        const [agentsResponse, logsResponse] = await Promise.all([
          api.listAgents(),
          api.getLogs({
            limit: 500,
            ...(filters.agent ? { agent_id: filters.agent } : {}),
            ...(filters.status ? { allowed: filters.status === "allowed" } : {}),
            ...(filters.service ? { service: filters.service } : {})
          })
        ]);

        if (cancelled) {
          return;
        }

        setAgents(agentsResponse.items);
        setLogs(logsResponse.items);
        setLastUpdatedAt(Date.now());
        setRefreshAgeSeconds(0);
      } catch {
        if (!cancelled) {
          setToast({ message: "Failed to load logs.", tone: "error" });
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadData();
    const refreshInterval = window.setInterval(() => {
      void loadData();
    }, 30000);

    return () => {
      cancelled = true;
      window.clearInterval(refreshInterval);
    };
  }, [filters.agent, filters.service, filters.status]);

  useEffect(() => {
    const ageInterval = window.setInterval(() => {
      setRefreshAgeSeconds(Math.floor((Date.now() - lastUpdatedAt) / 1000));
    }, 1000);

    return () => window.clearInterval(ageInterval);
  }, [lastUpdatedAt]);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeout = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const agentNames = useMemo(
    () =>
      Object.fromEntries(agents.map((agent) => [agent.id, agent.name])),
    [agents]
  );

  const filteredLogs = useMemo(() => applyDateRange(logs, filters.range), [logs, filters.range]);
  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / PAGE_SIZE));
  const currentPage = Math.min(filters.page, totalPages);
  const paginatedLogs = filteredLogs.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const updateSearchParams = (updates: Record<string, string | number | null>) => {
    const nextParams = new URLSearchParams(searchParams.toString());

    Object.entries(updates).forEach(([key, value]) => {
      if (value === null || value === "" || value === 1) {
        nextParams.delete(key);
      } else {
        nextParams.set(key, String(value));
      }
    });

    const query = nextParams.toString();
    router.replace((query ? `${pathname}?${query}` : pathname) as Route);
  };

  const showClear =
    Boolean(filters.agent) || Boolean(filters.status) || Boolean(filters.service) || filters.range !== "24h";

  return (
    <section>
      <h1 className="mb-5 text-[20px] font-semibold text-white">Logs</h1>
      <LogsFilterBar
        agents={agents.map((agent) => ({ id: agent.id, name: agent.name }))}
        filters={filters}
        onFilterChange={(key, value) => updateSearchParams({ [key]: value, page: null })}
        onClear={() => router.replace(pathname as Route)}
        showClear={showClear}
      />
      <LogsTable
        logs={paginatedLogs}
        loading={loading}
        agentNames={agentNames}
        lastUpdatedLabel={formatLastUpdated(refreshAgeSeconds)}
      />
      <div className="mt-4 flex items-center justify-end gap-2">
        <button
          type="button"
          disabled={currentPage <= 1}
          onClick={() => updateSearchParams({ page: currentPage - 1 })}
          className="h-8 rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white disabled:cursor-not-allowed disabled:text-[#52525b] disabled:hover:bg-transparent"
        >
          Prev
        </button>
        <span className="text-[12px] text-[#52525b]">
          Page {currentPage} of {totalPages}
        </span>
        <button
          type="button"
          disabled={currentPage >= totalPages}
          onClick={() => updateSearchParams({ page: currentPage + 1 })}
          className="h-8 rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa] transition-colors hover:bg-brand-elevated hover:text-white disabled:cursor-not-allowed disabled:text-[#52525b] disabled:hover:bg-transparent"
        >
          Next
        </button>
      </div>
      {toast ? <Toast message={toast.message} tone={toast.tone} /> : null}
    </section>
  );
}
