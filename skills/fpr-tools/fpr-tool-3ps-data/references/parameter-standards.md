# 3PS & Data Info Parameter Standards

Normalize user input to these canonical forms before calling any tool.

## Normalization table

| Parameter | Accepts | Normalized To |
|-----------|---------|---------------|
| `airlineId` | "Garuda", "garuda" | `"GA"` (IATA 2-letter, uppercase) |
| `origin` / `destination` | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA 3-letter, uppercase) |
| `destinationId` | numeric string or integer | integer |
| `tagName` | "beach", "Beach" | lowercase |
| `flightId` | full encrypted string | as-is (opaque string) |
| `country` | "Indonesia", "ID", "id" | `"ID"` (ISO 3166-1 alpha-2, uppercase) |

## Key distinctions

- **`airlineId` is IATA 2-letter uppercase** — `"GA"`, not `"Garuda"`
- **`origin`/`destination` are IATA 3-letter airport codes** — `"CGK"`, not `"Jakarta"`
- **`destinationId` is integer** — not string
- **Pronto tags are case-sensitive** — match existing tagName casing exactly
