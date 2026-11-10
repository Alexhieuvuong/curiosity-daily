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
import time

import requests
import markdown as md_lib


# The Resend account owner. Resend's test sender (onboarding@resend.dev) can only
# deliver to the account owner's own address until a domain is verified.
DEFAULT_TO = "hieudinhvuong@gmail.com"
DEFAULT_FROM = "onboarding@resend.dev"

# Retry only transient failures (network errors, 5xx). A 4xx is a config error
# (bad key, unverified sender) that retrying won't fix, so we fail fast on those.
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 3


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


def send_email(subject: str, markdown_body: str) -> bool:
    """Send the brief via Resend.

    Returns True if the email was sent OR intentionally skipped (no RESEND_API_KEY),
    and False if a configured send failed. The caller uses this to fail the run so a
    missing morning email is noticed the same day instead of days later.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("[email] RESEND_API_KEY not set — skipping email.")
        return True

    to_addr = os.environ.get("EMAIL_TO") or DEFAULT_TO
    from_addr = os.environ.get("EMAIL_FROM") or DEFAULT_FROM

    html = _wrap_html(md_lib.markdown(markdown_body, extensions=["extra", "sane_lists"]))
    payload = {"from": from_addr, "to": [to_addr], "subject": subject, "html": html}

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
        except requests.RequestException as e:  # network error — transient, retry
            print(f"[email] Network error (attempt {attempt}/{_MAX_ATTEMPTS}): {e}")
        else:
            if resp.status_code in (200, 201):
                print(f"[email] Sent to {to_addr} (id: {resp.json().get('id')})")
                return True
            if resp.status_code < 500:  # 4xx — config error, retrying won't help
                print(f"[email] Failed {resp.status_code} (not retrying): {resp.text[:200]}")
                return False
            print(f"[email] Server error {resp.status_code} "
                  f"(attempt {attempt}/{_MAX_ATTEMPTS}): {resp.text[:200]}")

        if attempt < _MAX_ATTEMPTS:
            time.sleep(_BACKOFF_SECONDS)

    print(f"[email] Giving up after {_MAX_ATTEMPTS} attempts.")
    return False
