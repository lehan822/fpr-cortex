# SKILL.md 模板

以下是生成 domain skill 时使用的标准模板。用 `{{}}` 标记需要填充的内容。

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

## 模板填充规则

1. **Operations 表**
   - 每行一个 operationId
   - Description 从 schema 的 summary/description 提取，精简到 10 字以内
   - Key Parameters 只列 `data` 里最重要的 2-3 个参数

2. **Routing Guide**
   - 每个 operation 至少一个意图映射
   - 用用户实际会说的话（中文/英文混合 OK）
   - 高频操作可以有多个意图映射

3. **Parameter Normalization**
   - 列出用户可能输入的非标准格式
   - 如：用户说"印尼" → normalize 为 `"ID"`

4. **Disambiguation**
   - 列出容易混淆的术语
   - 指向正确的 domain skill
