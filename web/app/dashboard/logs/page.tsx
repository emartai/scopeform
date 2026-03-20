import { Suspense } from "react";
import type { Metadata } from "next";

import { LogsPageClient } from "@/components/logs/LogsPageClient";

export const metadata: Metadata = {
  title: "Logs - Scopeform"
};

export default function LogsPage() {
  return (
    <Suspense
      fallback={
        <section>
          <h1 className="mb-5 text-[20px] font-semibold text-white">Logs</h1>
        </section>
      }
    >
      <LogsPageClient />
    </Suspense>
  );
}
