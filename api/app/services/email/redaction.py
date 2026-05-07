"""PHI redaction for the audit row.

The outbound email keeps PHI (the family member receiving the invoice
deserves the client's actual name). The audit row does not — operators query
email_events for "did the family receive this?" without needing to see PHI.

Strategy: callers pass a *template* with named parameters and a parameter map.
The redactor renders the outbound subject by substituting raw values, and
renders the audit subject by substituting placeholder tokens for any PII-named
keys. Pattern-based scrubbing (regex for emails, phones, SSN-shaped, dates)
runs on top to catch leaks the template missed.

If a caller has only a fully-rendered subject (no template), pass the same
string to both subject_rendered and subject_redacted; the redactor's regex
pass will still strip obvious PII patterns from the redacted side.
"""

from __future__ import annotations

import re
from typing import Final

# Field names whose values are ALWAYS PII and must be replaced with a token.
# Extend as new email categories add fields.
PII_PARAM_TOKENS: Final[dict[str, str]] = {
    "client_name": "<client>",
    "family_name": "<family>",
    "caregiver_name": "<caregiver>",
    "patient_name": "<client>",
    "first_name": "<person>",
    "last_name": "<person>",
    "full_name": "<person>",
}

_EMAIL_RE = re.compile(r"[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Dates (HIPAA Safe Harbor: anything more granular than year is PHI).
# Accept 2026-05-07, 5/7/2026, 5/7/26, May 7, 2026.
_ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_SLASH_DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_LONG_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{1,2},?\s+\d{4}\b",
    flags=re.IGNORECASE,
)


def render_subjects(
    template: str,
    params: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (rendered_subject, redacted_subject).

    rendered_subject: template with raw param values substituted (for the
    outbound email).

    redacted_subject: template with PII params replaced by tokens, then a
    pattern-based scrub for emails / phones / SSNs / dates.
    """
    params = params or {}
    rendered = template.format(**params) if params else template

    redacted_params = {
        name: PII_PARAM_TOKENS[name] if name in PII_PARAM_TOKENS else value
        for name, value in params.items()
    }
    redacted = template.format(**redacted_params) if redacted_params else template
    redacted = redact_phi(redacted)
    return rendered, redacted


def redact_phi(text: str) -> str:
    """Pattern-based scrub. Idempotent."""
    text = _EMAIL_RE.sub("<email>", text)
    text = _PHONE_RE.sub("<phone>", text)
    text = _SSN_RE.sub("<ssn>", text)
    text = _ISO_DATE_RE.sub("<date>", text)
    text = _SLASH_DATE_RE.sub("<date>", text)
    text = _LONG_DATE_RE.sub("<date>", text)
    return text
