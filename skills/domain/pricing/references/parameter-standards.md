# Pricing Parameter Standards

Normalize user input to these canonical forms before calling any tool.

## Normalization table

| Parameter | Accepts | Normalized To |
|-----------|---------|---------------|
| `profileGroup` | "traveloka", "affiliate", "corporate" | `"TRAVELOKA"` / `"AFFILIATE"` / `"CORPORATE"` |
| `profileType` | "default" | `"DEFAULT"` |
| `productType` | "standalone", "connecting" | `"STANDALONE"` / `"CONNECTING"` |
| `profileName` | "default", country code like "SG" | `"DEFAULT"` or `"SG"` etc. |
| `currency` | "rupiah", "idr", "sgd" | `"IDR"` / `"SGD"` (ISO 4217 uppercase) |
| `originCountry` | "Thailand", "TH", "th" | `"TH"` |
| `airlineId` | "Garuda", "garuda" | `"GA"` (IATA 2-letter, uppercase) |
| `fulfillmentId` | "amadeus", "Amadeus" | `"amadeus"` (lowercase channel id) |

## Key distinctions (common mistakes)

- **`profileGroup` is an enum, NOT a country code.** Only `TRAVELOKA` / `AFFILIATE` / `CORPORATE`.
- **`profileGroup` vs `originCountry`:** profileGroup is the business segment; originCountry is the market.
  They are different fields — never swap them.
- **`profileName` vs `originCountry`:** profileName may *contain* a country code (e.g. `"SG"`) but is a
  separate concept from the `originCountry` filter. For the 5-field S3-key tools, only `profileName`
  participates in the key.
- **`currency` must be ISO 4217 uppercase** — `"THB"`, not `"thb"` or `"Baht"`.
- **`airlineId` must be IATA 2-letter uppercase** — `"GA"`, not `"Garuda"`.

## Tools that take only `profileGroup`
These do NOT use the 5-field S3 key — just pass `profileGroup`:
`load_price_prediction_rules`, `load_price_cut_modifier_rules`, `load_trx_fee_rules`, `load_pricing_profiles`.

## Reference codes

**Airlines:** GA=Garuda, JT=Lion Air, QZ=AirAsia ID, ID=Batik Air, SQ=Singapore Airlines,
TG=Thai Airways, VJ=VietJet, QG=Citilink, TR=Scoot, AK=AirAsia

**Profile Groups:** TRAVELOKA (default B2C), AFFILIATE (B2B partners), CORPORATE (corporate accounts)

**Countries:** ID=Indonesia, TH=Thailand, VN=Vietnam, MY=Malaysia, SG=Singapore, PH=Philippines, AU=Australia
