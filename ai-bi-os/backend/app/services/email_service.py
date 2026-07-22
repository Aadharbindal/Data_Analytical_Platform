import os
import httpx

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "DataMind <onboarding@resend.dev>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

enabled = bool(RESEND_API_KEY)


def send_verification_email(to_email: str, full_name: str, token: str) -> bool:
    """Sends a real email via Resend's HTTP API. No-ops (returns False) if
    RESEND_API_KEY isn't set — signup/resend callers treat that the same way
    app/services/storage.py treats a disabled S3 client: log it, move on."""
    if not enabled:
        print(f"[email_service] RESEND_API_KEY not set — skipping verification email to {to_email}")
        return False

    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": EMAIL_FROM,
                "to": [to_email],
                "subject": "Verify your DataMind email address",
                "html": f"""
                    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                        <h2>Hi {full_name},</h2>
                        <p>Confirm this is your email address to finish setting up your DataMind account.</p>
                        <p>
                            <a href="{verify_url}"
                               style="display:inline-block;padding:12px 24px;background:#2563eb;color:#fff;
                                      border-radius:8px;text-decoration:none;font-weight:600;">
                                Verify email address
                            </a>
                        </p>
                        <p style="color:#666;font-size:13px;">Or paste this link in your browser: {verify_url}</p>
                        <p style="color:#999;font-size:12px;">If you didn't create a DataMind account, you can ignore this email.</p>
                    </div>
                """,
            },
            timeout=10,
        )
        if response.status_code >= 400:
            print(f"[email_service] Resend API error {response.status_code}: {response.text}")
            return False
        return True
    except Exception as e:
        print(f"[email_service] Failed to send verification email: {e}")
        return False
