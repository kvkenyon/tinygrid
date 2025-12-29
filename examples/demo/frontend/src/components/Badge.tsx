import { cn } from "../lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const styles: Record<string, { bg: string; text: string; border: string }> = {
    default: {
      bg: "var(--bg-tertiary)",
      text: "var(--text-secondary)",
      border: "var(--border-secondary)",
    },
    success: {
      bg: "rgba(0, 255, 136, 0.1)",
      text: "var(--status-normal)",
      border: "var(--status-normal)",
    },
    warning: {
      bg: "rgba(255, 217, 61, 0.1)",
      text: "var(--status-warning)",
      border: "var(--status-warning)",
    },
    danger: {
      bg: "rgba(255, 71, 87, 0.1)",
      text: "var(--status-danger)",
      border: "var(--status-danger)",
    },
    info: {
      bg: "rgba(0, 212, 255, 0.1)",
      text: "var(--accent-cyan)",
      border: "var(--accent-cyan)",
    },
  };

  const style = styles[variant];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium tracking-wide uppercase border",
        className
      )}
      style={{
        backgroundColor: style.bg,
        color: style.text,
        borderColor: style.border,
      }}
    >
      {children}
    </span>
  );
}

// Grid condition badge with automatic color selection
export function GridConditionBadge({ condition }: { condition: string }) {
  const getVariant = (cond: string): BadgeProps["variant"] => {
    const normalized = cond.toLowerCase();
    if (normalized === "normal") return "success";
    if (["conservation", "watch", "advisory"].includes(normalized)) return "warning";
    if (["emergency", "eea1", "eea2", "eea3"].includes(normalized)) return "danger";
    return "default";
  };

  const getLabel = (cond: string): string => {
    const labels: Record<string, string> = {
      normal: "NORMAL",
      conservation: "CONSERVATION",
      watch: "WATCH",
      advisory: "ADVISORY",
      emergency: "EMERGENCY",
      eea1: "EEA-1",
      eea2: "EEA-2",
      eea3: "EEA-3",
      unknown: "UNKNOWN",
    };
    return labels[cond.toLowerCase()] || cond.toUpperCase();
  };

  return <Badge variant={getVariant(condition)}>{getLabel(condition)}</Badge>;
}
