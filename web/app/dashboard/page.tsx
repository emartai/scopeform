import type { Metadata } from "next";

import { AgentsPageClient } from "@/components/dashboard/AgentsPageClient";

export const metadata: Metadata = {
  title: "Agents - Scopeform"
};

export default function DashboardPage() {
  return <AgentsPageClient />;
}
