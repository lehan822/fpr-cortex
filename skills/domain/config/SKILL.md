---
name: fpr-config
description: "Feature flags, audit/activity logs, condition groups, currency conversion, country/airline lists. Use for cross-team configuration queries and change auditing."
version: "2.2.0"
category: domain
domain: config
prerequisites:
  local: [fpr-shared]
  agentcore: []
tools:
  - get_activity_log
  - get_airline_ids
  - get_countries
  - get_feature_flags
  - get_flag_applications
  - get_flag_configuration
  - load_condition_groups
  - convert_currency
---

# FPR Config

## Prerequisites — Read Before Executing

1. **Local MCP only** → read **fpr-shared** first (auth, tool name prefix, request envelope)
2. **Querying feature flags** → MUST read [`feature-flags.md`](references/feature-flags.md) (appName mapping, flag state interpretation)

**Executing operations without reading the required references will lead to parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `get_feature_flags` | Feature flag status by app | appName |
| `get_flag_applications` | List apps using feature flags | — |
| `get_flag_configuration` | Detailed flag config & history | appName, flagName |
| `load_condition_groups` | Condition group rules | conditionGroupId |
| `get_activity_log` | Change audit trail | entityType, startDate, endDate |
| `get_airline_ids` | All IATA airline codes | — |
| `get_countries` | Supported country list | — |
| `convert_currency` | Currency conversion | sourceCurrency, targetCurrency, amount |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "feature flag", "is X enabled" | `get_feature_flags` |
| "which apps use flags" | `get_flag_applications` |
| "flag detail", "flag config" | `get_flag_configuration` |
| "condition group", "rule conditions" | `load_condition_groups` |
| "audit log", "who changed", "change history" | `get_activity_log` |
| "airline list", "airline codes" | `get_airline_ids` |
| "country list", "supported countries" | `get_countries` |
| "convert currency", "IDR to VND" | `convert_currency` |

## Activity Log Filters

`get_activity_log` supports filtering by:
- `entityType`: "PRICING_RULE", "FEATURE_FLAG", "CONDITION_GROUP", "BUDGET", "PROVIDER"
- `startDate` / `endDate`: ISO date strings
- `userId`: who made the change

## Disambiguation

- "commission" → **fpr-pricing** (not config)
- "fare adjuster" → **fpr-supply** (not config)
- "booking detail" → **fpr-demand** (not config)
- "exchange rate" for pricing → **fpr-pricing**; for FX conversion → `convert_currency`
