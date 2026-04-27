# VP Recipe Agent — Eval Methodology

**Course:** Understanding Evals  
**Project:** VP Recipe Agent (cooking recipe chatbot)  
**Model:** claude-opus-4-5 | **Test Queries:** 20 | **Date:** April 2026

---

## What is the VP Recipe Agent

A recipe chatbot built on Claude that suggests complete, tailored recipes based on user preferences — dietary restrictions, skill level, cuisine type.

**The eval question:** Does the agent follow its rules? Specifically — does it ever violate dietary constraints, use wrong skill level, or repeat recipes?

---

## System Prompt Design

The system prompt has 4 sections:

| Section | Purpose |
|---|---|
| **Role & Objective** | Defines the agent as a culinary assistant — friendly, creative, tailored |
| **Instructions & Response Rules** | ALWAYS / NEVER rules — dietary compliance, vary suggestions, complete recipes |
| **LLM Agency** | What Claude can decide — creative combinations, substitutions, no follow-up questions before answering |
| **Output Formatting** | Strict Markdown structure — Recipe Name, Description, Ingredients, Instructions, Tips |

### Key design decisions

**No follow-up questions before answering** — agent must attempt a recipe first, then invite refinement. This tests if the agent can handle underspecified queries without stalling.

**Vary suggestions** — explicit rule to prevent repetition. Tests if the agent generalizes across queries.

**SAFETY CLAUSE** — if asked for harmful recipes, decline politely without being preachy.

---

## Test Query Design

**20 queries across 3 dimensions:**

| Dimension | Examples |
|---|---|
| **Dietary restriction** | Vegan, keto, gluten-free, dairy-free, nut-free |
| **Cuisine type** | Italian, Japanese, Thai, Mexican, Indian |
| **Skill level** | Beginner, intermediate, advanced |

Queries were designed as **dimension combinations** — testing the agent on the intersections that are hardest to satisfy simultaneously (e.g., keto + Japanese, vegan + beginner).

---

## Eval Approach — Automated Checker

### What the checker does

For each of 20 responses, the checker looks for:
- **Dietary violations** — forbidden ingredients appearing in the recipe text
- **Skill level violations** — advanced culinary terms in beginner-targeted recipes
- **Recipe repetition** — same recipe name appearing across multiple responses

### Checker design — keyword matching

```
vegan query → checker scans response for: meat, chicken, beef, fish, egg, dairy, butter, cream, milk
beginner query → checker scans for: julienne, deglaze, temper, chiffonade, brunoise, fond
```

---

## Results

### Confusion Matrix

| | Checker says PASS | Checker says FAIL |
|---|---|---|
| **Actually PASS** | 10 (TN) | 9 (FP) ← problem |
| **Actually FAIL** | 0 (FN) | 1 (TP) |

### Metrics

| Metric | Value | What it means |
|---|---|---|
| **TPR (Sensitivity)** | 100% | Caught every real failure — no missed violations |
| **TNR (Specificity)** | 53% | High false alarm rate — checker too aggressive |
| **Precision** | 10% | Only 1 in 10 flags was a genuine failure |
| **FPR** | 47% | Nearly half of clean responses were falsely flagged |

---

## Failure Mode Taxonomy

### FM-01 — Dietary Constraint Violation
**Definition:** Bot suggests an ingredient that violates the stated dietary restriction.  
**Observed:** ID 19 — "Simple vegan Japanese dinner" — bot suggested a fried egg as optional topping. Eggs are not vegan.  
**Frequency:** 1 confirmed

### FM-02 — False Keyword Match (Checker Limitation)
**Definition:** Checker incorrectly flags a clean response because a forbidden keyword appears in a non-violating context.  
**Observed:**
- ID 1 — Vegan Italian query. Checker flagged `cream` but bot used **cashew cream** — fully vegan. → False Positive
- ID 13 — Beginner query. Checker flagged `temper` as advanced term but it appeared inside **temperature**. → False Positive  
**Frequency:** 9 false positives — **root cause of low TNR**

### FM-03 — Skill Level Mismatch
**Definition:** Bot uses advanced culinary techniques in a beginner-targeted recipe.  
**Observed:** ID 8 — "Simple vegan Thai for beginners" — bot used `julienne` (offered "or grated" as alternative — borderline).  
**Frequency:** 2 borderline cases

