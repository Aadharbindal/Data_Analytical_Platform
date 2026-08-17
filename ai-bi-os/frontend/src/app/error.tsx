'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { reportError } from '@/lib/reportError';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    // This page said "our team has been notified" while doing nothing but
    // logging to a console nobody was reading. Now it sends the crash, so the
    // sentence below is true.
    console.error(error);
    reportError(error, { kind: 'render' });
  }, [error]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center p-4">
      <div className="glass-card flex max-w-md flex-col items-center rounded-2xl p-8 text-center shadow-2xl">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-rose-500/10 text-rose-500 ring-1 ring-rose-500/20">
          <AlertCircle className="h-8 w-8" />
        </div>
        <h2 className="mb-2 text-2xl font-semibold tracking-tight text-foreground">
          Something went wrong
        </h2>
        <p className="mb-8 text-sm text-muted-foreground">
          An unexpected error occurred while rendering this page. It has been reported.
        </p>
        
        <div className="flex w-full flex-col gap-3 sm:flex-row sm:justify-center">
          <Button 
            onClick={() => reset()}
            variant="default"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </Button>
          <Button 
            onClick={() => router.push('/')}
            variant="outline"
            className="flex items-center gap-2 border-white/10 hover:bg-white/5"
          >
            <Home className="h-4 w-4" />
            Go to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
