"""
bulk_test.py — Runs all queries in data/sample_queries.csv through the
Recipe Suggestion Bot and writes results to results/results_<timestamp>.json
"""

import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

MODEL = "claude-opus-4-5"
MAX_TOKENS = 1024
ROOT = Path(__file__).parent.parent

SYSTEM_PROMPT_FILE = ROOT / "prompts" / "system_prompt.txt"
QUERIES_FILE       = ROOT / "data" / "sample_queries.csv"
RESULTS_DIR        = ROOT / "results"

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_system_prompt() -> str:
    return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()


def load_queries() -> list[dict]:
    with open(QUERIES_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_query(client: anthropic.Anthropic, system_prompt: str, query: str) -> tuple[str, float]:
    start = time.time()
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": query}],
    )
    duration_ms = round((time.time() - start) * 1000)
    response_text = message.content[0].text
    return response_text, duration_ms


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = load_system_prompt()
    queries = load_queries()

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"results_{timestamp}.json"

    results = []
    total = len(queries)

    print(f"\n🍳 VP Recipe Agent — Bulk Test")
    print(f"   Model   : {MODEL}")
    print(f"   Queries : {total}")
    print(f"   Output  : {output_file}\n")

    for i, row in enumerate(queries, 1):
        query = row["query"]
        print(f"[{i:02d}/{total}] {query[:60]}...")

        try:
            response, duration_ms = run_query(client, system_prompt, query)
            status = "success"
        except Exception as e:
            response = f"ERROR: {e}"
            duration_ms = 0
            status = "error"

        results.append({
            "id":                  row["id"],
            "query":               query,
            "category":            row["category"],
            "failure_mode_tested": row["failure_mode_tested"],
            "status":              status,
            "duration_ms":         duration_ms,
            "response":            response,
        })

        print(f"         ✅ {duration_ms}ms\n" if status == "success" else f"         ❌ {response}\n")

    # Write JSON output
    output = {
        "metadata": {
            "timestamp":   timestamp,
            "model":       MODEL,
            "total":       total,
            "success":     sum(1 for r in results if r["status"] == "success"),
            "errors":      sum(1 for r in results if r["status"] == "error"),
        },
        "results": results,
    }

    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Done! Results saved to: {output_file}")


if __name__ == "__main__":
    main()
