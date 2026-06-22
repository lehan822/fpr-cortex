# Demand Parameter Standards

Normalize user input to these canonical forms before calling any tool.

## Normalization table

| Parameter | Accepts | Normalized To |
|-----------|---------|---------------|
| `bookingId` | "123456789", 123456789 | integer (not string) |
| `pnr` | "ABCD12" | uppercase string |
| `path` | full S3 path | must start with `"/"` |
| `date` | "today", "yesterday" | `"YYYY-MM-DD"` |
| `origin` / `destination` | "Jakarta", "CGK", "cgk" | `"CGK"` (IATA 3-letter, uppercase) |

## Key distinctions

- **`bookingId` must be integer** — `123456789`, not `"123456789"`
- **PNR vs bookingId** — `pnr` is airline reference (string), `bookingId` is Traveloka internal (integer). They are different identifiers — never swap them.
- **`path` for `get_booking_log`** — always starts with `"/<bookingId>/"`. The backend parses the first path segment as bookingId, do NOT pass `bookingId` as a separate field.
- **`date` for `get_booking_log`** — optional, narrows the S3 prefix. Omitted = backend auto-resolves.
