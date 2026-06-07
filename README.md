# fpr-cortex

> Flight Pricing & Revenue — AI Skills + Schema Pipeline

## For Users (install skills)

```bash
npx skills add lehan822/fpr-cortex -g -y     # install all
npx skills update -g                          # update
```

After install, your AI agent gains FPR pricing knowledge. Try:
> "查一下 GA 的 commission rate"

## Skills

### 🔑 Gateway

| Skill | Description |
|-------|-------------|
| `fpr-shared` | Auth (PKCE login), Gateway protocol, environment config, parameter standards |

### 📦 Domain — Business Logic

| Skill | Description |
|-------|-------------|
| `fpr-pricing` | Autopilot, markup rules, budgets, commissions, incentives |
| `fpr-supply` | Fare adjusters, providers, routes, fare check, inventory |
| `fpr-demand` | Bookings, search simulation, fare cache, promo labels |
| `fpr-config` | Feature flags, condition groups, audit logs, FX, country/airline lists |

### ⚙️ Ops — Infrastructure & Operations

| Skill | Description |
|-------|-------------|
| `fpr-ops-infra` | S3 paths, BQ datasets, DynamoDB tables, Redis clusters |
| `fpr-ops-deploy` | CI/CD pipelines, CodeDeploy, canary, rollback |
| `fpr-ops-oncall` | Runbooks, error codes, escalation paths, incident response |
| `fpr-ops-data` | BigQuery queries, CDE pipeline, data schemas |

### 🛠 Meta — Tooling

| Skill | Description |
|-------|-------------|
| `fpr-skill-maker` | Create, validate, and iterate on FPR skills |

## Naming Convention

```
fpr-{domain}       → Business domain skills (pricing, supply, demand, config)
fpr-ops-{area}     → Operations/infrastructure skills (infra, deploy, oncall, data)
fpr-shared         → Gateway (auth + env, read FIRST)
fpr-skill-maker    → Meta tooling
```

All skills include a `[category]` tag in their description for quick identification:
- `[gateway]` — Auth & shared standards
- `[domain]` — Business logic & API operations
- `[ops]` — Infrastructure, deployment, monitoring
- `[meta]` — Skill authoring tools

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
├── skills/
│   ├── gateway/             ← Auth + shared standards
│   │   └── shared/SKILL.md
│   ├── domain/              ← Business logic
│   │   ├── pricing/SKILL.md
│   │   ├── supply/SKILL.md
│   │   ├── demand/SKILL.md
│   │   └── config/SKILL.md
│   ├── ops/                 ← Infrastructure & operations
│   │   ├── infra/SKILL.md
│   │   ├── deploy/SKILL.md
│   │   ├── oncall/SKILL.md
│   │   └── data/SKILL.md
│   └── meta/               ← Tooling
│       └── skill-maker/SKILL.md
├── infra/                   ← Schema pipeline (CI/CD, not distributed)
│   ├── schemas/
│   ├── config/
│   └── scripts/
├── docs/                    ← Documentation
├── .github/workflows/       ← CI: generate → S3 → Gateway reload
└── VERSION
```

## For Contributors

### Adding a domain operation
1. Update `infra/config/exposed-ops.yaml`
2. Update `skills/domain/{domain}/SKILL.md` (routing table)
3. PR → merge → CI generates schema → S3 → Gateway reloads

### Adding a new skill
1. Determine category: `domain/`, `ops/`, or `meta/`
2. Create `skills/{category}/{name}/SKILL.md`
3. Follow naming convention: `fpr-{name}` or `fpr-ops-{name}`
4. Include frontmatter: `name`, `version`, `description` (with `[category]` tag), `category`, `prerequisites`
5. Use `fpr-skill-maker` to validate

### Generate schemas locally
```bash
npm install && npm run generate
```

## References
- [Architecture Design](https://traveloka.sg.larksuite.com/docx/KcSSd0QgNoyoR8xO9E8l5r9NgTd)
- [Framework Recommendation](https://traveloka.sg.larksuite.com/docx/GkgkdZ1Zuor4vQx7z8llkNiUgYe)
