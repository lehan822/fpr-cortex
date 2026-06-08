---
name: fpr-pricing
description: "Pricing rules, autopilot, budget, commissions, incentives. Use when querying pricing configuration, markup/margin rules, budget balances, or commission rates."
version: "2.1.0"
category: domain
domain: pricing
prerequisites:
  local: [fpr-shared]
  agentcore: []
---

# FPR Pricing

## Prerequisites — Read Before Executing

1. **Local MCP only** → read **fpr-shared** first (auth, tool name prefix, request envelope)
2. **Querying commission/incentive** → MUST read [`commission-operations.md`](references/commission-operations.md)
3. **Querying budget** → MUST read [`budget-operations.md`](references/budget-operations.md)
4. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (profileGroup enum, originCountry distinction)

**Executing operations without reading the required references will lead to parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| `load_autopilot_rules` | Automated pricing rules by country/airline | profileGroup, originCountry, airlineId |
| `get_budget_balance` | Budget remaining/used by currency | currency |
| `list_active_budgets` | Active budgets by currency and level | currency |
| `load_baseline_pricing_rules` | Base markup/margin rules | profileGroup, airlineId |
| `load_bundling_pricing_rules` | Bundle pricing (flight+hotel) | profileGroup |
| `load_price_prediction_rules` | Anchor fare / dynamic pricing rules | profileGroup |
| `load_price_cut_modifier_rules` | Price cut / promo modifiers | profileGroup |
| `load_trx_fee_rules` | Transaction/service fee rules | profileGroup |
| `load_pricing_profiles` | Pricing profile names | profileGroup |
| `load_commission_incentive_rules` | Commission rates for airline partners | airlineId, fulfillmentId |
| `load_commission_incentive_profiles` | Commission profile list | — |
| `load_tiered_incentive_rules` | Volume-based incentive tiers | brandId |
| `check_tiered_incentive_progress` | PNR incentive progress check | pnr |
| `load_issuance_fee_rules` | Ticket issuance fees | fulfillmentId |
| `get_budget_levels` | Budget level types | — |
| `get_budget_user_balance` | User-level budget balance | currency |

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

## Common Codes

**Airlines:** GA=Garuda, JT=Lion Air, QZ=AirAsia ID, ID=Batik Air, SQ=Singapore Airlines, TG=Thai Airways, VJ=VietJet, QG=Citilink, TR=Scoot, AK=AirAsia

**Profile Groups:** TRAVELOKA (default B2C), AFFILIATE (B2B partners), CORPORATE (corporate accounts)

**Countries:** ID=Indonesia, TH=Thailand, VN=Vietnam, MY=Malaysia, SG=Singapore, PH=Philippines, AU=Australia

## Disambiguation

- "fare adjuster" → **fpr-supply** (not pricing)
- "feature flag" → **fpr-config** (not pricing)
- "search cache", "booking detail" → **fpr-demand** (not pricing)
