import { AlertTriangle, RefreshCw, WifiOff, Lock, Database, Clock, ShieldAlert, ServerCrash } from "lucide-react";
import { Button } from "@/components/ui/button";

type ErrorType =
  | "backend_offline"
  | "auth_error"
  | "no_data"
  | "timeout"
  | "validation"
  | "permission_denied"
  | "server_error"
  | "generic";

interface ErrorStateProps {
  title?: string;
  message?: string;
  errorType?: ErrorType;
  onRetry?: () => void;
  developerDetails?: string; // shown only in development
}

const errorConfig: Record<
  ErrorType,
  { icon: React.ReactNode; defaultTitle: string; defaultMessage: string }
> = {
  backend_offline: {
    icon: <WifiOff className="h-6 w-6 text-error" />,
    defaultTitle: "Backend Offline",
    defaultMessage:
      "Cannot reach the API server. Make sure the backend is running on port 8000.",
  },
  auth_error: {
    icon: <Lock className="h-6 w-6 text-warning" />,
    defaultTitle: "Authentication Error",
    defaultMessage: "Your session may have expired. Please log in again.",
  },
  no_data: {
    icon: <Database className="h-6 w-6 text-muted-foreground" />,
    defaultTitle: "No Data Available",
    defaultMessage:
      "There is no data for this view yet. Try uploading a dataset first.",
  },
  timeout: {
    icon: <Clock className="h-6 w-6 text-warning" />,
    defaultTitle: "API Timeout",
    defaultMessage:
      "The request took too long to complete. The server may be under heavy load.",
  },
  validation: {
    icon: <AlertTriangle className="h-6 w-6 text-warning" />,
    defaultTitle: "Validation Error",
    defaultMessage: "The request was rejected due to invalid parameters.",
  },
  permission_denied: {
    icon: <ShieldAlert className="h-6 w-6 text-error" />,
    defaultTitle: "Permission Denied",
    defaultMessage: "You do not have access to this resource.",
  },
  server_error: {
    icon: <ServerCrash className="h-6 w-6 text-error" />,
    defaultTitle: "Internal Server Error",
    defaultMessage:
      "Something went wrong on the server. The team has been notified.",
  },
  generic: {
    icon: <AlertTriangle className="h-6 w-6 text-error" />,
    defaultTitle: "Failed to Load Data",
    defaultMessage:
      "The backend may be unavailable. Check that the API server is running.",
  },
};

function detectErrorType(error?: unknown): ErrorType {
  if (!error) return "generic";
  const msg = String(error).toLowerCase();
  if (msg.includes("failed to fetch") || msg.includes("network") || msg.includes("econnrefused"))
    return "backend_offline";
  if (msg.includes("401") || msg.includes("unauthorized")) return "auth_error";
  if (msg.includes("403") || msg.includes("forbidden")) return "permission_denied";
  if (msg.includes("timeout") || msg.includes("aborted")) return "timeout";
  if (msg.includes("422") || msg.includes("validation")) return "validation";
  if (msg.includes("500") || msg.includes("server error")) return "server_error";
  if (msg.includes("404") || msg.includes("not found")) return "no_data";
  return "generic";
}

export function ErrorState({
  title,
  message,
  errorType = "generic",
  onRetry,
  developerDetails,
}: ErrorStateProps) {
  const config = errorConfig[errorType];
  const isDev = process.env.NODE_ENV === "development";

  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-error/10 border border-error/20 mb-5">
        {config.icon}
      </div>
      <h3 className="text-base font-semibold text-foreground mb-2">
        {title ?? config.defaultTitle}
      </h3>
      <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
        {message ?? config.defaultMessage}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          className="mt-5 gap-2"
          onClick={onRetry}
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      )}
      {isDev && developerDetails && (
        <details className="mt-4 max-w-md text-left">
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
            Developer Details
          </summary>
          <pre className="mt-2 text-xs bg-surface border border-border/60 rounded-lg p-3 overflow-auto text-error/80 font-mono whitespace-pre-wrap">
            {developerDetails}
          </pre>
        </details>
      )}
    </div>
  );
}

export { detectErrorType };
export type { ErrorType };
