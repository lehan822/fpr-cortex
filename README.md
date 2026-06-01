# fpr-cortex

> The brain layer of Flight Pricing & Revenue

Machine-readable schemas, domain skills, and intelligent CLI — everything AI agents need to operate FPR.

## Architecture

```
                    ┌─────────────────────────────────┐
                    │          fpr-cortex              │
                    ├──────────┬──────────┬────────────┤
                    │ schemas/ │ skills/  │ cli/       │
                    │ OpenAPI  │ Domain   │ Normalize  │
                    │ tool     │ routing  │ + Format   │
                    │ defs     │ hints    │ + Validate │
                    └────┬─────┴────┬─────┴─────┬──────┘
                         │          │           │
              ┌──────────▼──┐ ┌────▼────┐ ┌────▼────┐
              │  AgentCore  │ │ Agent   │ │ Human / │
              │  Gateway    │ │ Context │ │ On-call │
              └─────────────┘ └─────────┘ └─────────┘
```

## Components

### `schemas/` — Tool Definitions (OpenAPI 3.0)

Machine-readable tool definitions deployable to any AI platform.

| Domain | Tools | Schema Quality | Status |
|--------|-------|---------------|--------|
| [pricing](schemas/pricing/) | 16 | ✅ Rich — "Use when" triggers, business context, examples | Production |
| [supply](schemas/supply/) | 17 | 🟡 Minimal — function name only | Draft |
| demand | ~12 | ⬜ Planned | — |
| config | ~8 | ⬜ Planned | — |

**Deploy to AWS AgentCore Gateway:**
```bash
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier <gw-id> \
  --name fprtool-pricing \
  --cli-input-json file://deploy/pricing-target.json
```

### `skills/` — Domain Knowledge

Structured knowledge that helps AI agents route requests and normalize parameters.

- **Routing guide** — "flash sale" → `load_price_cut_modifier_rules`
- **Parameter normalization** — "Indonesia" → "ID", "Garuda" → "GA"
- **Airline code reference** — GA, JT, QZ, SQ, TG...

### `cli/` — Intelligent CLI

The smart middle layer with normalization, validation, and formatting.

```bash
fpr pricing budget --currency IDR
fpr pricing baseline --country Indonesia --airline Garuda
fpr supply search-fare --from CGK --to DPS --date 2026-06-15
```

## Schema Design Principles

1. **"Use when" routing** — Every description includes trigger phrases for LLM tool selection
2. **Business context** — Explain what it does in domain terms, not API terms
3. **Example values** — Real airline codes, currency codes, country codes
4. **Disambiguation** — Similar tools have descriptions that clarify which to use

```diff
- "Load baseline pricing rules"
+ "Retrieve baseline markup/margin rules that define the base price 
+  adjustment for flights. Use when someone asks about 'baseline markup',
+  'base margin', or 'how much markup do we add'."
```

## A/B Test Results

Tool selection accuracy comparison (same Gateway, same prompts):

| Metric | Rich Schema (pricing) | Minimal Schema (supply) |
|--------|----------------------|------------------------|
| "Use when" hints | ✅ 100% | ❌ 0% |
| Selection confidence | 🟢 HIGH | 🔴 LOW |
| Ambiguity cases | 0/5 | 3/5 |
| Predicted accuracy | **90-95%** | **50-60%** |

## License

Internal use — Traveloka Flight Pricing & Revenue team.
