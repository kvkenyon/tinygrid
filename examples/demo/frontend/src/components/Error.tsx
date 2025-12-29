import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorCardProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorCard({ message = "Something went wrong", onRetry }: ErrorCardProps) {
  return (
    <div className="alert alert-error">
      <AlertTriangle className="h-5 w-5" />
      <span>{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-sm btn-ghost">
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      )}
    </div>
  );
}
