---
name: fpr-skill-maker
version: "1.0.0"
description: "Help domain owners create, validate, and iterate on FPR skills. Works for engineers and non-technical product managers alike."
---

# FPR Skill Maker

> 帮助 domain owner 创建和维护 FPR skills。无需写代码，对话式完成。

## 触发条件

当用户说以下内容时激活此 skill：
- "帮我写一个 skill"、"创建新 skill"、"新建 domain"
- "检查/验证我的 skill"
- "给 skill 加一个新 operation"

## 工作流程

### 1. 收集信息（对话式）

逐步询问，一次一个问题：

1. **Domain 名称** — 这个 skill 覆盖什么领域？（如 inventory、routing、settlement）
2. **Operations** — 包含哪些操作？（让用户列出，或从 schema 自动提取）
3. **用户意图** — 用户通常怎么问？（自然语言 → 工具映射）
4. **关键参数** — 每个操作需要什么输入？

对于产品经理：用简单中文提问，不要求知道 operationId。
对于工程师：可以直接给 operationId 列表，跳过意图收集。

### 2. 从 Schema 提取信息

读取本地 schema 文件验证和补充信息：

```bash
cat ~/IdeaProjects/pricing/fpr-cortex/infra/schemas/fprtool-full.json
```

从 schema 中提取：
- operationId 是否存在 ✅/❌
- 每个 operation 的 requestBody 参数（在 `data` 里）
- 每个 operation 的 description

### 3. 生成 SKILL.md

按照 [template.md](references/template.md) 格式生成。关键规则：

- Operations 表必须包含：operationId、描述、关键参数
- Routing Guide 必须覆盖所有 operation（至少一个意图映射）
- 必须包含前缀提醒（见模板）
- 参数标准化表要列出常见的用户输入→规范值映射

### 4. 验证

生成后自动检查（见 [validation-rules.md](references/validation-rules.md)）：

- [ ] 所有 operationId 在 schema 中存在
- [ ] 每个 operation 有至少一个意图映射
- [ ] 参数名和 schema 一致
- [ ] 必填 frontmatter 齐全（name, version, description, domain, prerequisites）
- [ ] 包含前缀 + data 信封提醒
- [ ] references/ 对复杂操作有补充文档

### 5. 输出

将生成的文件写入：
```
skills/<domain>/SKILL.md
skills/<domain>/references/  (如有复杂操作)
```

告知用户：
> ✅ Skill 已生成在 `skills/<domain>/SKILL.md`。请 review 后 commit。

## 追加操作

用户说"给 XX skill 加一个 operation"时：
1. 读取现有 SKILL.md
2. 从 schema 提取新 operation 信息
3. 追加到 Operations 表和 Routing Guide
4. 重新验证

## 常见问题处理

| 情况 | 处理 |
|------|------|
| operationId 不在 schema 里 | 提醒用户：该操作尚未在 fprtool-backend 注册，需要先让后端团队添加 |
| 用户给了中文描述但不知道 operationId | 在 schema 中搜索匹配的 description，推荐候选 |
| 跨 domain 的操作 | 建议放在最相关的 domain，并在 Disambiguation 里注明 |
