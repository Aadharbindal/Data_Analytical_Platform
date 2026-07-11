'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
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
          An unexpected error occurred while rendering this page. Our team has been notified.
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
            onClick={() => router.push('/dashboard')}
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
