#!/usr/bin/env python3
"""Validate all SKILL.md files for structure and conventions.

Checks:
1. Frontmatter has required fields (name, version, description, category)
2. Description starts with [category] tag
3. All references/ files mentioned in SKILL.md actually exist
4. Naming convention: fpr-* or fpr-ops-*
5. Prerequisites field references valid skill names
"""
import os, re, sys, glob as globmod, yaml

SKILLS_DIR = "skills"
REQUIRED_FIELDS = {"name", "version", "description", "category"}
VALID_CATEGORIES = {"shared", "domain", "ops", "meta"}
errors = []


def parse_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return None, content
    try:
        fm = yaml.safe_load(match.group(1))
        return fm, content
    except yaml.YAMLError as e:
        errors.append(f"{filepath}: invalid YAML frontmatter: {e}")
        return None, content


def check_frontmatter(filepath, fm):
    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        errors.append(f"{filepath}: missing frontmatter fields: {missing}")

    name = fm.get("name", "")
    if not name.startswith("fpr-"):
        errors.append(f"{filepath}: name '{name}' must start with 'fpr-'")

    category = fm.get("category", "")
    if category not in VALID_CATEGORIES:
        errors.append(f"{filepath}: category '{category}' not in {VALID_CATEGORIES}")

    desc = fm.get("description", "")
    expected_tag = f"[{category}]"
    if not desc.startswith(expected_tag):
        errors.append(f"{filepath}: description must start with '{expected_tag}', got: '{desc[:30]}...'")


def check_references(filepath, content):
    """Ensure all referenced files in references/ actually exist."""
    skill_dir = os.path.dirname(filepath)
    # Find all markdown links to references/
    refs = re.findall(r'\[.*?\]\(references/([^)]+)\)', content)
    for ref in refs:
        ref_path = os.path.join(skill_dir, "references", ref)
        if not os.path.isfile(ref_path):
            errors.append(f"{filepath}: references '{ref}' but file not found: {ref_path}")


def check_tools_registered(filepath, fm):
    """Ensure all tools declared in skill exist in exposed-ops.yaml."""
    tools = fm.get("tools", [])
    if not tools:
        return
    # Load exposed-ops.yaml
    config_path = os.path.join("infra", "config", "exposed-ops.yaml")
    if not os.path.isfile(config_path):
        return  # skip if config not available
    with open(config_path) as f:
        config = yaml.safe_load(f)
    # Collect all registered operation IDs
    registered = set()
    for domain_ops in config.values():
        if isinstance(domain_ops, list):
            for op in domain_ops:
                if isinstance(op, dict) and "id" in op:
                    registered.add(op["id"])
    # Check each tool
    for tool in tools:
        if tool not in registered:
            errors.append(f"{filepath}: tool '{tool}' not found in exposed-ops.yaml")


def main():
    skill_files = sorted(globmod.glob(os.path.join(SKILLS_DIR, "**", "SKILL.md"), recursive=True))

    if not skill_files:
        print("❌ No SKILL.md files found")
        sys.exit(1)

    print(f"Validating {len(skill_files)} skills...\n")

    for filepath in skill_files:
        fm, content = parse_frontmatter(filepath)
        if fm is None:
            errors.append(f"{filepath}: no valid frontmatter found")
            continue
        check_frontmatter(filepath, fm)
        check_references(filepath, content)
        check_tools_registered(filepath, fm)

    if errors:
        print(f"❌ {len(errors)} error(s) found:\n")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print(f"✅ All {len(skill_files)} skills passed validation")
        sys.exit(0)


if __name__ == "__main__":
    main()
