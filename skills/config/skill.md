---
name: fpr-config
description: Query FPR system configuration — feature flags, condition groups, airline/country reference data, currency conversion, and audit logs
version: "1.0.0"
domain: flight-config
---

# FPR Config Skill

System-level configuration and reference data tools for Traveloka's Flight Pricing & Revenue platform.

## Available Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `get_feature_flags` | Get feature flag status | appName |
| `get_flag_applications` | List apps using feature flags | (none) |
| `get_flag_configuration` | Detailed flag config | appName, flagName |
| `load_condition_groups` | Load condition group rules | conditionGroupId |
| `get_activity_log` | Audit/activity log for changes | entityType, startDate, endDate |
| `get_airline_ids` | List all IATA airline codes | (none) |
| `get_countries` | List all supported countries | (none) |
| `convert_currency` | Convert amount between currencies | sourceCurrency, targetCurrency, amount |

## Routing Guide

- "feature flag", "flag status", "is feature enabled" → `get_feature_flags`
- "which apps", "flag applications" → `get_flag_applications`
- "flag detail", "flag configuration" → `get_flag_configuration`
- "condition group", "rule conditions" → `load_condition_groups`
- "audit log", "change history", "who changed" → `get_activity_log`
- "airline list", "airline codes", "all airlines" → `get_airline_ids`
- "country list", "supported countries" → `get_countries`
- "convert currency", "exchange rate", "IDR to VND" → `convert_currency`

## Disambiguation

- "commission" without "hotel" → use **fpr-pricing** `load_commission_incentive_rules`, NOT config tools
- "pricing rules" → use **fpr-pricing** tools, NOT `get_feature_flags`
- "fare check" → use **fpr-supply** `check_fare`, NOT `convert_currency`
- "exchange rate" for FX conversion → `convert_currency`; for pricing adjustment → **fpr-pricing** tools
