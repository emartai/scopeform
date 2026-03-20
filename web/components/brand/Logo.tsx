import { cn } from "@/lib/utils";

type LogoProps = {
  size?: "sm" | "md" | "lg";
  showWordmark?: boolean;
  className?: string;
};

const sizeMap = {
  sm: { icon: 16, text: "text-[14px]" },
  md: { icon: 24, text: "text-[16px]" },
  lg: { icon: 40, text: "text-[22px]" }
};

export function Logo({ size = "md", showWordmark = true, className }: LogoProps) {
  const dimensions = sizeMap[size];

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <svg
        viewBox="0 0 32 32"
        fill="none"
        width={dimensions.icon}
        height={dimensions.icon}
        aria-hidden="true"
      >
        <circle cx="16" cy="16" r="12" stroke="white" strokeWidth="1.5" strokeOpacity="0.45" fill="none" />
        <circle cx="16" cy="16" r="8" stroke="white" strokeWidth="0.75" strokeOpacity="0.2" fill="none" />
        <circle cx="16" cy="16" r="4" fill="#22c55e" />
      </svg>
      {showWordmark ? (
        <span className={cn("font-sans font-semibold lowercase text-white", dimensions.text)}>scopeform</span>
      ) : null}
    </div>
  );
}
