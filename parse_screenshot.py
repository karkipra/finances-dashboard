import base64
import json
import requests
import config

SCREENSHOT_PROMPT = """You are a financial data extractor. Analyze this screenshot from Empower Personal Capital.

Focus on the DETAILED ACCOUNT TABLE (right side panel showing individual account rows with name, type, and balance).
Do NOT extract the left sidebar group totals (e.g. "Cash $12,975", "Investments $136,849") — those are category rollups that double-count.

Extract each INDIVIDUAL account row from the table. Each row has: institution/account name, account type label, and a dollar balance.

Return a JSON object with this exact structure:
{
  "screenshot_type": "net_worth",
  "date": "YYYY-MM-DD or null if not visible",
  "accounts": [
    {"name": "Institution or Account Name", "balance": 12345.67, "account_type": "checking or savings or investment or credit or loan or mortgage"}
  ],
  "totals": {
    "total_assets": null,
    "total_liabilities": null,
    "net_worth": null
  },
  "allocations": [],
  "raw_numbers": [],
  "confidence": "high or medium or low",
  "notes": "anything unusual or ambiguous"
}

Rules:
- Only extract individual account rows, not category headers or subtotals.
- If the same institution appears multiple times with different balances, include each as a separate entry.
- Dollar amounts: plain floats, no $ or commas.
- Credit cards, loans, mortgages: negative floats.
- If a field is not visible, use null. Do not guess.
"""


def extract_data(image_path):
    """
    Send image to Claude Vision. Returns (extracted_dict, tokens_used).
    On error, returns (None, 0).
    """
    if not config.ANTHROPIC_API_KEY:
        print("  [WARN] ANTHROPIC_API_KEY not set — skipping screenshot parse.")
        return None, 0

    path_str = str(image_path)
    ext = path_str.rsplit(".", 1)[-1].lower()
    media_type_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_type_map.get(ext, "image/png")

    try:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"  [ERROR] Could not read {image_path}: {e}")
        return None, 0

    payload = {
        "model": config.SONNET_MODEL,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": SCREENSHOT_PROMPT},
                ],
            }
        ],
    }

    headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  [ERROR] Claude API call failed: {e}")
        return None, 0

    result = resp.json()
    text = result["content"][0]["text"]
    tokens = result["usage"]["input_tokens"] + result["usage"]["output_tokens"]

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.startswith("json"):
                inner = inner[4:]
            text = inner.strip()

    try:
        extracted = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Could not parse Claude response as JSON: {e}")
        return None, tokens

    return extracted, tokens
