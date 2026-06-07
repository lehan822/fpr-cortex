# Skill Validation Rules

After generating or modifying a skill, check each item against the following rules.

## Must Pass (❌ = Blocking)

### 1. Domain Ownership (exposed-ops.yaml)
- Each operationId in the skill MUST be listed under that domain in `infra/config/exposed-ops.yaml`
- If an operation is not listed there, it either belongs to a different domain or hasn't been approved for exposure
- To add a new operation: submit a PR to `exposed-ops.yaml` (requires review)

### 2. Schema Consistency
- Each operationId must exist in the `paths` of `infra/schemas/fprtool-full.json`
- Parameter names must match the schema's `requestBody.properties.data.properties`
- Validation: cross-reference exposed-ops.yaml → schema → skill

### 2. Frontmatter Completeness
Must include:
```yaml
name: fpr-<domain>       # Must start with fpr-
description: "..."       # Non-empty
version: "x.y.z"        # semver
domain: <domain>         # Must match the directory name
prerequisites:
  - fpr-shared           # Must depend on shared
```

### 3. Structural Completeness
- [ ] Includes an "Operations" table (at least 1 row)
- [ ] Includes a "Routing Guide" table (covers each operation at least once)
- [ ] Includes the prefix + data envelope reminder (⚠️ section)
- [ ] Includes the fpr-shared link

### 4. Naming Conventions
- File path: `skills/<domain>/SKILL.md`
- The domain name may contain only lowercase letters + hyphens
- operationId uses snake_case

## Recommended to Pass (⚠️ = Warning)

### 5. Coverage
- The number of operations listed in the Operations table should be ≥ 3 (if too few, consider merging into another domain)
- Routing Guide row count should be ≥ Operations row count (at least one intent per op)

### 6. Usability
- Has a "Parameter Normalization" section (helps AI understand non-standard input)
- Has a "Disambiguation" section (avoids confusion with other domains)
- Has a "Common Codes" section (lists commonly used codes in the domain)

### 7. References
- For complex operations with more than 5 parameters, a detailed `references/<operation>.md` is recommended
- For operations involving multi-step workflows, a workflow reference is recommended

## Validation Output Format

```
✅ Schema check: 5/5 operations found
✅ Frontmatter: complete
✅ Structure: all sections present
⚠️ Coverage: get_inventory_types has no routing guide entry
⚠️ References: get_inventory_detail has 7 params, consider adding reference doc

Result: PASS (2 warnings)
```
