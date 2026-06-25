# Autopilot & Baseline Operations

Autopilot and baseline use **different parameter models** — do not mix them up.

| Tool | Param model |
|------|-------------|
| `load_autopilot_rules`, `load_bundling_pricing_rules`, `update_autopilot_rules` | **5-field S3 key** (below) |
| `load_baseline_pricing_rules` | **route-based**: profileGroup + originCountry + destinationCountry + airlineId |

---

## Autopilot — 5-field S3 key

`load_autopilot_rules` resolves config by building an S3 key from five ordered fields:

```
{profileGroup}.{profileType}.{productType}.{profileName}.{currency}
```

Missing or misordered fields → backend `500 ArrayIndexOutOfBoundsException`.

| Field | Enum / Format | Example |
|-------|---------------|---------|
| `profileGroup` | `TRAVELOKA` / `AFFILIATE` / `CORPORATE` (enum, NOT a country) | `"TRAVELOKA"` |
| `profileType` | `DEFAULT` (B2C) / `SPECIFIC` (affiliate) | `"DEFAULT"` |
| `productType` | `STANDALONE` / `CONNECTING` | `"STANDALONE"` |
| `profileName` | `DEFAULT` (B2C) or partner name (e.g. `skyscanner-flight`) | `"DEFAULT"` |
| `currency` | ISO 4217 uppercase | `"THB"` |

```
tool: load_autopilot_rules
data: {profileGroup: "TRAVELOKA", profileType: "DEFAULT", productType: "STANDALONE", profileName: "DEFAULT", currency: "THB"}
```

Common specs: `TRAVELOKA.DEFAULT.STANDALONE.DEFAULT.THB`, `AFFILIATE.SPECIFIC.STANDALONE.skyscanner-flight.THB`.

**Response:** `data.autopilotToolData.rules[]` (evaluated top-down) + `data.autopilotToolData.version` (optimistic lock — keep for updates).

## load_baseline_pricing_rules — route-based (NOT 5-field)

Baseline does **not** use the S3 key. Confirmed via live Gateway schema — params are route-based:

```
tool: load_baseline_pricing_rules
data: {profileGroup: "TRAVELOKA", originCountry: "TH", destinationCountry: "...", airlineId: "FD"}
```

- `profileGroup` is still the enum (`TRAVELOKA` / `AFFILIATE` / `CORPORATE`).
- `originCountry` / `airlineId` ARE primary params here (the opposite of autopilot).
- **Response:** `data.pricingBaselineToolData.rules[]`; markup % at `adjustment.defaultTreatment.tieredRules[].adjustmentPctFromBaseCalculation`.
- API may not return all rules (MAB experiment rules not exposed) — actual matched baseline can differ.

> If unsure of exact fields, run `x_amz_bedrock_agentcore_search("load_baseline_pricing_rules")` to load the authoritative schema (some tools return `{body:{}}` — fall back to the params above).

## update_autopilot_rules ⚠️

Complex payload. **MUST follow the safe update flow:**

1. **Load current** → `load_autopilot_rules` → capture rules + `version`
2. **Search schema** → `x_amz_bedrock_agentcore_search("update_autopilot_rules")` → get `autopilotToolData` structure
3. **Build payload** → merge user changes onto current rules
4. **Call update** → submit with `autopilotToolData`, `version`, `notes` (backend has approval flow built in)

Updates require loading current state first — for the `version` (optimistic lock) and to avoid clobbering existing rules.
