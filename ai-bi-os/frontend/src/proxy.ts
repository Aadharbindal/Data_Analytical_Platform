import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Auth is handled client-side via localStorage Bearer tokens (AuthContext).
// Server-side middleware cannot access localStorage, so we do NOT redirect here.
// All protected route guarding is done in AuthContext + AppLayoutWrapper.
export function proxy(request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.glb|api).*)'],
};
