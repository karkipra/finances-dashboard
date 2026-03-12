"""
PDF budget parser. Sends PDF to Claude API (document type) and extracts
the 24-month budget table into structured rows for budget_plan table.
"""

import base64
import json
import requests
import config

PDF_PROMPT = """You are a financial data extractor. This PDF contains a 24-month household budget spreadsheet with rows for income and expenses by month.

Extract ALL numeric data from the budget table. Return a JSON object with this exact structure:

{
  "years": [
    {
      "year": 2025,
      "months": [
        {
          "month": 1,
          "nastya_income": 3600.00,
          "pratik_income": 0.0,
          "monthly_expenses": -3500.00,
          "one_time_income": 0.0,
          "one_time_expense": 0.0,
          "hysa": 0.0,
          "roth": 0.0,
          "net_income": 100.00
        }
      ]
    }
  ]
}

Rules:
- Income values should be positive floats.
- Expense values should be negative floats (the sheet may show them as positive with parentheses - convert those to negative).
- If a cell is blank or zero, use 0.0.
- Include ALL 12 months for each year shown.
- Do not skip any row or month.
"""


def extract_budget(pdf_path):
    """
    Send PDF to Claude. Returns (list_of_budget_rows, tokens_used).
    Each row: {year, month, category, planned_amount}
    On error returns ([], 0).
    """
    if not config.ANTHROPIC_API_KEY:
        print("  [WARN] ANTHROPIC_API_KEY not set - skipping PDF parse.")
        return [], 0

    try:
        with open(pdf_path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"  [ERROR] Could not read {pdf_path}: {e}")
        return [], 0

    payload = {
        "model": config.SONNET_MODEL,
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {"type": "text", "text": PDF_PROMPT},
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
            timeout=90,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  [ERROR] Claude API call failed: {e}")
        return [], 0

    result = resp.json()
    text = result["content"][0]["text"]
    tokens = result["usage"]["input_tokens"] + result["usage"]["output_tokens"]

    # Strip markdown fences
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:]
        text = inner.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Could not parse PDF response as JSON: {e}")
        return [], tokens

    # Flatten into storage rows
    rows = []
    categories = [
        "nastya_income", "pratik_income", "monthly_expenses",
        "one_time_income", "one_time_expense", "hysa", "roth", "net_income"
    ]
    for year_block in data.get("years", []):
        year = year_block["year"]
        for month_data in year_block.get("months", []):
            month = month_data["month"]
            for cat in categories:
                val = month_data.get(cat, 0.0) or 0.0
                rows.append({
                    "year": year,
                    "month": month,
                    "category": cat,
                    "planned_amount": round(float(val), 2),
                })

    return rows, tokens
