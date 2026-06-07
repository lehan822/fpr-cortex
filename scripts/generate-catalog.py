#!/usr/bin/env python3
"""Generate docs/operation-catalog.md from schema + skills."""
import json, os

SCHEMA_PATH = "infra/schemas/fprtool-full.json"
SKILLS_DIR = "skills"
OUTPUT_PATH = "docs/operation-catalog.md"

with open(SCHEMA_PATH) as f:
    schema = json.load(f)

all_ops = {}
for path, methods in schema.get("paths", {}).items():
    for method, detail in methods.items():
        if "operationId" in detail:
            desc = detail.get("summary", detail.get("description", "")).split("\n")[0][:80]
            all_ops[detail["operationId"]] = desc

domains = [d for d in os.listdir(SKILLS_DIR)
           if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
           and d not in ("shared", "skill-maker")]

domain_ops = {}
for domain in domains:
    with open(os.path.join(SKILLS_DIR, domain, "SKILL.md")) as f:
        content = f.read()
    domain_ops[domain] = [op for op in all_ops if op in content]

lines = [
    "# Operation Catalog",
    "",
    "> Auto-generated — do not edit manually.",
    "> Run: `python scripts/generate-catalog.py`",
    "",
    f"**Total: {len(all_ops)} operations**",
    "",
    "| operationId | Description | Domain |",
    "|---|---|---|",
]

for op_id in sorted(all_ops.keys()):
    owner = "❌ unclaimed"
    for domain, ops in domain_ops.items():
        if op_id in ops:
            owner = domain
            break
    lines.append(f"| `{op_id}` | {all_ops[op_id]} | {owner} |")

claimed = len(set(op for ops in domain_ops.values() for op in ops))
lines += ["", "## Summary", "", f"- **Claimed:** {claimed}/{len(all_ops)}", f"- **Unclaimed:** {len(all_ops) - claimed}", ""]
for domain in sorted(domain_ops):
    lines.append(f"- **{domain}:** {len(domain_ops[domain])} ops")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"✅ Generated {OUTPUT_PATH} ({len(all_ops)} ops, {claimed} claimed)")
