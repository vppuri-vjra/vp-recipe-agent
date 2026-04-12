# Failure Mode Taxonomy — VP Recipe Agent

> Based on bulk testing of 20 dimension-combination queries against `claude-opus-4-5`
> using `data/dimension_queries.csv` and evaluated via `scripts/error_analysis.py`.

---

## FM-01: Dietary Constraint Violation

**Title:** Dietary Constraint Violation

**Definition:** The bot suggests an ingredient or technique that directly violates the user's stated dietary restriction (e.g., using dairy in a dairy-free recipe, or meat in a vegan recipe).

**Examples:**
- *Observed (ID 19):* Query was "Simple vegan Japanese dinner for a cooking newbie." The bot suggested a fried egg as an optional topping — eggs are not vegan.
- *Hypothetical:* A gluten-free query receives a recipe using regular soy sauce without flagging it as a gluten risk.

---

## FM-02: False Keyword Match (Checker Limitation)

**Title:** False Keyword Match — Naive Evaluator Error

**Definition:** The automated checker incorrectly flags a response as a failure because a forbidden keyword appears in a non-violating context (e.g., "cream" in "cashew cream", "butter" in "peanut butter", "temper" in "temperature").

**Examples:**
- *Observed (ID 1):* Vegan Italian dinner query. Checker flagged `cream` but the bot used **cashew cream** — fully vegan. → False Positive.
- *Observed (ID 13):* Beginner query. Checker flagged `temper` as an advanced term but it appeared inside the word **temperature**. → False Positive.

**Impact on Metrics:** This failure mode inflated our FP count to 9, dropping TNR to 53% and Precision to 10%.

---

## FM-03: Skill Level Mismatch

**Title:** Skill Level Mismatch

**Definition:** The bot uses advanced culinary techniques or terminology in a recipe intended for a beginner, making the recipe difficult to follow for the target audience.

**Examples:**
- *Observed (ID 8):* Query was "Simple vegan Thai recipes for someone just learning to cook." Bot used the term `julienne` (though it offered "or grated" as an alternative — borderline acceptable).
- *Hypothetical:* A beginner query receives a recipe requiring "deglaze the pan with cognac and reduce by half" with no simpler alternative offered.

---

## FM-04: Cuisine-Restriction Conflict

**Title:** Cuisine-Dietary Restriction Conflict

**Definition:** The bot is asked to combine a cuisine type and a dietary restriction that are fundamentally incompatible, leading to either a recipe that abandons the cuisine authenticity or an unacknowledged constraint violation.

**Examples:**
- *Observed (ID 12):* "Keto-friendly Japanese desserts" — traditional Japanese desserts rely on rice, mochi, and sugar. Bot returned a response but authenticity was compromised.
- *Observed (ID 20):* "Keto Italian breakfast ideas" — Italian breakfast is pastry/bread-heavy. Bot managed but stretched authentic Italian identity.

---

## FM-05: Recipe Repetition

**Title:** Recipe Repetition / Variety Failure

**Definition:** The bot suggests the same or very similar recipe names across multiple queries, violating the system prompt rule to vary suggestions.

**Examples:**
- *Observed (original sample_queries run):* "Lemon Herb Roasted Chicken Thighs" was suggested for both ID 13 (vague query) and ID 18 (nut-free query) — exact duplicate name.
- *Observed:* "Honey Garlic Chicken" appeared in IDs 5 and 14 of the original run.

---

## FM-06: Default Protein Bias

**Title:** Default Protein Bias (Chicken Preference)

**Definition:** When given a vague or underspecified query, the bot defaults to chicken-based dishes, lacking variety in protein selection.

**Examples:**
- *Observed (original run, IDs 13, 14, 15):* Three consecutive vague queries ("Recipe", "Make me something good", "I want to eat something") all resulted in chicken dishes.
- *Hypothetical:* Any unspecified cuisine query consistently returns chicken regardless of prior suggestions in the same session.

---

## Summary Table

| ID | Failure Mode | Observed | Frequency |
|---|---|---|---|
| FM-01 | Dietary Constraint Violation | ✅ Yes | 1 confirmed (ID 19) |
| FM-02 | False Keyword Match | ✅ Yes | 9 false positives |
| FM-03 | Skill Level Mismatch | ✅ Yes | 2 cases (IDs 8, 13) |
| FM-04 | Cuisine-Restriction Conflict | ✅ Yes | 2 borderline (IDs 12, 20) |
| FM-05 | Recipe Repetition | ✅ Yes | 2 duplicates in original run |
| FM-06 | Default Protein Bias | ✅ Yes | 3 chicken defaults in vague queries |

---

## Checker Performance vs Ground Truth

| Metric | Value | Interpretation |
|---|---|---|
| **TPR** | 100% | Caught every real failure — no missed violations |
| **TNR** | 53% | High false alarm rate — checker too aggressive |
| **Precision** | 10% | Only 1 in 10 flags was a genuine failure |
| **FPR** | 47% | Nearly half of clean responses were falsely flagged |

> **Root Cause of Low TNR:** FM-02 (naive keyword matching) accounts for all 9 false positives.
> Fixing the checker to understand context (e.g. "peanut butter" ≠ dairy) would bring TNR close to 100%.
