---
name: fpr-config
description: "fpr-cli config domain: feature flags, audit/activity logs, condition groups, currency conversion, country/airline lists. Use for cross-team configuration queries and change auditing."
version: "2.0.0"
domain: config
prerequisites:
  - fpr-shared
---

# FPR Config

> ⚠️ **Read [fpr-shared](../shared/SKILL.md) first** — it covers authentication, Gateway URL, and parameter standards.

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
