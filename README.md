# fpr-cortex

> The brain layer of Flight Pricing & Revenue — Skills, Schemas, and config for AI-native pricing operations.

## Architecture

```
fpr-cortex/
├── skills/                    # Domain knowledge (AI agent instructions)
│   ├── shared/SKILL.md        # Platform layer: auth, gateway, standards
│   ├── pricing/SKILL.md       # Pricing domain routing + hints
│   ├── supply/SKILL.md        # Supply domain routing + hints  
│   ├── demand/SKILL.md        # Demand domain routing + hints
│   └── config/SKILL.md        # Config domain routing + hints
├── schemas/                   # API definitions (auto-generated)
│   ├── fprtool-full.json      # Source: complete OpenAPI spec (55 paths)
│   ├── pricing/pricing.json   # Generated: pricing-only spec
│   ├── supply/supply.json     # Generated: supply-only spec
│   ├── demand/demand.json     # Generated: demand-only spec
│   └── config/config.json     # Generated: config-only spec
├── config/
│   └── exposed-ops.yaml       # Whitelist: which operations to expose
├── scripts/
│   └── schema-gen.js          # Splits full schema by domain + whitelist
└── .github/workflows/
    └── generate-schemas.yaml  # CI: auto-generate on merge
```

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Developer      │     │  AgentCore   │     │  Agent          │     │  fprtool     │
│  installs       │────▶│  Gateway     │────▶│  Registry       │     │  backend     │
│  Skills locally │     │  (Schema+Auth)│     │  (Discovery)    │     │              │
└─────────────────┘     └──────┬───────┘     └──────────────────┘     └──────────────┘
                               │                                             ▲
                               └─────────────────────────────────────────────┘
                                              Route & Execute
```

**Data Flow:**
1. Agent reads domain Skill → knows which operation + params
2. Agent reads fpr-shared → gets M2M token + user token + Gateway URL
3. Agent calls Gateway: `Authorization: M2M` + `body.context.authServiceToken: user`
4. Gateway routes to fprtool-backend
5. Backend validates user token → returns data

## Dual Token Auth

| Token | Where | Who validates | Purpose |
|-------|-------|--------------|---------|
| M2M access_token | `Authorization` header | AgentCore Gateway | Agent is registered |
| User id_token | `body.context.authServiceToken` | fprtool-backend | Who initiated the request |

## For Domain Owners

Add or update your domain's Skill:

1. Edit `skills/{your-domain}/SKILL.md`
2. Add new operations to `config/exposed-ops.yaml`
3. Submit PR → review → merge
4. GitHub Actions auto-generates new schema → pushes to S3 → Gateway reloads

## For Developers (Using Skills)

```bash
# Install skills locally
npx fpr-cortex install

# Or manually symlink
ln -s /path/to/fpr-cortex/skills/* ~/.agents/skills/
```

## References

- [Architecture Design (Lark)](https://traveloka.sg.larksuite.com/docx/KcSSd0QgNoyoR8xO9E8l5r9NgTd)
- [Framework Recommendation (Lark)](https://traveloka.sg.larksuite.com/docx/GkgkdZ1Zuor4vQx7z8llkNiUgYe)
- [ATH M2M RFC](https://traveloka.sg.larksuite.com/wiki/JXgdw2PkgiQCdvk9JbklVvqxgrc)
