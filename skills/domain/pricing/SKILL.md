---
name: fpr-pricing
description: "Pricing rules (autopilot, baseline, commission, budget). Use when querying flight pricing configuration, markup/margin rules, budget balances, or airline commission rates. NOT for fare adjuster (→ fpr-supply), feature flags (→ fpr-config), or booking data (→ fpr-demand)."
metadata:
  requires:
    skills: ["fpr-shared"]
---

# FPR Pricing

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-shared — read it first (see Prerequisites).**

```
# Common examples — profileName is ALWAYS "DEFAULT" for B2C (never the country code)
tool: load_autopilot_rules   data: {profileGroup: "TRAVELOKA", profileType: "DEFAULT", productType: "STANDALONE", profileName: "DEFAULT", currency: "THB"}  # Thailand B2C
tool: load_autopilot_rules   data: {profileGroup: "TRAVELOKA", profileType: "DEFAULT", productType: "STANDALONE", profileName: "DEFAULT", currency: "SGD"}  # Singapore B2C
tool: get_budget_balance     data: {currency: "THB"}
tool: load_commission_incentive_rules   data: {airlineId: "GA", fulfillmentId: "amadeus"}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Autopilot (5-field S3-key) or baseline (route-based)** → MUST read [`autopilot-operations.md`](references/autopilot-operations.md)
3. **Querying or updating commission / incentive** → MUST read [`commission-operations.md`](references/commission-operations.md)
4. **Querying budget** → MUST read [`budget-operations.md`](references/budget-operations.md)
5. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (profileGroup enum, originCountry distinction, ISO/IATA normalization)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters | Ref |
|-----------|-------------|----------------|-----|
| `load_autopilot_rules` | Automated pricing rules by profile+currency | profileGroup, profileType, productType, profileName, currency | [autopilot](references/autopilot-operations.md) |
| `update_autopilot_rules` | Update/create autopilot rules (conditions + adjustments) ⚠️ complex — load schema via search | autopilotToolData, version, notes | [autopilot](references/autopilot-operations.md) |
| `load_baseline_pricing_rules` | Base markup/margin rules (route-based, NOT 5-field) | profileGroup, originCountry, destinationCountry, airlineId | [autopilot](references/autopilot-operations.md) |
| `load_bundling_pricing_rules` | Bundle pricing (flight+hotel) | profileGroup, profileType, productType, profileName, currency | [autopilot](references/autopilot-operations.md) |
| `load_price_prediction_rules` | Anchor fare / dynamic pricing rules | profileGroup | [params](references/parameter-standards.md) |
| `load_price_cut_modifier_rules` | Price cut / promo modifiers | profileGroup | [params](references/parameter-standards.md) |
| `load_trx_fee_rules` | Transaction/service fee rules | profileGroup | [params](references/parameter-standards.md) |
| `load_pricing_profiles` | Pricing profile names | profileGroup | [params](references/parameter-standards.md) |
| `load_issuance_fee_rules` | Ticket issuance fees | fulfillmentId | [params](references/parameter-standards.md) |
| `get_budget_balance` | Budget remaining/used by currency | currency | [budget](references/budget-operations.md) |
| `list_active_budgets` | Active budgets by currency and level | currency | [budget](references/budget-operations.md) |
| `get_budget_levels` | Budget level types | — | [budget](references/budget-operations.md) |
| `get_budget_user_balance` | User-level budget balance | currency | [budget](references/budget-operations.md) |
| `load_commission_incentive_rules` | Commission rates for airline partners | airlineId, fulfillmentId | [commission](references/commission-operations.md) |
| `load_commission_incentive_profiles` | Commission profile list | — | [commission](references/commission-operations.md) |
| `load_tiered_incentive_rules` | Volume-based incentive tiers | brandId | [commission](references/commission-operations.md) |
| `check_tiered_incentive_progress` | PNR incentive progress check | pnr | [commission](references/commission-operations.md) |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "markup", "margin", "base pricing" | `load_baseline_pricing_rules` |
| "budget", "remaining budget", "budget left" | `get_budget_balance` |
| "commission", "airline commission rate" | `load_commission_incentive_rules` |
| "flash sale", "promo", "discount" | `load_price_cut_modifier_rules` |
| "bundle", "package", "flight+hotel" | `load_bundling_pricing_rules` |
| "autopilot", "automated pricing", "查看 autopilot" | `load_autopilot_rules` |
| "update autopilot", "修改 autopilot", "add rule", "改规则" | `update_autopilot_rules` |
| "service fee", "transaction fee" | `load_trx_fee_rules` |
| "issuance fee", "ticketing fee" | `load_issuance_fee_rules` |
| "incentive progress", "PNR check" | `check_tiered_incentive_progress` |
| "tiered incentive", "volume bonus" | `load_tiered_incentive_rules` |
| "anchor fare", "price prediction" | `load_price_prediction_rules` |

## Gotchas (top traps — full rules in references)

- **Parameter normalization & enums** (profileGroup is an enum not a country; ISO currency; IATA airline; commission needs airlineId + fulfillmentId) → [parameter-standards.md](references/parameter-standards.md)

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

### Update Rules (any rule type) ⚠️

**All update operations MUST follow this safety flow:**

1. **Load current** → `load_*_rules` → get baseline + `version` (optimistic lock)
2. **Search schema** → `x_amz_bedrock_agentcore_search(tool_name)` → get field structure
3. **Build payload** → assemble changes based on current rules + user request
4. **Call update** → submit (backend has approval flow built-in)

**All updates require loading current state first** — both for the `version` field and to understand existing rules before modifying.

## Disambiguation

- "fare adjuster" → **fpr-supply** (not pricing)
- "feature flag" → **fpr-config** (not pricing)
- "search cache", "booking detail" → **fpr-demand** (not pricing)
