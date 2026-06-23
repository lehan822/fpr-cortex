# FPR Cortex Skill Onboarding — Presentation Script

> ~50 min talk + 10 min Q&A = 60 min total. Casual, conversational tone. Screen-share the Lark doc throughout.

---

## Opening (2 min)

"Hey everyone, thanks for coming. Quick context — over the past few weeks we've been building something called FPR Cortex. It's a framework that lets AI agents — Copilot CLI, Claude Code, Lark bots — call our FPR APIs directly, without us engineers manually opening Postman every time.

Today's goal is four things: understand the design, see a live demo, know exactly what your team needs to do, and align on PICs and timeline. Should take about an hour — I'll keep it interactive, feel free to jump in with questions."

*[Share screen: Lark doc — Part 1]*

---

## Part 1: Architecture Overview (12 min)

### 1.1 Problem (3 min)

"Let's start with the pain. Today, if a PM or on-call engineer wants to check Thailand autopilot rules, here's what happens:"

*[Point to the before/after grid]*

"They ping us on Lark. We stop what we're doing, open Postman, find the right API among 900+, figure out the parameters, make the call, format the result, paste it back. Every single time.

It's slow — minutes to hours of back-and-forth. And it blocks on engineer availability. If you're on-call at 2am, you're the one doing this.

The goal is simple: let users ask an AI agent the same question in plain English, and the agent figures out which API to call and how to fill the parameters. Instant. Self-service."

### 1.2 Core Challenge (3 min)

"Now, the hard part isn't calling the API — it's knowing WHICH API to call. We have 88 operations across 5 domains. When someone says 'check autopilot pricing rules for Thailand', there's no keyword match — 'autopilot' isn't in any API name."

*[Point to the whiteboard diagram]*

"This is a routing accuracy problem. Our primary metric is: given a natural language intent, does the AI select the correct operation AND fill correct parameters? If it picks the wrong API or fills the wrong country code, that's a failure — even if the call itself succeeds."

### 1.3 Why Schema + Skill (4 min)

"We attacked this with two layers:

**Schema** is auto-generated from our backend Java code. CI scans fprtool-backend, extracts parameter names and types, generates OpenAPI JSON, pushes to S3. This tells the AI what tools exist — but with bare parameter names like `originCountry: string`, the AI has no idea what to put there.

**Skill** is what you'll be writing. It's a Markdown file loaded into the AI's context that says things like: 'when someone says autopilot, use load_autopilot_rules. Thailand means TH. currency must be ISO 4217 uppercase.'

We measured the impact with 75 test cases across all domains:"

*[Point to the accuracy table]*

- Weak schema only: **44%** — the AI basically guesses
- Rich schema (good parameter descriptions): **78%** — +34%, biggest single win
- Rich schema + Skill routing: **87%** — +9% on top

"The key insight: good descriptions and routing guides take us from random to 87%, with zero code changes to the backend. This is purely a content investment."

### 1.4 What Files Exist (2 min)

"Right now we have 5 domain skills plus a shared gateway skill. Each domain has a SKILL.md and a parameter-standards.md. Pricing and demand have extra reference files for complex operations like the autopilot 5-field S3 key or booking PNR vs bookingId.

For supply, sysinteg, and 3PS — it's just SKILL.md + parameter-standards.md. Clean and simple.

This is the foundation we've built. Now we need each team to own and enrich their domain."

*[Move to Part 2]*

---

## Part 2: Demo (10 min)

### 2.1 Local CLI Setup (3 min)

"Let me show you what it actually looks like in practice. The setup is one command."

*[Open terminal]*

```bash
curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh
```

"That's it. It downloads all 7 skill files to your `~/.agents/skills/` directory. No CLI to install, no AWS credentials — just the skill files. The agent you already use — Copilot CLI, Claude Code, whatever — reads these files and knows how to route."

*[Wait for install to complete]*

### 2.2 Live Demo — Budget Query (3 min)

"Now let me ask it a real question."

*[Type: copilot "what is the THB budget balance?"]*

"Behind the scenes, here's what happens:

1. The agent reads the skill index — about 300 tokens, just skill names and descriptions
2. It matches 'budget' to fpr-pricing domain
3. It loads the pricing SKILL.md — about 2000 tokens, on demand
4. It finds `get_budget_balance` in the operations table
5. It reads parameter-standards.md — 'currency must be ISO 4217 uppercase' → fills 'THB'
6. It calls the Gateway with the right tool + params
7. Returns the formatted answer

The user doesn't need to know any of that. They just ask a question and get an answer."

*[Wait for response, show the output]*

### 2.3 More Examples (2 min)

