---
name: fpr-supply-search
description: "fpr-cli supply-search domain: fare search simulation, revalidation, provider sourcing configuration. Use when querying supply search results, testing fetcher, checking provider config, or revalidating fares."
version: "1.0.0"
domain: supply-search
prerequisites:
  - fpr-shared
---

# FPR Supply Search

> ⚠️ **Read [fpr-shared](../shared/SKILL.md) first** — it covers authentication, Gateway URL, and parameter standards.
>
> ⚠️ **Read [fpr-shared](../shared/SKILL.md) first** — covers auth, request format, and call format per source.

## Operations

| Operation | Source | Description | Key Parameters |
|-----------|--------|-------------|----------------|
| `search_regular_fare` | fprtool | Search regular fares by route | origin, destination, departureDate, airline, provider |
| `get_provider_sourcing` | fprtool | Get provider sourcing config | airlineId, inventoryType, originCountry, destinationCountry |
| `get_provider_source_histories` | fprtool | Provider sourcing change history | airlineId, inventoryType, agentId |
| `get_provider_source_latest_version` | fprtool | Latest provider sourcing version | — |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "search fare", "fetcher test", "run search", "search regular fare" | `search_regular_fare` |
| "provider sourcing", "which provider serves this route", "provider config" | `get_provider_sourcing` |
| "provider history", "sourcing changes", "who changed provider" | `get_provider_source_histories` |
| "latest sourcing version", "current version" | `get_provider_source_latest_version` |

## Parameter Normalization

| Parameter | Accepts | Normalized To |
|-----------|---------|--------------|
| origin / destination | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA airport code, uppercase) |
| departureDate | "tomorrow", "2026-06-15", "June 15" | `"2026-06-15"` (ISO format) |
| airline | "Garuda", "GA", "ga" | `"GA"` (IATA airline code, uppercase) |
| inventoryType | "regular", "REGULAR" | `"REGULAR"` |
| originCountry | "Indonesia", "ID", "id" | `"ID"` (ISO 3166 country code) |

## Workflows

### No Results Diagnosis
1. `search_regular_fare` — confirm no fare returned
2. `get_provider_sourcing` — check if provider is configured for this route
3. `get_provider_source_histories` — check if config was recently changed

### Provider Config Audit
1. `get_provider_sourcing` — get current config
2. `get_provider_source_histories` — compare with previous versions

## Common Codes

- **Airlines:** GA (Garuda), SQ (Singapore Airlines), QZ (AirAsia ID), JT (Lion Air), VJ (VietJet), AA (AirAsia), TG (Thai Airways)
- **Inventory types:** REGULAR, SPECIAL, UPSELL
- **Providers:** amadeus, sabre, travelport, mystifly, kiwi, ndc-*

## Disambiguation

- "budget balance", "pricing rules", "autopilot" → **fpr-pricing** (not supply-search)
- "booking details", "PNR lookup" → **fpr-supply-booking** (not supply-search)
- "promo label", "top pick" → **fpr-demand** (not supply-search)
