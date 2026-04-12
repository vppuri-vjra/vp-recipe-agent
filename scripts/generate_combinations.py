"""
generate_combinations.py — Uses Claude to generate 15-20 unique, realistic
combinations of dimension values for recipe bot eval testing.

Usage:
    uv run python scripts/generate_combinations.py
"""

import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

# ── Dimensions ────────────────────────────────────────────────────────────────
DIMENSIONS = {
    "Cuisine Type":        ["Italian", "Thai", "Mexican", "Japanese", "Indian"],
    "Dietary Restriction": ["Vegan", "Gluten-free", "Keto", "Nut-free", "Dairy-free"],
    "Meal Type":           ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"],
    "Skill Level":         ["Beginner", "Intermediate", "Advanced"],
}

# ── Prompt ────────────────────────────────────────────────────────────────────
GENERATION_PROMPT = """
You are helping build an evaluation dataset for a Recipe Suggestion Bot.

Here are the dimensions and their possible values:

{dimensions}

Your task:
1. Generate 15-20 unique combinations of these dimension values.
2. Each combination should use 2-4 dimensions (not always all four).
3. For each combination, write a natural user query someone would realistically type.
4. Flag any combination that seems unrealistic with "UNREALISTIC" so it can be reviewed.

Return your response as a valid JSON array with this structure:
[
  {{
    "id": 1,
    "combination": {{
      "Cuisine Type": "Italian",
      "Dietary Restriction": "Vegan",
      "Meal Type": "Dinner",
      "Skill Level": "Beginner"
    }},
    "query": "I'm a beginner cook looking for a vegan Italian dinner recipe",
    "realistic": true,
    "note": ""
  }},
  ...
]

Only return the JSON array, no other text.
"""


def format_dimensions(dims: dict) -> str:
    lines = []
    for dim, values in dims.items():
        lines.append(f"- {dim}: {', '.join(values)}")
    return "\n".join(lines)


def main():
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = GENERATION_PROMPT.format(
        dimensions=format_dimensions(DIMENSIONS)
    )

    print("🤖 Asking Claude to generate dimension combinations...\n")

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    raw = raw.strip()

    # Parse JSON
    combinations = json.loads(raw)

    # Display all combinations for review
    print(f"{'='*65}")
    print(f"{'ID':<4} {'REALISTIC':<10} {'QUERY':<50}")
    print(f"{'='*65}")
    for c in combinations:
        flag = "✅" if c["realistic"] else "❌ UNREALISTIC"
        print(f"{c['id']:<4} {flag:<10} {c['query'][:55]}")
        dims = " + ".join(f"{k}={v}" for k, v in c["combination"].items())
        print(f"          Dims: {dims}")
        if c.get("note"):
            print(f"          Note: {c['note']}")
        print()

    # Save full output
    output_file = ROOT / "data" / "combinations_raw.json"
    output_file.write_text(json.dumps(combinations, indent=2), encoding="utf-8")
    print(f"\n💾 Saved to: {output_file}")
    print(f"\n📋 Next step: Review above and run generate_combinations.py")
    print(f"   to filter unrealistic ones into dimension_queries.csv")


if __name__ == "__main__":
    main()