### FM-04 — Cuisine-Restriction Conflict
**Definition:** Cuisine and dietary restriction are fundamentally incompatible — bot stretches authenticity or ignores the conflict.  
**Observed:**
- ID 12 — "Keto Japanese desserts" — traditional Japanese desserts are rice/mochi/sugar-based
- ID 20 — "Keto Italian breakfast" — Italian breakfast is pastry-heavy  
**Frequency:** 2 borderline cases

### FM-05 — Recipe Repetition
**Definition:** Same recipe suggested across multiple queries.  
**Observed:** "Lemon Herb Roasted Chicken Thighs" appeared in both ID 13 and ID 18.  
**Frequency:** 2 duplicates

### FM-06 — Default Protein Bias
**Definition:** Bot defaults to chicken for vague or underspecified queries.  
**Observed:** IDs 13, 14, 15 — three consecutive vague queries all returned chicken dishes.  
**Frequency:** 3 cases in original run

---

## The 3 Gulfs — Applied to Recipe Agent

The 3 Gulfs framework explains where AI agents fail:

| Gulf | Definition | Recipe Agent example |
|---|---|---|
| **Gulf of Comprehension** | Agent misunderstands what the user wants | "Keto Japanese desserts" — agent doesn't flag the incompatibility, just tries to comply |
| **Gulf of Specification** | System prompt doesn't fully specify the required behaviour | "Vary suggestions" rule didn't prevent protein bias — rule was there but not specific enough |
| **Gulf of Generalization** | Agent applies rules correctly in training cases but fails on edge cases | Vegan rule followed for obvious cases (meat) but missed edge case (egg as optional topping) |

---

## Root Cause of Low TNR — FM-02

**Problem:** Naive keyword matching can't distinguish context.

```
"cashew cream"   → checker sees "cream" → flags as dairy violation → FALSE POSITIVE
"temperature"    → checker sees "temper" → flags as advanced term → FALSE POSITIVE
"peanut butter"  → checker sees "butter" → flags as dairy → FALSE POSITIVE
```

**Fix:** Context-aware checker — use LLM-as-judge instead of keyword matching.  
This is exactly what we built in Step 3 (VP Substitution Agent — LLM Judge).

---

## Key Learnings

| Learning | Detail |
|---|---|
| **TPR ≠ quality** | 100% TPR sounds great — but with 53% TNR, the checker is nearly useless in practice. Alerts every response, no one trusts it. |
| **Keyword checkers break on context** | "cashew cream" is not dairy. A checker that can't read context will always have this problem. |
| **LLM agency creates edge cases** | "Feel free to add substitutions" in the system prompt created the vegan egg topping failure. Agency rules need boundaries. |
| **Dimension combinations reveal failures** | Single-dimension queries (just "vegan") passed easily. Cross-dimension queries (keto + Japanese) exposed real gaps. |
| **3 Gulfs are real** | Every failure maps to one of the three gulfs — comprehension, specification, or generalization. |

---

## What the Checker Should Have Been

**V1 — keyword match (what we built)**
- Fast, deterministic, zero API cost
- Breaks on context (FM-02 — the main failure)

**V2+ — LLM-as-judge (what we built in Step 3)**
- Reads full response + context
- Understands "cashew cream" ≠ dairy
- Higher accuracy, API cost per evaluation

**The lesson:** Start with a simple checker to establish baseline. Then iterate toward semantic understanding when the simple checker's failure modes are understood.

---

## Tech Stack

| Component | Tool |
|---|---|
| Model | claude-opus-4-5 |
| Bulk test runner | `scripts/bulk_test.py` (Python, Anthropic SDK) |
| Checker | `scripts/error_analysis.py` (keyword matching) |
| Results viewer | `scripts/generate_viewer.py` (HTML output) |
| Query generation | `scripts/generate_combinations.py` |
| Ground truth | `data/ground_truth.csv` (manually labeled) |

---

## Files

| File | Purpose |
|---|---|
| `prompts/system_prompt.txt` | 4-section system prompt |
| `data/sample_queries.csv` | 20 diverse test queries |
| `data/dimension_queries.csv` | Queries by dimension combination |
| `data/ground_truth.csv` | Manually labeled ground truth |
| `failure_mode_taxonomy.md` | 6 failure modes with examples |
| `results/` | JSON + HTML output from bulk test runs |

---

## GitHub

https://github.com/vppuri-vjra/vp-recipe-agent
