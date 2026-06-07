#!/usr/bin/env python3
"""Skill accuracy eval — verify AI picks correct skill + operation for given prompts.

Usage:
  python tests/eval/test_skill_accuracy.py          # deterministic keyword baseline (CI)
  python tests/eval/test_skill_accuracy.py --llm    # LLM eval via Gemini (manual/periodic)

Deterministic mode: regex keyword matching against routing tables.
LLM mode: sends prompt + skill descriptions to Gemini, checks routing decision.
"""
import os, re, sys, json, argparse
from pathlib import Path

SKILLS_DIR = "skills"

# Gemini config (company staging endpoint, OpenAI-compatible)
GEMINI_ENDPOINT = os.environ.get("GEMINI_ENDPOINT", "https://genai.stg.tvlk-data.com/openai")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "sk-3e66d456e9e674")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Test cases: (user_prompt, expected_skill_name, expected_operations)
TEST_CASES = [
    # Pricing
    ("What's the commission rate for GA?", "fpr-pricing", ["load_commission_incentive_rules"]),
    ("Check budget balance for IDR", "fpr-pricing", ["get_budget_balance"]),
    ("Show me autopilot rules for Thailand", "fpr-pricing", ["load_autopilot_rules"]),
    ("What's the markup for Garuda?", "fpr-pricing", ["load_baseline_pricing_rules"]),
    ("Any flash sale active?", "fpr-pricing", ["load_price_cut_modifier_rules"]),
    ("Show tiered incentive for this PNR", "fpr-pricing", ["check_tiered_incentive_progress"]),
    ("Transaction fee rules", "fpr-pricing", ["load_trx_fee_rules"]),
    ("Price prediction rules", "fpr-pricing", ["load_price_prediction_rules"]),

    # Supply
    ("Check fare for GA CGK-DPS tomorrow", "fpr-supply", ["check_fare"]),
    ("What's the fare adjuster for Lion Air?", "fpr-supply", ["load_fare_adjuster_by_base_fare"]),
    ("Show provider config for provider 123", "fpr-supply", ["read_pricing_provider"]),
    ("Active routes for VietJet", "fpr-supply", ["get_airline_routes"]),
    ("Where does fare come from for GA CGK-SIN?", "fpr-supply", ["get_provider_sourcing"]),
    ("Special fare config for TG", "fpr-supply", ["get_special_fare_config"]),

    # Demand
    ("Look up booking ABC123", "fpr-demand", ["get_flight_info"]),
    ("Simulate search CGK to DPS next Monday", "fpr-demand", ["simulate_search"]),
    ("Search fare cache CGK-SIN", "fpr-demand", ["search_cache_content"]),
    ("User profile for user 12345", "fpr-demand", ["search_user_profile"]),
    ("Active promo labels for GA", "fpr-demand", ["search_promo_labels"]),
    ("Booking log for order XYZ", "fpr-demand", ["get_booking_log"]),

    # Config
    ("Is feature X enabled?", "fpr-config", ["get_feature_flags"]),
    ("Who changed the pricing rule yesterday?", "fpr-config", ["get_activity_log"]),
    ("List all airline codes", "fpr-config", ["get_airline_ids"]),
    ("Convert 100 IDR to THB", "fpr-config", ["convert_currency"]),
    ("Show condition group rules", "fpr-config", ["load_condition_groups"]),
]


def load_skills():
    """Load all domain skills with their routing guides."""
    skills = {}
    for skill_path in Path(SKILLS_DIR).rglob("SKILL.md"):
        with open(skill_path) as f:
            content = f.read()
        # Extract name from frontmatter
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        if not name.startswith("fpr-") or name in ("fpr-shared", "fpr-skill-maker"):
            continue
        skills[name] = content
    return skills


def find_best_skill(prompt, skills):
    """Simple keyword matching against routing guides. Returns (skill_name, matched_ops)."""
    prompt_lower = prompt.lower()
    best_skill = None
    best_ops = []
    best_score = 0

    for skill_name, content in skills.items():
        # Extract routing guide entries
        routes = re.findall(r'\|\s*"([^"]+)".*?\|\s*`(\w+)`', content)
        score = 0
        matched_ops = []
        for keywords, op in routes:
            # Check if any keyword phrase matches
            for kw in keywords.split('", "'):
                if kw.lower() in prompt_lower:
                    score += 1
                    if op not in matched_ops:
                        matched_ops.append(op)

        if score > best_score:
            best_score = score
            best_skill = skill_name
            best_ops = matched_ops

    return best_skill, best_ops


