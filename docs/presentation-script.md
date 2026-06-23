# FPR Cortex Skill Onboarding — Presentation Script

> ~20 minutes total. Casual, conversational tone. Screen-share the Lark doc throughout.

---

## Opening (1 min)

"Hey everyone, thanks for coming. Quick context — we've been building something called FPR Cortex over the past few weeks. It's basically a way for AI agents like Copilot CLI, Claude Code, or Lark bots to call our FPR APIs directly, without us engineers manually opening Postman.

Today I want to walk you through four things: what it is, a quick demo, what each team needs to do, and how long it'll take. Should be about 20 minutes."

*[Share screen: Lark doc — Part 1]*

---

## Part 1: Architecture Overview (5 min)

### 1.1 Problem

"Let's start with the problem. Today, if someone wants to check Thailand autopilot rules or look up a budget balance, they ping us on Lark. We open Postman, find the right API, fill in parameters, copy-paste the result back. It's slow and it blocks on engineer availability.

The goal is simple — let users ask an AI agent the same question, and the agent figures out which API to call and how to fill the params."

*[Point to the before/after grid in the doc]*

### 1.2 Core Challenge

"The core challenge here is routing accuracy. When someone says 'check autopilot pricing rules for Thailand' — how does the AI know which API to call? We have 88 operations across 5 domains. That's not trivial.

*[Point to the whiteboard diagram]*

Our key metric is: given a natural language intent, does the AI pick the right operation and fill the correct parameters?"

### 1.3 Why Schema + Skill

"We solved this with two layers. Schema is auto-generated from our backend code — it tells the AI what tools exist. Skill is what you'll be writing — it tells the AI how to choose the right tool.

The results were pretty convincing. With weak schema descriptions, the AI got 44% accuracy. After enriching parameter descriptions, it jumped to 78%. And after adding Skill routing guides on top, we hit 87%.

That's the key takeaway — good descriptions and routing guides take us from basically random to 87% accuracy, with zero code changes to the backend."

### 1.4 What Files Exist

"Right now we have 5 domain skills plus a shared gateway skill. Pricing, supply, demand, sysinteg, and 3PS. Each domain has a SKILL.md and a parameter-standards.md. Pricing and demand have a few extra reference files for complex operations.

This is what we've already built. Now we need each team to own and enrich their domain."

*[Move to Part 2]*

---

## Part 2: Demo (4 min)

### 2.1 Local CLI Setup

"Let me show you what it actually looks like. The setup is one command — just curl the install script and it pulls down all the skill files."

*[Open terminal, run: curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh]*

"That's it. It installs 7 skills to your local machine. No CLI to install, no AWS credentials — just the skill files."

### 2.2 Live Demo

"Now let me ask it a real question."

*[Type: copilot "what is the THB budget balance?"]*

"Behind the scenes, the agent reads the skill index, matches 'budget' to the pricing domain, loads the pricing SKILL.md, finds the get_budget_balance tool, normalizes the currency parameter, and calls the Gateway.

The user doesn't need to know any of that. They just ask a question and get an answer."

*[Wait for response]*

"You can also search fares, look up bookings, check feature flags — anything we've covered in the skills. The example queries table in the doc shows a few more."

*[Point to the example queries table]*

"The remote agent — Lark bot via AgentCore — is still being integrated. Raphael and Lingyan are working on that. But local CLI works today."

*[Move to Part 3]*

---

## Part 3: What Each Team Needs to Do (6 min)

### 3.1 Adding Operations

"OK, so what do you actually need to do? There are two parts.

First — adding new APIs. This is fully automated. You just add one line to exposed-ops.yaml in the repo, submit a PR, and CI does the rest. It clones the backend, scans the Java source, generates the OpenAPI schema, and pushes it to S3. The Gateway picks it up automatically.

No manual schema editing, no infrastructure work. Just YAML + PR."

*[Point to the exposed-ops.yaml example in the doc]*