"You can ask about anything we've covered in the skills:"

*[Point to the example queries table]*

- "What are Thailand autopilot rules?" → pricing → load_autopilot_rules
- "Show me booking 123456789 details" → demand → get_flight_info
- "Search GA fares CGK to DPS" → supply → search_regular_fare
- "Is the promo label feature flag on?" → sysinteg → get_feature_flag
- "What airlines fly to Bali?" → 3ps-datainfo → get_airline_routes

"The remote agent — Lark bot via AgentCore — is still being integrated. Raphael and Lingyan are working on that. But local CLI works today, and anything you write in your skill files is automatically picked up."

### 2.4 Try It Yourself (2 min)

"If you have your laptop, feel free to run the install command now and try a query from your own domain. I'll wait."

*[Pause for people to try]*

*[Move to Part 3]*

---

## Part 3: What Each Team Needs to Do (15 min)

### 3.1 Adding New APIs — exposed-ops.yaml (5 min)

"OK, so what do you actually need to do? There are two parts.

**Part A: Adding new APIs.** This is fully automated. You edit one YAML file."

*[Point to the exposed-ops.yaml example]*

```yaml
pricing:
  - id: my_new_operation
    path: my-domain/my-endpoint
    description: What this API does
```

"Submit a PR. On merge to main, CI automatically:
1. Clones fprtool-backend
2. Scans the Java source code
3. Extracts parameter names, types, and descriptions
4. Generates per-domain OpenAPI JSON
5. Pushes to S3
6. Gateway picks it up

No manual schema editing. No infrastructure work. Just YAML + PR.

For CRUD entities, it's even easier — use `crud/getEntryList(entityType)` and the script auto-discovers filter fields from the backend source."

*[Point to the CRUD example]*

"Branch strategy: main deploys to staging, release deploys to production. So you test on staging first, then merge to release when you're confident."

### 3.2 Writing Skills — The Main Ask (8 min)

"**Part B: Writing your Skill files.** This is the main ask, and this is where your domain expertise becomes AI intelligence."

*[Move to Part 4 — point to the file tree]*

"Each domain has this structure:

```
skills/domain/your-domain/
├── SKILL.md           # the main file
└── references/
    └── parameter-standards.md   # param types and normalization
```

For most domains, that's it. Two files. Pricing and demand have extra reference files for complex operations — but supply, sysinteg, and 3PS just need these two."

*[Scroll to the complete pricing template]*

"Now let me walk through the SKILL.md structure. It has 6 sections:

**1. Frontmatter** — name, version, description. The description field is critical — it's how the agent decides whether to load your skill. If someone says 'budget', the agent searches all skill descriptions and finds 'budgets' in pricing's description. So list ALL the keywords and topics your domain covers.

**2. Prerequisites** — what the agent must read before calling your tools. Always starts with fpr-shared for auth. Then point to your reference files. For most domains, it's just two lines: read fpr-shared, read parameter-standards.

**3. Operations Table** — every tool listed with description and key parameters. This is where the 34% accuracy gain lives. Instead of just `load_autopilot_rules`, you write 'Automated pricing rules by profile+currency — profileGroup, profileType, productType, profileName, currency'. The agent reads this and knows exactly what params to fill.

**4. Routing Guide** — this is the 9% gain. Map what users actually say to the right tool. 'Budget', 'remaining budget', 'budget left' → get_budget_balance. 'Markup', 'margin', 'base pricing' → load_baseline_pricing_rules. Include synonyms, abbreviations, even Chinese terms like '自动定价'. Only you know how your users phrase things — that's why this has to be domain-owned.

**5. Gotchas** — common traps that trip people up. 'ProfileGroup is an enum, not a country code.' 'AirlineId must be IATA 2-letter uppercase.' 'Autopilot uses a 5-field S3 key — misordered fields cause 500 errors.' The agent reads these and avoids making the same mistakes.

**6. Disambiguation** — what does NOT belong to your domain. 'Fare adjuster → supply, not pricing.' 'Feature flag → sysinteg, not pricing.' This prevents the agent from routing to the wrong domain.

And then **parameter-standards.md** is a separate reference file with the full normalization table: what inputs are accepted, what they normalize to, and key distinctions. Like 'Thailand / TH / th → TH'. 'Garuda / garuda → GA'. Plus reference codes — airline codes, country codes, profile group enums.

The pricing SKILL.md in the repo is a complete working example. Copy it, replace the content with your domain's operations, and you're most of the way there."

### 3.3 Optional: Javadoc (2 min)