def main(skills, mode="keyword"):
    print("FPR Skill Accuracy Eval\n")
    print(f"Test cases: {len(TEST_CASES)}\n")

    print(f"Loaded {len(skills)} domain skills: {', '.join(sorted(skills.keys()))}\n")

    correct_skill = 0
    correct_op = 0
    results = []

    for prompt, expected_skill, expected_ops in TEST_CASES:
        predicted_skill, predicted_ops = find_best_skill(prompt, skills)

        skill_match = predicted_skill == expected_skill
        op_match = any(op in predicted_ops for op in expected_ops) if predicted_ops else False

        if skill_match:
            correct_skill += 1
        if op_match:
            correct_op += 1

        status = "✅" if (skill_match and op_match) else "⚠️ " if skill_match else "❌"
        results.append({
            "status": status,
            "prompt": prompt,
            "expected": f"{expected_skill} → {expected_ops[0]}",
            "predicted": f"{predicted_skill} → {predicted_ops[0] if predicted_ops else 'none'}",
        })

    # Print results
    for r in results:
        print(f"  {r['status']} {r['prompt'][:50]}")
        if r['status'] != "✅":
            print(f"      expected: {r['expected']}")
            print(f"      got:      {r['predicted']}")

    total = len(TEST_CASES)
    print(f"\n{'─' * 50}")
    print(f"Skill routing:    {correct_skill}/{total} ({100*correct_skill//total}%)")
    print(f"Operation match:  {correct_op}/{total} ({100*correct_op//total}%)")
    print(f"Full accuracy:    {sum(1 for r in results if r['status']=='✅')}/{total} ({100*sum(1 for r in results if r['status']=='✅')//total}%)")

    # Save results as JSON for CI
    output_path = "tests/eval/results.json"
    with open(output_path, "w") as f:
        json.dump({
            "mode": mode,
            "total": total,
            "skill_accuracy": correct_skill / total,
            "operation_accuracy": correct_op / total,
            "full_accuracy": sum(1 for r in results if r['status'] == '✅') / total,
            "cases": results
        }, f, indent=2)
    print(f"\nResults saved to {output_path}")

    sys.exit(0 if correct_skill / total >= 0.8 else 1)


# ─── LLM Eval Mode ───────────────────────────────────────────────────────────

def llm_eval(skills):
    """Run eval using Gemini to simulate real AI routing decisions."""
    import urllib.request

    # Build skill context (what AI sees)
    skill_summaries = []
    for name, content in sorted(skills.items()):
        # Extract description from frontmatter
        desc_match = re.search(r'^description:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
        desc = desc_match.group(1) if desc_match else ""
        # Extract operations table
        ops_match = re.search(r'## Operations\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        ops_table = ops_match.group(1).strip() if ops_match else ""
        skill_summaries.append(f"### {name}\n{desc}\n\n{ops_table}")

    skill_context = "\n\n".join(skill_summaries)

    system_prompt = f"""You are an AI agent with access to FPR (Flight Pricing & Revenue) skills.
Given a user prompt, you must decide:
1. Which skill to use (skill name)
2. Which operation to call (operation name)

Available skills and their operations:

{skill_context}

Respond ONLY in this exact JSON format, no markdown:
{{"skill": "fpr-pricing", "operation": "load_autopilot_rules"}}"""

    print("FPR Skill Accuracy Eval (LLM mode — Gemini)\n")
    print(f"Test cases: {len(TEST_CASES)}")
    print(f"Model: {GEMINI_MODEL}")
    print(f"Endpoint: {GEMINI_ENDPOINT}\n")

    correct_skill = 0
    correct_op = 0
    results = []

    for i, (prompt, expected_skill, expected_ops) in enumerate(TEST_CASES):
        # Call Gemini
        body = json.dumps({
            "model": GEMINI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 100
        }).encode()

        req = urllib.request.Request(
            f"{GEMINI_ENDPOINT}/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GEMINI_API_KEY}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            answer_text = result["choices"][0]["message"]["content"].strip()
            # Parse JSON response
            answer = json.loads(answer_text)
            predicted_skill = answer.get("skill", "")
            predicted_op = answer.get("operation", "")
        except Exception as e:
            predicted_skill = f"ERROR: {e}"
            predicted_op = ""

        skill_match = predicted_skill == expected_skill
        op_match = predicted_op in expected_ops

        if skill_match:
            correct_skill += 1
        if op_match:
            correct_op += 1

        status = "✅" if (skill_match and op_match) else "⚠️ " if skill_match else "❌"
        results.append({
            "status": status,
            "prompt": prompt,
            "expected": f"{expected_skill} → {expected_ops[0]}",
            "predicted": f"{predicted_skill} → {predicted_op}",
        })

        # Progress indicator
        print(f"  [{i+1}/{len(TEST_CASES)}] {status} {prompt[:50]}")
        if status != "✅":
            print(f"        expected: {expected_skill} → {expected_ops[0]}")
            print(f"        got:      {predicted_skill} → {predicted_op}")

    total = len(TEST_CASES)
    print(f"\n{'─' * 50}")
    print(f"Skill routing:    {correct_skill}/{total} ({100*correct_skill//total}%)")
    print(f"Operation match:  {correct_op}/{total} ({100*correct_op//total}%)")
    print(f"Full accuracy:    {sum(1 for r in results if r['status']=='✅')}/{total} ({100*sum(1 for r in results if r['status']=='✅')//total}%)")

    # Save results
    output_path = "tests/eval/results-llm.json"
    with open(output_path, "w") as f:
        json.dump({
            "mode": "llm",
            "model": GEMINI_MODEL,
            "total": total,
            "skill_accuracy": correct_skill / total,
            "operation_accuracy": correct_op / total,
            "full_accuracy": sum(1 for r in results if r['status'] == '✅') / total,
            "cases": results
        }, f, indent=2)
    print(f"\nResults saved to {output_path}")

    sys.exit(0 if correct_skill / total >= 0.8 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FPR Skill Accuracy Eval")
    parser.add_argument("--llm", action="store_true", help="Use Gemini LLM for eval (slower, more accurate)")
    args = parser.parse_args()

    skills = load_skills()

    if args.llm:
        llm_eval(skills)
    else:
        main(skills)
