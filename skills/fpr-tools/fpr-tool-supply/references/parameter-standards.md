# Supply Parameter Standards

Normalize user input to these canonical forms before calling any tool.

## Normalization table

| Parameter | Accepts | Normalized To |
|-----------|---------|---------------|
| `airlineId` | "Garuda", "garuda" | `"GA"` (IATA 2-letter, uppercase) |
| `origin` / `destination` | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA 3-letter, uppercase) |
| `departureDate` | "tomorrow", "next Monday", "15 Jan" | `"YYYY-MM-DD"` |
| `providerId` | "1", 1 | integer |
| `fareCheckId` | full ID string | as-is (opaque string) |
| `flightNumber` | "GA123", "ga123" | `"GA123"` (uppercase) |

## Key distinctions

- **`airlineId` is IATA 2-letter uppercase** — `"GA"`, not `"Garuda"` or `"garuda"`
- **`origin`/`destination` are IATA 3-letter airport codes** — `"CGK"`, not `"Jakarta"`
- **`departureDate` is always `YYYY-MM-DD`** — resolve relative dates before calling
- **`providerId` is integer** — not string
