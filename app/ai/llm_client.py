"""Thin wrapper around the Groq API (OpenAI-compatible chat completions).

Kept as a single narrow interface (parse_document / classify_line_item) so
swapping to another provider (OpenAI/Anthropic/Gemini) later only means
changing this file, not every call site.
"""

import json
import os
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

PARSE_SYSTEM_PROMPT = """You extract structured data from a receipt or invoice's raw text.
Only extract values that are explicitly present in the text — never invent a vendor name, date,
amount, or line item that isn't there. If a field isn't present, use null (or an empty list for
line_items). Respond with ONLY a JSON object:
{
  "vendor": <string or null>,
  "document_date": <string "YYYY-MM-DD" or null>,
  "total_amount": <number or null>,
  "line_items": [{"description": <string>, "amount": <number>}, ...]
}
"""

CLASSIFY_SYSTEM_PROMPT = """You classify a single expense line item into exactly one of the
provided categories. Base your answer only on the line item description given — do not invent
information about the vendor or purchase beyond what's stated. Respond with ONLY a JSON object:
{
  "category": <string — must be one of the provided categories, or "Uncategorized" if none fit>,
  "confidence": <number 0-1>,
  "rationale": <string — one sentence explaining why, grounded only in the description text>
}
"""


def _call_groq(system_prompt, user_content, api_key):
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return json.loads(body["choices"][0]["message"]["content"])


def parse_document(text, api_key=None):
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    result = _call_groq(PARSE_SYSTEM_PROMPT, text, api_key)
    result.setdefault("line_items", [])
    return result


def classify_line_item(description, categories, api_key=None):
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    user_content = (
        f"LINE ITEM: {description}\n"
        f"CATEGORIES: {', '.join(categories)}"
    )
    return _call_groq(CLASSIFY_SYSTEM_PROMPT, user_content, api_key)
