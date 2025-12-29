import { AlertTriangle, RefreshCw } from "lucide-react";
import { cn } from "../lib/utils";

interface ErrorMessageProps {
  message: string;
  className?: string;
}

export function ErrorMessage({ message, className }: ErrorMessageProps) {
  return (
    <div
      className={cn("border p-4", className)}
      style={{
        backgroundColor: "rgba(255, 71, 87, 0.1)",
        borderColor: "var(--status-danger)",
      }}
    >
      <div className="flex items-center gap-2">
        <AlertTriangle 
          className="h-4 w-4" 
          style={{ color: 'var(--status-danger)' }}
        />
        <p 
          className="text-sm"
          style={{ color: 'var(--status-danger)' }}
        >
          {message}
        </p>
      </div>
    </div>
  );
}

interface ErrorCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorCard({ title = "ERROR", message, onRetry }: ErrorCardProps) {
  return (
    <div
      className="border p-4"
      style={{
        backgroundColor: "rgba(255, 71, 87, 0.05)",
        borderColor: "var(--status-danger)",
      }}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle 
          className="h-5 w-5 flex-shrink-0 mt-0.5" 
          style={{ color: 'var(--status-danger)' }}
        />
        <div className="flex-1">
          <h3 
            className="text-xs font-semibold tracking-wide uppercase"
            style={{ color: 'var(--status-danger)' }}
          >
            {title}
          </h3>
          <p 
            className="mt-1 text-sm"
            style={{ color: 'var(--text-secondary)' }}
          >
            {message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 flex items-center gap-2 text-xs font-medium tracking-wide uppercase transition-colors"
              style={{ color: 'var(--accent-cyan)' }}
            >
              <RefreshCw className="h-3 w-3" />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
