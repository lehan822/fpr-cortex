---
name: fpr-pricing
description: "Pricing rules, autopilot, budget, commissions, incentives. Use when querying pricing configuration, markup/margin rules, budget balances, or commission rates."
version: "2.3.0"
category: domain
domain: pricing
prerequisites:
  local: [fpr-shared]
  agentcore: []
tools:
  - load_autopilot_rules
  - get_budget_balance
  - get_budget_levels
  - get_budget_user_balance
  - list_active_budgets
  - load_baseline_pricing_rules
  - load_bundling_pricing_rules
  - load_commission_incentive_profiles
  - load_commission_incentive_rules
  - load_issuance_fee_rules
  - load_price_cut_modifier_rules
  - load_price_prediction_rules
  - load_pricing_profiles
  - load_tiered_incentive_rules
  - load_trx_fee_rules
  - check_tiered_incentive_progress
---

# FPR Pricing

## Prerequisites — Read Before Executing

1. **Local MCP only** → read **fpr-shared** first (auth, tool name prefix, request envelope)
2. **Querying commission/incentive** → MUST read [`commission-operations.md`](references/commission-operations.md)
3. **Querying budget** → MUST read [`budget-operations.md`](references/budget-operations.md)
4. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (profileGroup enum, originCountry distinction)

**Executing operations without reading the required references will lead to parameter errors.**

## Quick Examples

```
tool: load_autopilot_rules
data: {profileGroup: "TRAVELOKA", originCountry: "TH"}
→ returns autopilot pricing rules for Thailand B2C
```

```
tool: get_budget_balance
data: {currency: "THB"}
→ returns remaining/used budget in Thai Baht
```

```
tool: load_commission_incentive_rules
data: {airlineId: "GA", fulfillmentId: "amadeus"}
→ returns Garuda commission rates via Amadeus
```

## Operations

| Operation | Source | Description | Key Parameters |
|-----------|--------|-------------|----------------|
| `load_autopilot_rules` | fprtool | Automated pricing rules by country/airline | profileGroup, originCountry, airlineId |
| `get_budget_balance` | fprtool | Budget remaining/used by currency | currency |
| `list_active_budgets` | fprtool | Active budgets by currency and level | currency |
| `load_baseline_pricing_rules` | fprtool | Base markup/margin rules | profileGroup, airlineId |
| `load_bundling_pricing_rules` | fprtool | Bundle pricing (flight+hotel) | profileGroup |
| `load_price_prediction_rules` | fprtool | Anchor fare / dynamic pricing rules | profileGroup |
| `load_price_cut_modifier_rules` | fprtool | Price cut / promo modifiers | profileGroup |
| `load_trx_fee_rules` | fprtool | Transaction/service fee rules | profileGroup |
| `load_pricing_profiles` | fprtool | Pricing profile names | profileGroup |
| `load_commission_incentive_rules` | fprtool | Commission rates for airline partners | airlineId, fulfillmentId |
| `load_commission_incentive_profiles` | fprtool | Commission profile list | — |
| `load_tiered_incentive_rules` | fprtool | Volume-based incentive tiers | brandId |
| `check_tiered_incentive_progress` | fprtool | PNR incentive progress check | pnr |
| `load_issuance_fee_rules` | fprtool | Ticket issuance fees | fulfillmentId |
| `get_budget_levels` | fprtool | Budget level types | — |
| `get_budget_user_balance` | fprtool | User-level budget balance | currency |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "markup", "margin", "base pricing" | `load_baseline_pricing_rules` |
| "budget", "remaining budget", "budget left" | `get_budget_balance` |
| "commission", "airline commission rate" | `load_commission_incentive_rules` |
| "flash sale", "promo", "discount" | `load_price_cut_modifier_rules` |
| "bundle", "package", "flight+hotel" | `load_bundling_pricing_rules` |
| "autopilot", "automated pricing" | `load_autopilot_rules` |
| "service fee", "transaction fee" | `load_trx_fee_rules` |
| "issuance fee", "ticketing fee" | `load_issuance_fee_rules` |
| "incentive progress", "PNR check" | `check_tiered_incentive_progress` |
| "tiered incentive", "volume bonus" | `load_tiered_incentive_rules` |
| "anchor fare", "price prediction" | `load_price_prediction_rules` |

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| profileGroup | "traveloka", "affiliate", "corporate" | `"TRAVELOKA"` / `"AFFILIATE"` / `"CORPORATE"` |
| originCountry | "Thailand", "TH", "th" | `"TH"` |
| currency | "rupiah", "idr" | `"IDR"` |
| airlineId | "Garuda", "garuda" | `"GA"` |

## Gotchas

- `profileGroup` is an enum (`TRAVELOKA` / `AFFILIATE` / `CORPORATE`), NOT a country code
- Use `originCountry` for country filtering (e.g. `"TH"`), not `profileGroup`
- `currency` must be ISO 4217 uppercase (e.g. `"THB"`, not `"thb"` or `"Baht"`)
- `airlineId` is IATA 2-letter code, uppercase (e.g. `"GA"`, not `"Garuda"`)
- Commission queries require both `airlineId` AND `fulfillmentId`

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

## Common Codes

**Airlines:** GA=Garuda, JT=Lion Air, QZ=AirAsia ID, ID=Batik Air, SQ=Singapore Airlines, TG=Thai Airways, VJ=VietJet, QG=Citilink, TR=Scoot, AK=AirAsia

**Profile Groups:** TRAVELOKA (default B2C), AFFILIATE (B2B partners), CORPORATE (corporate accounts)

**Countries:** ID=Indonesia, TH=Thailand, VN=Vietnam, MY=Malaysia, SG=Singapore, PH=Philippines, AU=Australia

## Disambiguation

- "fare adjuster" → **fpr-supply** (not pricing)
- "feature flag" → **fpr-config** (not pricing)
- "search cache", "booking detail" → **fpr-demand** (not pricing)
