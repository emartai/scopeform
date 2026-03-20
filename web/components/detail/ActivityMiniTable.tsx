import Link from "next/link";
import type { Route } from "next";

import { StatusBadge } from "@/components/ui/StatusBadge";
import type { LogEntry } from "@/lib/api";

type ActivityMiniTableProps = {
  agentId: string;
  logs: LogEntry[];
};

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}

export function ActivityMiniTable({ agentId, logs }: ActivityMiniTableProps) {
  return (
    <section className="rounded-[8px] border border-brand-border bg-brand-card px-5 py-4">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">Recent activity</h2>
      <div className="mt-4 overflow-hidden rounded-[8px] border border-brand-border">
        <div className="grid grid-cols-[88px_96px_1fr_82px] border-b border-brand-border bg-brand-card px-4 py-3 text-[11px] font-medium uppercase tracking-[0.04em] text-[#52525b]">
          <span>Time</span>
          <span>Service</span>
          <span>Action</span>
          <span>Status</span>
        </div>
        {logs.length === 0 ? (
          <div className="px-4 py-6 text-[13px] text-[#a1a1aa]">No activity yet.</div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className={`grid grid-cols-[88px_96px_1fr_82px] items-center border-b border-brand-border px-4 py-3 text-[12px] text-[#a1a1aa] last:border-b-0 ${
                log.allowed ? "" : "border-l-2 border-l-[#ef4444] bg-[#1a0505]"
              }`}
            >
              <span className="font-mono text-[#52525b]">{formatTimestamp(log.called_at)}</span>
              <span className="font-mono text-white">{log.service}</span>
              <span className="font-mono">{log.action}</span>
              <div>
                <StatusBadge tone={log.allowed ? "active" : "revoked"} label={log.allowed ? "allowed" : "blocked"} />
              </div>
            </div>
          ))
        )}
      </div>
      <Link
        href={`/dashboard/logs?agent=${agentId}` as Route}
        className="mt-4 inline-flex text-[13px] text-[#a1a1aa] transition-colors hover:text-white"
      >
        View all logs →
      </Link>
    </section>
  );
}
