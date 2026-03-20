"use client";

import { LogRow } from "@/components/logs/LogRow";
import { SkeletonRow } from "@/components/ui/SkeletonRow";
import type { LogEntry } from "@/lib/api";

type LogsTableProps = {
  logs: LogEntry[];
  loading: boolean;
  agentNames: Record<string, string>;
  lastUpdatedLabel: string;
};

const headers = [
  { label: "Timestamp", width: "w-[180px]" },
  { label: "Agent", width: "w-[180px]" },
  { label: "Service / Action", width: "w-[220px]" },
  { label: "Status", width: "w-[100px]" }
];

export function LogsTable({ logs, loading, agentNames, lastUpdatedLabel }: LogsTableProps) {
  return (
    <div className="rounded-[8px] border border-brand-border">
      <div className="flex items-center justify-between border-b border-brand-border px-4 py-3">
        <div className="flex text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">
          {headers.map((header) => (
            <div key={header.label} className={`${header.width} px-4`}>
              {header.label}
            </div>
          ))}
        </div>
        <div className="text-[12px] text-[#52525b]">Last updated: {lastUpdatedLabel}</div>
      </div>
      {loading ? (
        <>
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </>
      ) : logs.length === 0 ? (
        <div className="px-6 py-12 text-[13px] text-[#a1a1aa]">
          No logs yet. Logs appear here once your agents start making calls.
        </div>
      ) : (
        logs.map((log) => <LogRow key={log.id} log={log} agentName={agentNames[log.agent_id] ?? log.agent_id} />)
      )}
    </div>
  );
}
