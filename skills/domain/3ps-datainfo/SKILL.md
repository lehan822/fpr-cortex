---
name: fpr-3ps-datainfo
version: 1.0.0
description: "Third-party services and data information: Pronto destination tags, airport lists, airline routes, flight ID decryption. Use for reference data queries and route management."
category: domain
prerequisites:
  local: [fpr-shared]
  agentcore: []
---

# FPR 3PS & Data Info

> **⚠️ Local MCP tools. All tools are prefixed and authed via fpr-shared — read it first (see Prerequisites).**

```
# Common examples
tool: get_airport_list                     data: {}
tool: get_airline_routes                   data: {airlineId: "GA"}
tool: pronto_get_list_destination          data: {}
tool: decrypt_flight_id                    data: {flightId: "xxx"}
```

## Prerequisites — Read Before Executing

**CRITICAL — before the matching operation, you MUST Read the file(s) below. None are optional:**

1. **Local MCP only** → read **fpr-shared** first — auth, tool name prefix, request envelope (**all operations**)
2. **Unsure about parameters** → MUST read [`parameter-standards.md`](references/parameter-standards.md) (airlineId IATA format, destinationId type)

**Executing an operation without reading its required reference will cause parameter errors.**

## Operations

| Operation | Description | Key Parameters |
|-----------|-------------|----------------|
| **Pronto (Destination Tags)** |||
| `pronto_get_list_destination` | List all destinations with tags | — |
| `pronto_get_list_tag_name` | List all tag names | — |
| `pronto_view_destination` | View destination details | destinationId |
| `pronto_view_tag_name` | View tag details | tagName |
| `pronto_get_static_data` | Get static data for tags | — |
| `pronto_add_new_tag` | Add new tag (write) | tagData |
| `pronto_add_single_tag` | Add single tag (write) | tagData |
| `pronto_edit_single_tag` | Edit tag (write) | tagId, tagData |
| `pronto_edit_complete_tag` | Complete tag edit (write) | tagId |
| `pronto_remove_tag` | Remove tag (write) | tagId |
| **Reference Data** |||
| `get_airport_list` | List all airports | — |
| `get_airline_ids` | All IATA airline codes | — |
| `get_countries` | Supported country list | — |
| `get_airline_routes` | Active routes for airline | airlineId |
| `get_airline_route_history` | Route activation/deactivation history | airlineId, origin, destination |
| `get_airline_route_history_filtered` | Filtered route history | filters |
| `multi_country_crud` | Multi-country CRUD operations | operation, data |
| **Flight Services** |||
| `decrypt_flight_id` | Decrypt flight ID | flightId |
| `save_airline_route` | Save route (write) | routeData |
| `import_airline_route` | Import route (write) | routeData |

## Routing Guide

| User Intent | → Operation |
|-------------|-------------|
| "airport list", "all airports" | `get_airport_list` |
| "airline routes", "active routes" | `get_airline_routes` |
| "route history", "when did route start" | `get_airline_route_history` |
| "pronto tag", "destination tag" | `pronto_get_list_destination` or `pronto_view_destination` |
| "decrypt flight ID", "decode flight ID" | `decrypt_flight_id` |
| "multi-country", "batch country ops" | `multi_country_crud` |

## Gotchas (top traps — full rules in references)

- **Parameter normalization** — airlineId must be IATA 2-letter uppercase (`"GA"` not `"garuda"`); see [parameter-standards.md](references/parameter-standards.md)
- **Pronto tags** — destination tags are used for marketing campaign and route segmentation
- **Flight ID decryption** — used for debugging and tracing flight identifiers across systems

## Disambiguation

- "fare adjuster", "provider sourcing" → **fpr-supply** (not 3ps-datainfo)
- "booking detail", "PNR lookup" → **fpr-demand** (not 3ps-datainfo)
- "feature flag" → **fpr-sysinteg** (not 3ps-datainfo)
- "airline route config" (provider level) → **fpr-supply**; at reference data level → **fpr-3ps-datainfo**
