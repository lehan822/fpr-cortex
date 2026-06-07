---
name: fpr-skill-maker
version: "1.0.0"
description: "Help domain owners create, validate, and iterate on FPR skills. Works for engineers and non-technical product managers alike."
---

# FPR Skill Maker

> Help domain owners create and maintain FPR skills. No code required — conversational authoring.

## Activation

Activate when user says:
- "help me write a skill", "create new skill", "new domain"
- "check/validate my skill"
- "add an operation to skill"

## Workflow

### 1. Gather Information (Conversational)

Ask one question at a time:

1. **Domain name** — What area does this skill cover? (e.g. inventory, routing, settlement)
2. **Operations** — Which operations to include? (user lists them, or auto-extract from schema)
3. **User intents** — How do users typically ask? (natural language → tool mapping)
4. **Key parameters** — What inputs does each operation need?

For product managers: ask in plain language, no need to know operationId.
For engineers: can give operationId list directly, skip intent collection.

### 2. Extract from Schema

Read the schema file from the fpr-cortex repo to validate and supplement:

```bash
# Find the schema in the fpr-cortex repo (wherever it's cloned)
find ~ -path "*/fpr-cortex/infra/schemas/fprtool-full.json" -print -quit 2>/dev/null
```

If not found locally, fetch from GitHub:
```bash
curl -sf https://raw.githubusercontent.com/lehan822/fpr-cortex/main/infra/schemas/fprtool-full.json
```

Extract from schema:
- operationId exists ✅/❌
- Each operation's requestBody parameters (inside `data`)
- Each operation's description

### 3. Generate SKILL.md

Follow [template.md](references/template.md) format. Key rules:

- Operations table must include: operationId, description, key parameters
- Routing Guide must cover all operations (at least one intent mapping each)
- Must include prefix reminder (see template)
- Parameter normalization table should list common user input → normalized value

### 4. Validate

Run checks after generation (see [validation-rules.md](references/validation-rules.md)):

- [ ] All operationIds exist in schema
- [ ] Each operation has at least one intent mapping
- [ ] Parameter names match schema
- [ ] Required frontmatter complete (name, version, description, domain, prerequisites)
- [ ] Includes prefix + data envelope reminder
- [ ] Complex operations have references/ docs

### 5. Output

Write generated files to:
```
skills/<domain>/SKILL.md
skills/<domain>/references/  (for complex operations)
```

Tell user:
> ✅ Skill generated at `skills/<domain>/SKILL.md`. Please review and commit.

## Add Operation

When user says "add an operation to XX skill":
1. Read existing SKILL.md
2. Extract new operation info from schema
3. Append to Operations table and Routing Guide
4. Re-validate

## Update Existing Skill

Supported update scenarios:

| User says | Action |
|-----------|--------|
| "add a new operation" | Append to Operations table + Routing Guide |
| "change description/intent for XX" | Locate row, modify in place |
| "remove XX operation" | Remove from Operations + Routing Guide, check if references need deletion |
| "check/validate skill" | Run validation-rules, output results |
| "bump version" | Bump version, verify all changes are consistent |
| "schema updated, help me sync" | Compare schema vs skill, list diffs, confirm each update |

### Schema Sync Flow

When backend adds new APIs or changes parameters:

1. Read latest `infra/schemas/fprtool-full.json`
2. Compare operations listed in skill vs schema operations for that domain
3. Output diff report:
   - 🆕 In schema but not in skill
   - ⚠️ Parameter names changed
   - 🗑️ In skill but deleted from schema
4. Ask user to confirm each update
5. Re-validate after updates

## Common Issues

| Situation | Action |
|-----------|--------|
| operationId not in schema | Tell user: operation not yet registered in fprtool-backend, backend team needs to add it first |
| User gives description but doesn't know operationId | Search schema for matching description, recommend candidates |
| Cross-domain operation | Suggest placing in most relevant domain, note in Disambiguation section |
