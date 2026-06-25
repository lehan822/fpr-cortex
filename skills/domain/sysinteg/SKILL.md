---
name: fpr-sysinteg
version: 1.0.0
description: "[domain] System integration tools: feature flags, audit logs, configuration management, currency conversion, reference data (countries, airlines). Use for cross-team configuration queries and change auditing."
category: domain
prerequisites:
  local: [fpr-shared]
  agentcore: []
---

# FPR SysInteg (System Integration)

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-shared — read it first (see Prerequisites).**

```
# Common examples
tool: get_feature_flags           data: {appName: "fprbopi"}
tool: get_flag_configuration      data: {appName: "fprbopi", flagName: "enable-new-pricing"}
tool: get_activity_log            data: {entityType: "PRICING_RULE", startDate: "2026-01-01", endDate: "2026-01-31"}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (appName mapping, entityType enum)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `get_flag_applications` | List apps using feature flags | — |
| `get_feature_flags` | Feature flag status by app | appName |
| `get_flag_configuration` | Detailed flag config & history | appName, flagName |
| `get_activity_log` | Change audit trail | entityType, startDate, endDate |
| `get_decompressed_object` | Get decompressed object from S3 | key |
| `load_condition_groups` | Condition group rules | conditionGroupId |
| `get_airline_ids` | All IATA airline codes | — |
| `get_countries` | Supported country list | — |
| `convert_currency` | Currency conversion | sourceCurrency, targetCurrency, amount |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "feature flag", "is X enabled", "toggle" | `get_feature_flags` |
| "which apps use flags" | `get_flag_applications` |
| "flag detail", "flag config" | `get_flag_configuration` |
| "condition group", "rule conditions" | `load_condition_groups` |
| "audit log", "who changed", "change history" | `get_activity_log` |
| "airline list", "airline codes" | `get_airline_ids` |
| "country list", "supported countries" | `get_countries` |
| "convert currency", "IDR to VND" | `convert_currency` |

## Gotchas (top traps — full rules in references)

- **appName mapping** — use `fprbopi` (not `fpr-bopi`, not `FlightBookingPricing`); see [parameter-standards.md](references/parameter-standards.md)
- **Flag state interpretation** — `true` / `false` / percentage rollout
- **Activity log entityType** — must be one of `PRICING_RULE`, `FEATURE_FLAG`, `CONDITION_GROUP`, `BUDGET`, `PROVIDER`

## Activity Log Filters

`get_activity_log` supports filtering by:
- `entityType`: "PRICING_RULE", "FEATURE_FLAG", "CONDITION_GROUP", "BUDGET", "PROVIDER"
- `startDate` / `endDate`: ISO date strings
- `userId`: who made the change

## Disambiguation

- "commission", "budget", "markup" → **fpr-pricing** (not sysinteg)
- "fare adjuster", "provider config" → **fpr-supply** (not sysinteg)
- "booking detail", "PNR lookup" → **fpr-demand** (not sysinteg)
- "exchange rate" for pricing → **fpr-pricing**; for FX conversion → `convert_currency`
