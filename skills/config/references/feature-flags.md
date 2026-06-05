# Feature Flag Operations

## get_feature_flags
Check flag status for an application.

**Parameters:**
- `appName` (required): e.g. "fprtool", "flight-search", "pricing-engine"

**Response:** Map of flagName → { enabled: bool, rolloutPercentage: number }

## get_flag_configuration
Detailed flag config including targeting rules.

**Parameters:**
- `appName` (required)
- `flagName` (required)

**Response:** Full flag definition with:
- Enabled state
- Targeting rules (by country, user segment, etc.)
- Rollout percentage
- Last modified by/when
