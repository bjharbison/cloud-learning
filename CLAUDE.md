# Authoring rules for this repo

This repo is a multi-cloud learning curriculum for Brian Harbison. Modules are written by scheduled, unattended Claude sessions. Follow these rules exactly.

## The learner

- ~20 years in national security: all-source intelligence, targeting, counterintelligence, cyber threat intelligence, OT/ICS security. M.S. Cyber Operations. Security+.
- Hands-on homelab background: Proxmox, OPNsense, Docker, VLAN segmentation, MQTT/InfluxDB/Grafana, local LLMs (Ollama), Python, Splunk.
- **Gap:** limited production cloud-platform experience. Treat him as a strong technical generalist who is new to cloud — skip "what is an IP address," don't skip "what is a VPC."
- Target roles: Google Public Sector Customer Engineer; cloud security; cloud CTI; solutions architect. **Not** full sysadmin.
- Reads on a phone a lot. Short paragraphs, short sections, scannable tables.

## Teaching style

1. **Plain language first, then practitioner vocabulary.** Introduce each term in bold the first time, with a one-line plain definition.
2. **Bridge from what he knows.** Map new ideas to his homelab and intel experience (e.g., VPC ↔ OPNsense VLANs; IAM policy ↔ need-to-know and compartments; Cloud Audit Logs ↔ Splunk sources). One good analogy per major concept, not five.
3. **Three clouds side by side.** Google Cloud first, then AWS, then Azure. Every module has a comparison table. Call out real differences, not just name swaps.
4. **Every module has a security angle and a CTI angle.** What can go wrong, what an adversary does here, what telemetry exists.
5. **Public-sector hooks** where they're genuine (gov regions, compliance, mission constraints). Don't force them.
6. **Shared responsibility reinforcement:** identity, access control, firewall rules, VPN configuration, and SSH/RDP exposure are always the customer's responsibility. Say so whenever it's relevant.

## Accuracy — non-negotiable

- **Verify every product name, feature, limit, price, free-tier detail, compliance authorization, and CLI flag with web search against official docs** (cloud.google.com, docs.aws.amazon.com, learn.microsoft.com, fedramp.gov, etc.) before writing it. Products get renamed constantly.
- Put a `Sources` section at the end of each module README with links and `Verified: YYYY-MM-DD`.
- If something can't be verified, leave it out or mark it `⚠️ unverified`.
- Paraphrase sources. No copied passages.
- No classified, CUI, or employer-specific content. Public information only.

## Honesty about claims

Every `interview.md` ends with a **What you can honestly claim** section in three tiers:
- After reading + quiz → "I've studied X and can discuss Y."
- After completing the lab → "In a personal lab I've configured X."
- What still requires a cert, production experience, or a clearance — say so plainly.

Never write resume language that implies production or professional cloud experience he doesn't have.

## Module structure

Each module lives in `modules/NN-slug/` (folder names are fixed in `CURRICULUM.md`) and has exactly four files. Follow `templates/module-template.md`.

| File | Contents | Target length |
|---|---|---|
| `README.md` | Lesson | 1,500–3,000 words |
| `lab.md` | Hands-on lab, free-tier, all three clouds where feasible (GCP mandatory) | Step-by-step, console **and** CLI |
| `quiz.md` | 8–12 questions, mixed formats, answers in `<details>` blocks | |
| `interview.md` | 4–6 likely questions with answer outlines, a 60-second "explain it to an exec" script, and the claim tiers | |

### Lab rules

- Start every lab with: estimated cost (target $0 on free tier/credits), time required, prerequisites.
- Always end with a **Cleanup** section that deletes everything created, with commands, and a step to confirm nothing billable remains.
- Prefer Cloud Shell / CloudShell / Azure Cloud Shell so nothing needs installing.
- Never open SSH/RDP to `0.0.0.0/0` without immediately explaining why that's bad and showing the safer option (IAP, Session Manager, Bastion).
- Offensive or attack-emulation steps only against resources in the learner's own account, using recognized open-source tools.

## Batch workflow (what each scheduled build does)

Modules are built in batches by scheduled runs. Each run's prompt names its modules.

1. Read this file, `CURRICULUM.md`, `PROGRESS.md`, `templates/module-template.md`, everything in `reference/`, and every module already in `modules/` (keep continuity, build on what came before, don't repeat it).
2. Build the modules named in the run, in order. If an **earlier** module is still ⬜, build it first. Skip any module already 🟦/✅ with all four files present.
3. Research with web search against official docs. Write the four files.
4. Append new cross-cloud equivalents to `reference/service-map.md` and new terms to `reference/glossary.md` (keep the glossary alphabetical).
5. Flip the module's Build marker ⬜ → 🟦 in `CURRICULUM.md`. Never touch ✅ markers or `PROGRESS.md` — those are the learner's.
6. Self-check: links go to official domains, every comparison table covers all three clouds, every lab has complete cleanup, every interview file has the claim tiers, nothing unverified is presented as fact.
7. Commit each module as `Add module NN: <title>`, fetch and rebase, push to `main`. Never force-push.
8. After the batch, an independent reviewer agent (one that didn't draft the content) checks accuracy, sequencing, lab safety, and claim honesty. Fix what holds up, commit `Fix review findings for modules NN–NN`, push.

The learner flips 🟦 → ✅ after working through a module, or a later review run does after re-verifying facts.
