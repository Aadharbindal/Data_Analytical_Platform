"""Somewhere for the browser to report its own crashes.

A client-side error is invisible from the server: the page breaks, the person
either reloads or leaves, and nothing about it reaches anyone who could fix it.
This gives the browser a way to say so, and forwards it to the same place
server errors go.

Deliberately not a client SDK. Adding one would put another 30-40KB in front of
every visitor on a page whose weight is already worth arguing about, for
something only the maintainer benefits from. The cost of that trade lands on
the user; this way it does not.
"""

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.error_tracking import capture_message
from app.routers.auth import limiter

router = APIRouter()


class BrowserError(BaseModel):
    # Bounded because this endpoint is unauthenticated by necessity - a crash
    # can happen on the sign-in page, before anyone is logged in - and an
    # unbounded string field on an open endpoint is an invitation.
    message: str = Field(max_length=500)
    stack: Optional[str] = Field(default=None, max_length=4000)
    # Where it happened. Path only: a full URL can carry a share token or a
    # query the user typed.
    path: Optional[str] = Field(default=None, max_length=200)
    kind: Optional[str] = Field(default=None, max_length=40)


@router.post("/browser-error", status_code=204)
@limiter.limit("20/minute")
async def report_browser_error(request: Request, error: BrowserError):
    """Record a crash that happened in someone's browser.

    Always answers 204, even when tracking is switched off or the report is
    unusable. A page that has already broken should not then have a failed
    error report to deal with, and there is nothing the browser could
    usefully do with a rejection.
    """
    capture_message(
        f"Browser: {error.message}",
        level="error",
        path=error.path,
        kind=error.kind or "error",
        stack=error.stack,
        user_agent=request.headers.get("user-agent"),
    )
    return None
