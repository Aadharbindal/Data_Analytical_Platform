"""Read a Google Sheet that has been shared by link.

Deliberately not OAuth. Reading a user's spreadsheets through the API needs
`spreadsheets.readonly`, which Google classes as a sensitive scope: until an
app passes their verification review, only manually-added test users can
connect at all. That would gate the feature behind a review process rather
than shipping it. A link-shared sheet exports as CSV over plain HTTP, needs no
credentials, and works for every user immediately.

The trade-off is real and belongs in front of the user, not buried here: a
link-shared sheet is readable by anyone who has the URL. The connect dialog
says so.
"""

import re
from typing import Optional, Tuple

import httpx

# Matches both the normal editing URL and the /d/e/... published form.
_SHEET_ID = re.compile(r"/spreadsheets/d/(?:e/)?([a-zA-Z0-9-_]+)")
_GID = re.compile(r"[#&?]gid=([0-9]+)")

FETCH_TIMEOUT_SECONDS = 25
MAX_SHEET_BYTES = 50 * 1024 * 1024


class SheetError(Exception):
    """Carries a message meant to be shown to the user as-is."""


def parse_sheet_url(url: str) -> Tuple[str, Optional[str]]:
    """Pull the spreadsheet id and optional tab id out of a Sheets URL."""
    if not url or "docs.google.com" not in url:
        raise SheetError(
            "That doesn't look like a Google Sheets link. It should start with "
            "https://docs.google.com/spreadsheets/…"
        )

    m = _SHEET_ID.search(url)
    if not m:
        raise SheetError(
            "Couldn't find a spreadsheet ID in that link. Copy the URL straight "
            "from your browser's address bar while the sheet is open."
        )

    gid_match = _GID.search(url)
    return m.group(1), (gid_match.group(1) if gid_match else None)


def build_export_url(sheet_id: str, gid: Optional[str]) -> str:
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return f"{base}&gid={gid}" if gid else base


def fetch_sheet_csv(url: str) -> Tuple[bytes, str]:
    """Fetch a link-shared sheet as CSV bytes. Returns (content, export_url)."""
    sheet_id, gid = parse_sheet_url(url)
    export_url = build_export_url(sheet_id, gid)

    try:
        with httpx.Client(follow_redirects=True, timeout=FETCH_TIMEOUT_SECONDS) as client:
            resp = client.get(export_url)
    except httpx.TimeoutException:
        raise SheetError("Google didn't respond in time. Try again in a moment.")
    except httpx.HTTPError:
        raise SheetError("Couldn't reach Google Sheets. Check your connection and try again.")

    # A sheet that isn't shared does NOT come back as an error. Google answers
    # 200 with the HTML of a sign-in page, which would otherwise sail into the
    # CSV parser and land as a dataset full of markup. Content type is the
    # reliable tell.
    content_type = resp.headers.get("content-type", "")
    if resp.status_code in (401, 403) or "text/html" in content_type:
        raise SheetError(
            "This sheet isn't shared publicly, so it can't be read. In Google "
            "Sheets open Share, set General access to \"Anyone with the link\" "
            "as Viewer, then paste the link again."
        )

    if resp.status_code == 404:
        raise SheetError("That sheet doesn't exist, or it has been deleted.")

    if resp.status_code != 200:
        raise SheetError(f"Google returned an unexpected error ({resp.status_code}). Try again.")

    content = resp.content
    if not content.strip():
        raise SheetError("That sheet (or the selected tab) is empty.")

    if len(content) > MAX_SHEET_BYTES:
        raise SheetError("That sheet is too large to import.")

    return content, export_url


def sheet_display_name(url: str) -> str:
    """A stable filename for the dataset, so re-syncs version the same row."""
    sheet_id, gid = parse_sheet_url(url)
    suffix = f"-{gid}" if gid else ""
    return f"gsheet-{sheet_id[:12]}{suffix}.csv"
