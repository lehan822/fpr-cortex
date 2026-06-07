# SKILL.md Template

Below is the standard template used when generating a domain skill. Use `{{}}` to mark content that needs to be filled in.

---

```markdown
---
name: fpr-{{domain}}
description: "fpr-cli {{domain}} domain: {{one-line description}}. Use when {{triggering scenarios}}."
version: "1.0.0"
domain: {{domain}}
prerequisites:
  - fpr-shared
---

# FPR {{Domain Title}}

> ⚠️ **Read [fpr-shared](../shared/SKILL.md) first** — it covers authentication, Gateway URL, and parameter standards.
>
> ⚠️ **Tool name prefix required:** When calling `tools/call`, prepend `fprtool-backend___` to every operation name below. Params go inside `data:{}` envelope. See fpr-shared for full request format.

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `{{operationId}}` | {{description}} | {{param1, param2}} |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "{{natural language phrase}}" | `{{operationId}}` |

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| {{param}} | "{{user input example}}" | `"{{normalized value}}"` |

## Common Codes

{{List frequently used code mappings relevant to this domain}}

## Disambiguation

- "{{confusing term}}" → **fpr-{{other-domain}}** (not {{this domain}})
```

---

## Template Filling Rules

1. **Operations Table**
   - One operationId per row
   - Extract Description from the schema's summary/description and keep it within 10 words
   - Key Parameters should list only the 2-3 most important parameters inside `data`

2. **Routing Guide**
   - At least one intent mapping for each operation
   - Use phrases users would actually say (Chinese/English mixed is OK)
   - High-frequency operations can have multiple intent mappings

3. **Parameter Normalization**
   - List non-standard formats users may input
   - Example: user says "Indonesia" → normalize to `"ID"`

4. **Disambiguation**
   - List terms that are easy to confuse
   - Point to the correct domain skill
