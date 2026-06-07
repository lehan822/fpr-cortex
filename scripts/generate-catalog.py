#!/usr/bin/env python3
"""Generate docs/operation-catalog.md from schema(s) + skills."""
import json, os, glob as globmod

SCHEMAS_DIR = "infra/schemas"
SKILLS_DIR = "skills"
OUTPUT_PATH = "docs/operation-catalog.md"

# Load all *-full.json schemas
all_ops = {}  # operationId -> {desc, backend}
schema_files = sorted(globmod.glob(os.path.join(SCHEMAS_DIR, "*-full.json")))

for schema_file in schema_files:
    backend = os.path.basename(schema_file).replace("-full.json", "")
    with open(schema_file) as f:
        schema = json.load(f)
    for path, methods in schema.get("paths", {}).items():
        for method, detail in methods.items():
            if "operationId" in detail:
                desc = detail.get("summary", detail.get("description", "")).split("\n")[0][:80]
                all_ops[detail["operationId"]] = {"desc": desc, "backend": backend}

domains = {}
# Walk skills directory to find all SKILL.md files (supports nested structure)
for root, dirs, files in os.walk(SKILLS_DIR):
    if "SKILL.md" in files:
        rel = os.path.relpath(root, SKILLS_DIR)
        # Skip shared-layer skills (auth, skill-maker)
        if rel.startswith("shared"):
            continue
        domain_name = os.path.basename(root)
        with open(os.path.join(root, "SKILL.md")) as f:
            content = f.read()
        domains[domain_name] = [op for op in all_ops if op in content]

domain_ops = domains

backends = sorted(set(v["backend"] for v in all_ops.values()))
multi_backend = len(backends) > 1

lines = [
    "# Operation Catalog",
    "",
    "> Auto-generated — do not edit manually.",
    "> Run: `python scripts/generate-catalog.py`",
    "",
    f"**Total: {len(all_ops)} operations** across {len(backends)} backend(s): {', '.join(backends)}",
    "",
]

if multi_backend:
    lines.append("| operationId | Description | Backend | Domain |")
    lines.append("|---|---|---|---|")
else:
    lines.append("| operationId | Description | Domain |")
    lines.append("|---|---|---|")

for op_id in sorted(all_ops.keys()):
    info = all_ops[op_id]
    owners = [domain for domain, ops in domain_ops.items() if op_id in ops]
    owner_str = ", ".join(sorted(owners)) if owners else "❌ unclaimed"
    if multi_backend:
        lines.append(f"| `{op_id}` | {info['desc']} | {info['backend']} | {owner_str} |")
    else:
        lines.append(f"| `{op_id}` | {info['desc']} | {owner_str} |")

claimed = len(set(op for ops in domain_ops.values() for op in ops))
lines += ["", "## Summary", "", f"- **Claimed:** {claimed}/{len(all_ops)}", f"- **Unclaimed:** {len(all_ops) - claimed}", ""]
if multi_backend:
    for b in backends:
        count = sum(1 for v in all_ops.values() if v["backend"] == b)
        lines.append(f"- **{b}:** {count} ops")
    lines.append("")
for domain in sorted(domain_ops):
    lines.append(f"- **{domain}:** {len(domain_ops[domain])} ops")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"✅ Generated {OUTPUT_PATH} ({len(all_ops)} ops, {claimed} claimed)")
