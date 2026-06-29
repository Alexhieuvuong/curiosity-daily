"""
email_brief.py — deliver the daily brief by email (Resend).

Converts the Markdown brief to HTML and sends via the Resend API. No-ops if
RESEND_API_KEY is unset, so a run never fails just because email isn't configured.

Adapted from ai-daily-digest/scripts/email_brief.py.

Env:
- RESEND_API_KEY  (required to send; missing -> skipped)
- EMAIL_TO        (recipient; default below)
- EMAIL_FROM      (sender; default onboarding@resend.dev — Resend's test sender)
"""

import os

import requests
import markdown as md_lib


# The Resend account owner. Resend's test sender (onboarding@resend.dev) can only
# deliver to the account owner's own address until a domain is verified.
DEFAULT_TO = "hieudinhvuong@gmail.com"
DEFAULT_FROM = "onboarding@resend.dev"


def _wrap_html(inner: str) -> str:
    """Wrap the HTML body in a minimal, mobile-friendly frame."""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f6f8fa;">
  <div style="max-width:680px;margin:0 auto;padding:24px 20px;
              font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
              color:#1f2328;line-height:1.6;font-size:15px;">
    {inner}
  </div>
</body></html>"""


def send_email(subject: str, markdown_body: str) -> None:
    """Send the brief via Resend. Skips silently if RESEND_API_KEY is unset."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("[email] RESEND_API_KEY not set — skipping email.")
        return

    to_addr = os.environ.get("EMAIL_TO") or DEFAULT_TO
    from_addr = os.environ.get("EMAIL_FROM") or DEFAULT_FROM

    html = _wrap_html(md_lib.markdown(markdown_body, extensions=["extra", "sane_lists"]))

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_addr,
                "to": [to_addr],
                "subject": subject,
                "html": html,
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            print(f"[email] Sent to {to_addr} (id: {resp.json().get('id')})")
        else:
            print(f"[email] Failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:  # an email error must never break the whole run
        print(f"[email] Error while sending: {e}")
