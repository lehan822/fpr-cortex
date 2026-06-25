# SysInteg Parameter Standards

Normalize user input to these canonical forms before calling any tool.

## Normalization table

| Parameter | Accepts | Normalized To |
|-----------|---------|---------------|
| `appName` | "FlightBookingPricing", "fpr-bopi", "fprbopi" | `"fprbopi"` (lowercase, no hyphens) |
| `flagName` | "enable new pricing", "enable-new-pricing" | `"enable-new-pricing"` (kebab-case) |
| `entityType` | "pricing rule", "Pricing Rule" | `"PRICING_RULE"` (SCREAMING_SNAKE_CASE) |
| `startDate` / `endDate` | "last month", "Jan 1" | `"YYYY-MM-DD"` |
| `sourceCurrency` / `targetCurrency` | "rupiah", "IDR", "idr" | `"IDR"` (ISO 4217 uppercase) |
| `key` | full S3 key | as-is (opaque string) |

## Valid entityType values

- `PRICING_RULE`, `FEATURE_FLAG`, `CONDITION_GROUP`, `BUDGET`, `PROVIDER`

## Key distinctions

- **`appName` must be lowercase service name** — `"fprbopi"`, not `"fpr-bopi"` or `"FlightBookingPricing"`
- **`entityType` is SCREAMING_SNAKE_CASE** — `"PRICING_RULE"`, not `"pricing_rule"` or `"Pricing Rule"`
- **`flagName` is kebab-case** — `"enable-new-pricing"`, not `"enableNewPricing"`
- **Currency codes are ISO 4217 uppercase** — `"IDR"`, not `"idr"` or `"rupiah"`
