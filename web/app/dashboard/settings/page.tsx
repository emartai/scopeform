import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Settings - Scopeform"
};

export default function SettingsPage() {
  return (
    <section>
      <h1 className="text-[20px] font-semibold text-white">Settings</h1>
      <p className="mt-2 text-[13px] text-[#a1a1aa]">Settings stays as a placeholder in this phase.</p>
    </section>
  );
}
