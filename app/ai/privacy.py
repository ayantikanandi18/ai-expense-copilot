"""Best-effort PII redaction applied before any text is sent to the LLM.

This is a data-minimization gesture in the spirit of GDPR/CCPA, not a
certified PII scrubber — regexes cannot catch every PII pattern. It exists
so the design decision is visible and intentional rather than absent.
"""

import re

SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

REDACTIONS = [
    (SSN_RE, "[REDACTED-SSN]"),
    (CREDIT_CARD_RE, "[REDACTED-CARD]"),
    (EMAIL_RE, "[REDACTED-EMAIL]"),
    (PHONE_RE, "[REDACTED-PHONE]"),
]


def redact(text):
    """Returns (redacted_text, was_redacted)."""
    redacted_text = text
    changed = False
    for pattern, replacement in REDACTIONS:
        new_text, n = pattern.subn(replacement, redacted_text)
        if n:
            changed = True
        redacted_text = new_text
    return redacted_text, changed
