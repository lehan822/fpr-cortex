# fpr-cortex

> Flight Pricing & Revenue — AI Skills for pricing operations via AgentCore Gateway.

## Quick Start

```bash
# Install all FPR skills (no GitHub account needed)
npx skills add lehan822/fpr-cortex -g -y

# Install specific domain only
npx skills add lehan822/fpr-cortex -s fpr-pricing -g -y

# Update to latest
npx skills update -g
```

After install, your AI agent (Claude Code, Copilot CLI, etc.) automatically gains FPR knowledge.

**Try it:**
> "查一下 GA Indonesia 的 commission rate"
> "CGK-DPS 明天的 fare cache"
> "budget balance IDR"

## Skills

| Skill | Domain | Description |
|-------|--------|-------------|
| `fpr-shared` | Platform | Auth, Gateway URL, parameter standards (loaded first) |
| `fpr-pricing` | Pricing | Markup rules, budgets, commissions, incentives |
| `fpr-supply` | Supply | Fare adjusters, providers, routes, fare check |
| `fpr-demand` | Demand | Bookings, search simulation, fare cache, promo labels |
| `fpr-config` | Config | Feature flags, condition groups, audit logs, FX |

## How It Works

```
User → AI Agent → reads Skill → calls AgentCore Gateway → fprtool-backend
                                       ↓
                              M2M auth (agent identity)
                              + user token (who asked)
```

**On-demand loading (zero overhead):**
1. Agent starts → reads only skill names + descriptions (~50 tokens each)
2. User asks pricing question → Agent loads full `fpr-pricing` SKILL.md
3. Needs auth details → loads `fpr-shared`
4. Needs deep docs → reads `references/budget-operations.md`

## Architecture

```
fpr-cortex/
├── skills/                    # AI agent instructions (the "brain")
│   ├── shared/SKILL.md        # Platform: auth + gateway + standards
│   ├── pricing/SKILL.md       # Pricing domain routing
│   ├── supply/SKILL.md        # Supply domain routing
│   ├── demand/SKILL.md        # Demand domain routing
│   └── config/SKILL.md        # Config domain routing
├── schemas/                   # API definitions
│   └── fprtool-full.json      # Source OpenAPI spec (55 operations)
├── config/
│   └── exposed-ops.yaml       # API exposure whitelist (PR-gated)
├── scripts/
│   └── schema-gen.js          # Per-domain schema generator
├── VERSION                    # For auto-update detection
└── .github/workflows/
    └── generate-schemas.yaml  # CI: auto-generate on merge → S3
```

## Updates

Skills auto-check for updates. When a new version is available, your agent will suggest:

```
ℹ️ FPR Skills 有新版本 (v2.1.0)。运行 `npx skills update -g` 更新。
```

Or manually: `npx skills update -g`

## For Contributors

### Adding a new operation

1. Add operation to `config/exposed-ops.yaml`
2. Update the domain's `skills/{domain}/SKILL.md`
3. (Optional) Add deep doc to `skills/{domain}/references/`
4. Submit PR → review → merge
5. CI generates new schema → pushes to S3 → Gateway reloads
6. Users run `npx skills update -g` to get new skill content

### Generating schemas locally

```bash
npm install
node scripts/schema-gen.js
```

## References

- [Architecture Design](https://traveloka.sg.larksuite.com/docx/KcSSd0QgNoyoR8xO9E8l5r9NgTd)
- [Framework Recommendation](https://traveloka.sg.larksuite.com/docx/GkgkdZ1Zuor4vQx7z8llkNiUgYe)
- [ATH M2M RFC](https://traveloka.sg.larksuite.com/wiki/JXgdw2PkgiQCdvk9JbklVvqxgrc)
