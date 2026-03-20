import { cn } from "@/lib/utils";

type BadgeTone =
  | "active"
  | "suspended"
  | "decommissioned"
  | "revoked"
  | "production"
  | "staging"
  | "development";

const badgeMap: Record<BadgeTone, string> = {
  active: "border-[#166534] bg-[#052e16] text-[#22c55e]",
  suspended: "border-[#854d0e] bg-[#451a03] text-[#eab308]",
  decommissioned: "border-[#27272a] bg-[#18181b] text-[#52525b]",
  revoked: "border-[#7f1d1d] bg-[#450a0a] text-[#ef4444]",
  production: "border-[#1e3a5f] bg-[#0c1a3a] text-[#3b82f6]",
  staging: "border-[#4a1d78] bg-[#2d1b4e] text-[#a855f7]",
  development: "border-[#0d4039] bg-[#042f2e] text-[#14b8a6]"
};

const badgeStyles: Record<BadgeTone, { backgroundColor: string; borderColor: string; color: string }> = {
  active: { backgroundColor: "#052e16", borderColor: "#166534", color: "#22c55e" },
  suspended: { backgroundColor: "#451a03", borderColor: "#854d0e", color: "#eab308" },
  decommissioned: { backgroundColor: "#18181b", borderColor: "#27272a", color: "#52525b" },
  revoked: { backgroundColor: "#450a0a", borderColor: "#7f1d1d", color: "#ef4444" },
  production: { backgroundColor: "#0c1a3a", borderColor: "#1e3a5f", color: "#3b82f6" },
  staging: { backgroundColor: "#2d1b4e", borderColor: "#4a1d78", color: "#a855f7" },
  development: { backgroundColor: "#042f2e", borderColor: "#0d4039", color: "#14b8a6" }
};

type StatusBadgeProps = {
  tone: BadgeTone;
  label: string;
  withDot?: boolean;
  className?: string;
};

export function StatusBadge({ tone, label, withDot = false, className }: StatusBadgeProps) {
  return (
    <span
      data-tone={tone}
      className={cn(
        "inline-flex h-5 items-center rounded-[4px] border px-2 text-[11px] font-medium",
        badgeMap[tone],
        className
      )}
      style={badgeStyles[tone]}
    >
      {withDot ? <span className="mr-[5px] h-[5px] w-[5px] rounded-full bg-current" /> : null}
      {label}
    </span>
  );
}
