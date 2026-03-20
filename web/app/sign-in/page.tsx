import { SignIn } from "@clerk/nextjs";
import type { Metadata } from "next";

import { Logo } from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "Sign In - Scopeform"
};

export default function SignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-6">
      <div className="w-full max-w-[380px] rounded-[10px] border border-brand-border bg-brand-card p-8">
        <div className="mb-8 flex justify-center">
          <Logo size="md" showWordmark />
        </div>
        {publishableKey ? (
          <SignIn
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "border-0 bg-transparent p-0 shadow-none",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                socialButtonsBlockButton:
                  "h-10 rounded-[6px] border border-brand-border bg-transparent text-[13px] text-[#a1a1aa]",
                dividerLine: "bg-[#1f1f1f]",
                dividerText: "text-[12px] text-[#52525b]",
                formButtonPrimary:
                  "h-10 rounded-[6px] bg-white text-[13px] font-medium text-brand-bg hover:bg-white/90",
                formFieldInput:
                  "h-10 rounded-[6px] border border-brand-border bg-brand-card text-[13px] text-white",
                footerActionLink: "text-[#a1a1aa]"
              }
            }}
          />
        ) : (
          <div className="space-y-4">
            <p className="text-center text-[13px] text-[#a1a1aa]">
              Clerk is not configured yet. Add <code className="font-mono text-white">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> to enable sign-in.
            </p>
            <div className="rounded-[6px] border border-brand-border bg-brand-subtle px-4 py-3 font-mono text-[12px] text-brand-green">
              NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
