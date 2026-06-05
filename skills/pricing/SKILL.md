---
name: fpr-pricing
description: "fpr-cli pricing domain: pricing rules, autopilot, budget, commissions, incentives. Use when querying pricing configuration, markup/margin rules, budget balances, or commission rates."
version: "2.0.0"
domain: pricing
prerequisites:
  - fpr-shared
---

# FPR Pricing

> ⚠️ **Read [fpr-shared](../shared/SKILL.md) first** — it covers authentication, Gateway URL, and parameter standards.
>
> ⚠️ **Tool name prefix required:** When calling `tools/call`, prepend `fprtool-backend___` to every operation name below (e.g. `fprtool-backend___load_commission_incentive_rules`). Params go inside `data:{}` envelope. See fpr-shared for full request format.

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
| profileGroup | "Indonesia", "ID", "id" | `"ID"` |
| currency | "rupiah", "idr" | `"IDR"` |
| airlineId | "Garuda", "garuda" | `"GA"` |

## Common Codes

**Airlines:** GA=Garuda, JT=Lion Air, QZ=AirAsia ID, ID=Batik Air, SQ=Singapore Airlines, TG=Thai Airways, VJ=VietJet, QG=Citilink, TR=Scoot, AK=AirAsia

**Profile Groups:** ID=Indonesia, TH=Thailand, VN=Vietnam, MY=Malaysia, SG=Singapore, PH=Philippines

## Disambiguation

- "fare adjuster" → **fpr-supply** (not pricing)
- "feature flag" → **fpr-config** (not pricing)
- "search cache", "booking detail" → **fpr-demand** (not pricing)