"One thing that's changed since the original design — we used to ask teams to enrich Javadoc in the Java code. That's now optional. The parameter descriptions that matter live in your Skill files, not in Javadoc. If you want to add Javadoc for non-AI consumers, great, but it's not required for accuracy."

*[Move to Part 5]*

---

## Part 4: PIC & Timeline (8 min)

### 4.1 Effort Estimate (4 min)

"Here's the effort breakdown per domain:"

*[Point to the effort table]*

| Domain | Ops | Files | Effort |
|--------|-----|-------|--------|
| Pricing | ~35 | SKILL.md + 4 refs | ~5 days |
| Supply | ~25 | SKILL.md + 1 ref | 1-2 days |
| Demand | ~17 | SKILL.md + 2 refs | 1-2 days |
| SysInteg | ~6 | SKILL.md + 1 ref | 0.5-1 day |
| 3PS | ~20 | SKILL.md + 1 ref | ~1 day |

"Pricing is the biggest because it has 35 operations and 4 reference files. But remember — pricing is already done. You can look at it as the template.

For the other domains, it's 1-2 days of work. Most of the time goes into:
- Writing good operation descriptions (the +34% part)
- Mapping user intents in the routing guide (the +9% part)
- Documenting parameter normalization rules

The structure is already there. You're filling in domain-specific content, not building from scratch."

### 4.2 Ack Your Operations (2 min)

"Before you start writing, there's one thing I need from each team today — review your domain's full operation list in the Phase-1 Tool Scope doc."

*[Point to the Phase-1 Tool Scope callout]*

"Go through the table for your domain, and mark each operation as Acked or Phase-2. This confirms what's in scope for Phase-1 so we're all aligned. It should take 10-15 minutes per domain."

### 4.3 Next Steps (2 min)

"After this meeting:
1. **Confirm your PIC** — who on your team will own the skill enrichment
2. **Set up locally** — run the install script, try a query
3. **Study pricing SKILL.md** — it's the reference template
4. **Write your SKILL.md + parameter-standards.md** — follow the 6-section structure
5. **Test locally** — ask the agent real questions from your domain
6. **Submit a PR** — CI validates skill structure, deploys to staging
7. **Merge to release** — deploys to production"

---

## Closing (3 min)

"To summarize where we are:

**Done:**
- Architecture built and verified E2E
- CI auto-deploys schema + skills to S3
- Prod Gateway is live and operational
- 5 domain skills + shared skill deployed
- Local agent tested on real on-call queries
- Routing accuracy: 44% → 87%

**What we need from you:**
- Each team: write your SKILL.md + parameter-standards.md (1-5 days)
- Ack your operations in the Phase-1 Tool Scope doc (today)
- Nominate a PIC (today)

**Support:**
- Repo: github.com/lehan822/fpr-cortex
- Skill-maker template in the repo to help you get started
- Ping me on Lark for any questions

Let's spend the last few minutes figuring out PICs. Who's taking ownership for each domain?"

*[Open the Phase-1 Tool Scope doc for live ack]*

---

## Q&A (10 min)

Likely questions and prepared answers:

**Q: "Can PMs contribute without GitHub access?"**
A: Yes. Each domain has a Lark skill doc — PMs can edit routing guides, normalization rules, and gotchas directly there. An engineer syncs it to GitHub. The Lark doc links are in the Enrichment Guide.

**Q: "What if my API isn't in exposed-ops.yaml yet?"**
A: Add one line to the YAML file, submit a PR. CI auto-generates the schema from backend source and deploys. No manual schema work.

**Q: "How do I test my skill before merging?"**
A: Run the install script locally, then ask Copilot CLI a real question from your domain. If it picks the right tool and fills the right params, your skill is working.

**Q: "What about write operations?"**
A: Phase-1 is read-only. Write ops (update_autopilot_rules, create_promo_label, etc.) are Phase-2. But the skill structure is the same — just add them to the operations table when ready.

**Q: "Do I need to write Javadoc in the Java code?"**
A: No, that's optional now. Parameter descriptions live in the Skill files. Javadoc is nice-to-have for non-AI consumers but not required for accuracy.

**Q: "How does this work with the SysInteg MCP?"**
A: Same Gateway, same S3. We've converged — no separate systems. Skills and schema are stored in S3, CI auto-deploys on merge.

**Q: "What if the AI picks the wrong tool?"**
A: That's what the routing guide and eval test cases are for. If you see mis-routing in practice, add the missing keyword to your routing guide and add an eval test case. We'll run eval in CI to catch regressions.

**Q: "How often do skills need updating?"**
A: When you add a new API, rename an operation, or discover a new user intent pattern. The install script has version checking — when you push a new version, agents auto-update on next run.
