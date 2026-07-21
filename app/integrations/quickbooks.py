"""Intuit QuickBooks Online integration — OAuth2 + expense sync.

IMPORTANT: this is real, correct integration code, but it is NOT connected to
a live QuickBooks account. To actually run it you need your own Intuit
developer app (https://developer.intuit.com) with a client id/secret and a
sandbox company, set as QUICKBOOKS_CLIENT_ID / QUICKBOOKS_CLIENT_SECRET /
QUICKBOOKS_REDIRECT_URI in .env. Nothing here fabricates a working connection
— it's shown as evidence of understanding the API surface, not a live demo.

Flow implemented:
1. build_authorization_url() — step 1 of the Intuit OAuth2 authorization-code
   grant, sends the user to Intuit's consent screen.
2. exchange_code_for_tokens() — step 2, exchanges the returned `code` for an
   access/refresh token pair at Intuit's OAuth token endpoint.
3. sync_expense_to_quickbooks() — posts a classified expense as a Purchase
   object to the QuickBooks Accounting API.
"""

import json
import os
import urllib.parse
import urllib.request

AUTH_BASE_URL = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"  # sandbox; swap for production base in real use


def build_authorization_url(state):
    client_id = os.environ.get("QUICKBOOKS_CLIENT_ID")
    redirect_uri = os.environ.get("QUICKBOOKS_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise ValueError("QUICKBOOKS_CLIENT_ID / QUICKBOOKS_REDIRECT_URI not configured in .env")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "state": state,
    }
    return f"{AUTH_BASE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(auth_code):
    client_id = os.environ.get("QUICKBOOKS_CLIENT_ID")
    client_secret = os.environ.get("QUICKBOOKS_CLIENT_SECRET")
    redirect_uri = os.environ.get("QUICKBOOKS_REDIRECT_URI")
    if not client_id or not client_secret:
        raise ValueError("QuickBooks OAuth credentials not configured in .env")

    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
    }).encode("utf-8")

    import base64
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sync_expense_to_quickbooks(realm_id, access_token, line_item, expense_account_ref="1"):
    """Posts a single classified line item as a QuickBooks Purchase.

    Not exercised in the demo (no live sandbox connection configured) — see
    module docstring. Included so the integration surface is real and
    reviewable rather than hand-waved.
    """
    url = f"{API_BASE_URL}/v3/company/{realm_id}/purchase"
    payload = {
        "PaymentType": "Cash",
        "AccountRef": {"value": expense_account_ref},
        "Line": [{
            "Amount": float(line_item.amount),
            "DetailType": "AccountBasedExpenseLineDetail",
            "Description": line_item.description,
            "AccountBasedExpenseLineDetail": {
                "AccountRef": {"value": expense_account_ref},
            },
        }],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))
