# Skill 验证规则

生成或修改 skill 后，按以下规则逐项检查。

## 必须通过（❌ = 阻塞）

### 1. Schema 一致性
- 每个 operationId 必须存在于 `infra/schemas/fprtool-full.json` 的 `paths` 中
- 参数名必须和 schema 的 `requestBody.properties.data.properties` 一致
- 验证方法：读取 schema，逐个 operationId 检查

### 2. Frontmatter 完整性
必须包含：
```yaml
name: fpr-<domain>       # 必须以 fpr- 开头
description: "..."       # 非空
version: "x.y.z"        # semver
domain: <domain>         # 和目录名一致
prerequisites:
  - fpr-shared           # 必须依赖 shared
```

### 3. 结构完整性
- [ ] 包含 "Operations" 表（至少 1 行）
- [ ] 包含 "Routing Guide" 表（至少覆盖每个 operation 一次）
- [ ] 包含前缀 + data 信封提醒（⚠️ 段落）
- [ ] 包含 fpr-shared 链接

### 4. 命名规范
- 文件路径：`skills/<domain>/SKILL.md`
- domain 名只能是小写字母 + 连字符
- operationId 使用 snake_case

## 建议通过（⚠️ = 警告）

### 5. 覆盖率
- Operations 表列出的 operation 数量 ≥ 3（太少考虑合并到其他 domain）
- Routing Guide 行数 ≥ Operations 行数（每个 op 至少一个意图）

### 6. 可用性
- 有 "Parameter Normalization" 段（帮助 AI 理解非标准输入）
- 有 "Disambiguation" 段（避免和其他 domain 混淆）
- 有 "Common Codes" 段（列出领域常用编码）

### 7. References
- 超过 5 个参数的复杂操作，建议有 `references/<operation>.md` 详细说明
- 涉及多步工作流的操作，建议有 workflow reference

## 验证输出格式

```
✅ Schema check: 5/5 operations found
✅ Frontmatter: complete
✅ Structure: all sections present
⚠️ Coverage: get_inventory_types has no routing guide entry
⚠️ References: get_inventory_detail has 7 params, consider adding reference doc

Result: PASS (2 warnings)
```
