"use client";

import * as Dialog from "@radix-ui/react-dialog";

type RevokeButtonProps = {
  agentName?: string;
  disabled?: boolean;
  onConfirm?: () => Promise<void> | void;
};

export function RevokeButton({ agentName = "this agent", disabled = false, onConfirm }: RevokeButtonProps) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button
          type="button"
          disabled={disabled}
          className="h-7 rounded-[5px] border border-[#7f1d1d] px-[10px] text-[12px] text-[#ef4444] transition-colors hover:border-[#ef4444] hover:bg-[#450a0a] disabled:cursor-not-allowed disabled:border-[#27272a] disabled:text-[#52525b] disabled:hover:bg-transparent"
        >
          Revoke
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/70" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(92vw,420px)] -translate-x-1/2 -translate-y-1/2 rounded-[10px] border border-brand-border bg-brand-card p-6 text-white">
          <Dialog.Title className="text-[15px] font-semibold">
            Revoke token for {agentName}?
          </Dialog.Title>
          <Dialog.Description className="mt-3 text-[13px] text-[#a1a1aa]">
            This will immediately terminate all active sessions for this agent. This cannot be undone.
          </Dialog.Description>
          <div className="mt-6 flex justify-end gap-3">
            <Dialog.Close asChild>
              <button
                type="button"
                className="h-8 rounded-[6px] border border-brand-border px-3 text-[13px] text-[#a1a1aa]"
              >
                Cancel
              </button>
            </Dialog.Close>
            <Dialog.Close asChild>
              <button
                type="button"
                onClick={onConfirm}
                className="h-8 rounded-[6px] border border-[#7f1d1d] bg-[#450a0a] px-3 text-[13px] text-[#ef4444]"
              >
                Revoke Token
              </button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