"For CRUD entities, it's even simpler — just use the crud/getEntryList format and the script auto-discovers filter fields from the backend."

### 3.2 Writing Skills

"Second — and this is the main ask — writing your Skill files. This is where your domain expertise becomes AI intelligence.

Let me show you the structure using pricing as an example."

*[Move to Part 4 — point to the file tree]*

"Each domain has a SKILL.md and a references folder with parameter-standards.md. That's it for most domains. Pricing and demand have extra reference files because they have complex operations like the autopilot 5-field S3 key."

*[Scroll to the complete pricing template]*

"The SKILL.md has 6 sections. Let me walk through them quickly:

1. **Frontmatter** — name, version, description. The description is critical — it's how the agent discovers your skill. List all the keywords your domain covers.

2. **Prerequisites** — what the agent must read before calling your tools. Always starts with fpr-shared for auth. Then your reference files.

3. **Operations Table** — every tool listed with description and key parameters. This is where the 34% accuracy gain comes from. Good parameter descriptions matter.

4. **Routing Guide** — maps what users actually say to the right tool. 'Budget', 'remaining budget', 'budget left' all map to get_budget_balance. This is the 9% gain. Only you know how your users phrase things.

5. **Gotchas** — common traps. 'AirlineId is case-sensitive', 'bookingId must be integer not string'. Stuff that trips people up.

6. **Disambiguation** — what does NOT belong to your domain. 'Fare adjuster goes to supply, not pricing.' Prevents mis-routing.

And then parameter-standards.md is a separate file with type constraints and normalization rules — like 'currency must be ISO 4217 uppercase, airlineId must be IATA 2-letter'.

The pricing SKILL.md in the repo is a working example with all sections filled. You can copy it as a starting point."

*[Move to Part 5]*

---

## Part 4: PIC & Timeline (3 min)

### 4.1 Effort Estimate

"Here's the effort breakdown. Pricing is the biggest — about 35 operations, 4 reference files, roughly 5 days. Supply and demand are 1-2 days each. SysInteg is half a day to a day since it's only 6 ops. 3PS is about a day.

Most of the time goes into writing good operation descriptions, routing guides, and parameter standards. The template is already there — you just fill in your domain-specific content."

*[Point to the effort table]*

### 4.2 Ack Your Operations

"Before you start writing, please review your domain's full operation list in the Phase-1 Tool Scope doc and mark each one as Acked or Phase-2. This confirms the scope so we're all aligned on what's in and what's out."

*[Point to the Phase-1 Tool Scope callout]*

### 4.3 Next Steps

"After this meeting:
1. Confirm your PIC — who on your team will own the skill enrichment
2. Run the install script to set up your local environment
3. Study the pricing SKILL.md as a reference template
4. Write your SKILL.md and parameter-standards.md
5. Test locally with real queries
6. Submit a PR — CI validates and deploys to staging
7. Merge to release when ready for production"

---

## Closing (1 min)

"To summarize — the framework is built, CI auto-deploys, the Gateway is live in production. What we need from each team is content: good descriptions, routing guides, and parameter standards. About 1 to 5 days per domain depending on scope.

The repo is github.com/lehan822/fpr-cortex. Ping me on Lark if you have questions. There's also a skill-maker template in the repo to help you get started.

Thanks everyone — let's figure out the PICs now."

*[Open the Phase-1 Tool Scope doc for live ack]*

---

## Q&A Buffer (5 min)

Likely questions:
- **"Can PMs contribute without GitHub?"** — Yes, each domain has a Lark skill doc. Edit there, eng syncs to GitHub.
- **"What if my API isn't in exposed-ops.yaml yet?"** — Add it, one line in YAML, PR, CI auto-deploys.
- **"How do I test my skill?"** — Run the install script, then ask Copilot CLI a real question from your domain.
- **"What about write operations?"** — Phase-1 is read-only. Write ops are Phase-2.
- **"Do I need to write Javadoc?"** — No, that's optional now. Parameter descriptions live in the Skill files.
