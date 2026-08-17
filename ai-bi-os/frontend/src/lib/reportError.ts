import { BASE_URL } from "@/lib/api";

/**
 * Tells the server when something broke in the browser.
 *
 * No SDK: a client error tracker would add tens of kilobytes to every visit,
 * and the person paying that cost is the visitor while the benefit is entirely
 * the maintainer's. This is a fetch and a few fields.
 *
 * What it gives up in exchange is readable stack traces - the frames name
 * minified chunks. The message and the path are usually enough to find the
 * component, and when they are not, the answer is to reproduce it rather than
 * to have shipped a bundle to everyone on the chance it might one day help.
 */

/** Reports are deduplicated: one broken render can fire the same error on every
 *  frame, and a hundred identical reports say nothing a single one does not. */
const seen = new Set<string>();
const MAX_DISTINCT = 20;

export function reportError(
  error: unknown,
  context: { path?: string; kind?: string } = {}
): void {
  if (typeof window === "undefined") return;

  const err = error instanceof Error ? error : new Error(String(error));
  const message = (err.message || "Unknown error").slice(0, 500);
  const key = `${context.kind ?? "error"}:${message}`;

  if (seen.has(key)) return;
  // A page generating endless distinct errors is itself the problem, and
  // reporting all of them would just be a second problem.
  if (seen.size >= MAX_DISTINCT) return;
  seen.add(key);

  const body = JSON.stringify({
    message,
    stack: err.stack?.slice(0, 4000) ?? null,
    // Path only. A full URL can carry a share token or something the user
    // typed, and neither belongs in a bug report.
    path: context.path ?? window.location.pathname,
    kind: context.kind ?? "error",
  });

  try {
    // keepalive so the report still goes out if this error is what makes the
    // user close the tab.
    void fetch(`${BASE_URL}/api/v1/telemetry/browser-error`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => {
      // Reporting a failure to report helps nobody.
    });
  } catch {
    /* ignore */
  }
}

/** Catches what React's error boundaries cannot: errors thrown outside render,
 *  and promise rejections nobody handled. Returns a cleanup function. */
export function installGlobalErrorReporting(): () => void {
  if (typeof window === "undefined") return () => {};

  const onError = (e: ErrorEvent) => {
    reportError(e.error ?? e.message, { kind: "uncaught" });
  };
  const onRejection = (e: PromiseRejectionEvent) => {
    reportError(e.reason, { kind: "unhandled-rejection" });
  };

  window.addEventListener("error", onError);
  window.addEventListener("unhandledrejection", onRejection);

  return () => {
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onRejection);
  };
}
