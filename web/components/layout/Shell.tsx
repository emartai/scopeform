import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

type ShellProps = {
  children: ReactNode;
};

export function Shell({ children }: ShellProps) {
  return (
    <div className="min-h-screen bg-brand-bg text-white">
      <Sidebar />
      <div className="hidden md:block md:pl-[40px] lg:pl-[240px]">
        <TopBar />
        <main className="px-6 py-6">
          <div className="mx-auto max-w-[1200px]">{children}</div>
        </main>
      </div>
      <div className="flex min-h-screen items-center justify-center px-6 text-center md:hidden">
        <div className="max-w-[320px] rounded-[8px] border border-brand-border bg-brand-card px-6 py-8">
          <p className="text-[20px] font-semibold text-white">Best viewed on desktop</p>
          <p className="mt-2 text-[13px] text-[#a1a1aa]">
            Scopeform&apos;s dashboard is designed for desktop screens in this MVP.
          </p>
        </div>
      </div>
    </div>
  );
}
