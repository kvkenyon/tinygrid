import { cn } from "../lib/utils";

interface LoadingProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function Loading({ className, size = "md" }: LoadingProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-10 w-10",
  };

  return (
    <div className={cn("flex items-center justify-center", className)}>
      <div
        className={cn("animate-spin", sizeClasses[size])}
        style={{
          border: "2px solid var(--border-secondary)",
          borderTopColor: "var(--accent-cyan)",
          borderRadius: "50%",
        }}
      />
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loading size="lg" />
    </div>
  );
}

export function LoadingPage() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <Loading size="lg" className="mb-4" />
        <p 
          className="text-xs tracking-wide uppercase"
          style={{ color: 'var(--text-muted)' }}
        >
          Loading data...
        </p>
      </div>
    </div>
  );
}
