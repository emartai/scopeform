import type { LogEntry } from "@/lib/api";

type LogRowProps = {
  log: LogEntry;
  agentName: string;
};

function formatTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  }).format(date);
}

export function LogRow({ log, agentName }: LogRowProps) {
  const blockedStyles = log.allowed
    ? undefined
    : {
        backgroundColor: "#1a0505",
        borderLeft: "2px solid #ef4444"
      };

  return (
    <div
      data-allowed={String(log.allowed)}
      className={`flex min-h-12 items-center border-b border-brand-border px-4 text-[13px] text-[#a1a1aa] last:border-b-0 ${
        log.allowed ? "hover:bg-brand-elevated" : "border-l-2 border-l-[#ef4444] bg-[#1a0505]"
      }`}
      style={blockedStyles}
    >
      <div className="w-[180px] px-4 font-mono text-[12px] text-[#52525b]" title={log.called_at}>
        {formatTimestamp(log.called_at)}
      </div>
      <div className="w-[180px] px-4 font-mono text-[13px] text-white">{agentName}</div>
      <div className="w-[220px] px-4 font-mono text-[12px] text-[#a1a1aa]">
        {log.service}/{log.action}
      </div>
      <div className={`w-[100px] px-4 font-medium ${log.allowed ? "text-brand-green" : "text-[#ef4444]"}`}>
        {log.allowed ? "✓ Allowed" : "✕ Blocked"}
      </div>
    </div>
  );
}
