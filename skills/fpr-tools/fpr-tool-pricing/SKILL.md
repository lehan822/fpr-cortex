---
name: fpr-tool-pricing
version: 2.6.0
description: "[fprtool] Pricing rules, autopilot rules, budgets, commissions, incentives, baseline markup, bundling, transaction fees. Use for price adjustments, margin settings, and revenue management."
category: fprtool
prerequisites:
  local: [fpr-tool-shared]
  agentcore: []
---

# FPR Pricing

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-tool-shared — read it first (see Prerequisites).**

```
# Common examples
tool: load_autopilot_rules               data: {profileGroup: "TRAVELOKA", profileType: "DEFAULT", productType: "STANDALONE", profileName: "DEFAULT", currency: "THB"}
tool: get_budget_balance                 data: {currency: "THB"}
tool: load_commission_incentive_rules    data: {airlineId: "GA", fulfillmentId: "amadeus"}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-tool-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Autopilot (5-field S3-key) or baseline (route-based)** → MUST read [`autopilot-operations.md`](references/autopilot-operations.md)
3. **Querying or updating commission / incentive** → MUST read [`commission-operations.md`](references/commission-operations.md)
4. **Querying budget** → MUST read [`budget-operations.md`](references/budget-operations.md)
5. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (profileGroup enum, originCountry distinction, ISO/IATA normalization)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Pricing Rules** |||
| `load_autopilot_rules` | Automated pricing rules by profile+currency | profileGroup, profileType, productType, profileName, currency |
| `update_autopilot_rules` | Update/create autopilot rules (conditions + adjustments) ⚠️ complex | autopilotToolData, version, notes |
| `load_baseline_pricing_rules` | Base markup/margin rules (route-based) | profileGroup, originCountry, destinationCountry, airlineId |
| `load_bundling_pricing_rules` | Bundle pricing (flight+hotel) | profileGroup, profileType, productType, profileName, currency |
| `load_price_prediction_rules` | Anchor fare / dynamic pricing rules | profileGroup |
| `load_price_cut_modifier_rules` | Price cut / promo modifiers | profileGroup |
| `load_trx_fee_rules` | Transaction/service fee rules | profileGroup |
| `load_pricing_profiles` | Pricing profile names | profileGroup |
| `load_issuance_fee_rules` | Ticket issuance fees | fulfillmentId |
| **Budget Management** |||
| `get_budget_balance` | Budget remaining/used by currency | currency |
| `list_active_budgets` | Active budgets by currency and level | currency |
| `get_budget_levels` | Budget level types | — |
| `get_budget_user_balance` | User-level budget balance | currency |
| **Commission & Incentives** |||
| `load_commission_incentive_rules` | Commission rates for airline partners | airlineId, fulfillmentId |
| `load_commission_incentive_profiles` | Commission profile list | — |
| `load_tiered_incentive_rules` | Volume-based incentive tiers | brandId |
| `check_tiered_incentive_progress` | PNR incentive progress check | pnr |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "markup", "margin", "base pricing" | `load_baseline_pricing_rules` |
| "budget", "remaining budget", "budget left" | `get_budget_balance` |
| "commission", "airline commission rate" | `load_commission_incentive_rules` |
| "flash sale", "promo", "discount" | `load_price_cut_modifier_rules` |
| "bundle", "package", "flight+hotel" | `load_bundling_pricing_rules` |
| "autopilot", "automated pricing" | `load_autopilot_rules` |
| "update autopilot", "修改 autopilot" | `update_autopilot_rules` |
| "service fee", "transaction fee" | `load_trx_fee_rules` |
| "issuance fee", "ticketing fee" | `load_issuance_fee_rules` |
| "PNR", "incentive progress", "PNR check" | `check_tiered_incentive_progress` |
| "tiered incentive", "volume bonus" | `load_tiered_incentive_rules` |
| "anchor fare", "price prediction" | `load_price_prediction_rules` |

## Gotchas (top traps — full rules in references)

- **Parameter normalization & enums** (profileGroup is an enum not a country; ISO currency; IATA airline; commission needs airlineId + fulfillmentId) → [parameter-standards.md](references/parameter-standards.md)
- **Autopilot uses 5-field S3 key** (`profileGroup.profileType.productType.profileName.currency`); misordered fields → 500 error → [autopilot-operations.md](references/autopilot-operations.md)
- **Baseline is route-based** (profileGroup + originCountry + destinationCountry + airlineId); NOT the 5-field key → [autopilot-operations.md](references/autopilot-operations.md)

## Workflows

### Budget Health Check
1. `get_budget_balance` with currency — see remaining amount
2. `list_active_budgets` — check all active budgets for that currency
3. `get_budget_levels` — understand budget hierarchy if needed

### Pricing Rule Audit (by country)
1. `load_autopilot_rules` with originCountry — see dynamic rules
2. `load_baseline_pricing_rules` — compare with base markup
3. `load_price_cut_modifier_rules` — check if promo is active

### Commission Investigation
1. `load_commission_incentive_rules` with airlineId + fulfillmentId — get rates
2. `load_tiered_incentive_rules` with brandId — check volume tiers
3. `check_tiered_incentive_progress` with pnr — verify specific booking

### Update Rules ⚠️

**All update operations MUST follow this safety flow:**

1. **Load current** → `load_*_rules` → get baseline + `version` (optimistic lock)
2. **Search schema** → `x_amz_bedrock_agentcore_search(tool_name)` → get field structure
3. **Build payload** → assemble changes based on current rules + user request
4. **Call update** → submit (backend has approval flow built-in)

**All updates require loading current state first** — both for the `version` field and to understand existing rules before modifying.

## Disambiguation

- "fare adjuster" → **fpr-tool-supply** (not pricing)
- "feature flag" → **fpr-tool-sysinteg** (not pricing)
- "search cache", "booking detail" → **fpr-tool-demand** (not pricing)
