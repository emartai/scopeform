"use client";

import { cn } from "@/lib/utils";

type ToastProps = {
  message: string;
  tone?: "success" | "error";
};

export function Toast({ message, tone = "success" }: ToastProps) {
  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 max-w-[320px] rounded-[8px] border border-brand-border bg-brand-card px-4 py-3 text-[13px] text-[#a1a1aa]",
        tone === "success" ? "border-l-[3px] border-l-brand-green" : "border-l-[3px] border-l-[#ef4444]"
      )}
    >
      {message}
    </div>
  );
}
