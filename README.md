# fpr-cortex

> Flight Pricing & Revenue — AI Skills + Schema Pipeline

## For Users (install skills)

```bash
npx skills add lehan822/fpr-cortex -g -y     # install
npx skills update -g                          # update
```

After install, your AI agent gains FPR pricing knowledge. Try:
> "查一下 GA 的 commission rate"

## Skills

| Skill | Description |
|-------|-------------|
| `fpr-shared` | Auth (PKCE login), Gateway protocol (MCP), parameter standards |
| `fpr-pricing` | Markup rules, budgets, commissions, incentives |
| `fpr-supply` | Fare adjusters, providers, routes, fare check |
| `fpr-demand` | Bookings, search simulation, fare cache, promo labels |
| `fpr-config` | Feature flags, condition groups, audit logs, FX |

## How It Works

```
User → AI Agent → loads Skill (routing + auth)
                → calls Gateway tools/list (get params)
                → calls Gateway tools/call (execute)
                → returns data
```

- **Skills** = local Markdown, tells Agent which tool to call
- **Gateway** = MCP server, provides tool schemas + executes calls
- **No local schema needed** — Agent queries Gateway at runtime

## Repo Structure

```
fpr-cortex/
├── skills/              ← Distributed to users via npx skills add
│   ├── shared/SKILL.md  # Auth + Gateway + standards
│   ├── pricing/SKILL.md # Pricing domain routing
│   ├── supply/SKILL.md  # Supply domain routing
│   ├── demand/SKILL.md  # Demand domain routing
│   └── config/SKILL.md  # Config domain routing
├── infra/               ← Schema pipeline (CI/CD, not distributed)
│   ├── schemas/         # OpenAPI specs (source + generated)
│   ├── config/          # exposed-ops.yaml whitelist
│   └── scripts/         # schema-gen.js
├── .github/workflows/   # CI: generate → S3 → Gateway reload
└── VERSION
```

## For Contributors

### Adding operations
1. Update `infra/config/exposed-ops.yaml`
2. Update domain `skills/{domain}/SKILL.md` (routing table)
3. PR → merge → CI generates schema → S3 → Gateway reloads

### Generate schemas locally
```bash
npm install && npm run generate
```

## References
- [Architecture Design](https://traveloka.sg.larksuite.com/docx/KcSSd0QgNoyoR8xO9E8l5r9NgTd)
- [Framework Recommendation](https://traveloka.sg.larksuite.com/docx/GkgkdZ1Zuor4vQx7z8llkNiUgYe)
