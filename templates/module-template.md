# Module template

Copy this structure into `modules/NN-slug/`. Four files.

---

## `README.md`

```markdown
# NN — Title

> **In one sentence:** <what this module makes you able to do>

**Prereqs:** modules NN, NN · **Time:** ~X hours incl. lab · **Phase:** N

## Learning objectives
- Explain …
- Configure …
- Compare …

## Why this matters for the target roles
2–4 bullets: CE/architect, security, CTI.

## Concepts
### <Concept 1>
Plain-language explanation → practitioner vocabulary (**bold** on first use) → one bridge to homelab/intel experience.

(repeat for each concept; short sections)

## Text diagram
ASCII diagram of the key architecture or flow.

## Google Cloud vs AWS vs Azure
| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|

## Administer and monitor it
What an admin actually touches day to day; where the logs and metrics for this live in each cloud.

## Security angle
Common misconfigurations, the controls that matter, shared-responsibility line.

## Threat intel angle
How adversaries abuse this; relevant MITRE ATT&CK techniques (IDs); public reporting worth reading.

## Public sector notes
Only where genuinely relevant.

## Key takeaways
5–7 bullets.

## Sources
- [Title](official-url)
Verified: YYYY-MM-DD
```

## `lab.md`

```markdown
# NN Lab — Title

**Cost:** $0 on free tier (details) · **Time:** X min · **Clouds:** GCP (required), AWS, Azure (optional parallels)

## Goal
## Prerequisites
## Part A — Google Cloud (console, then CLI)
## Part B — AWS equivalent
## Part C — Azure equivalent
## Verify it worked
## What to notice (reflection questions)
## Cleanup  ← mandatory, with commands and a final "nothing billable remains" check
## Write-up prompt
3–5 sentences to paste into PROGRESS.md notes or a lab journal — this is evidence for the claim ledger.
```

## `quiz.md`

```markdown
# NN Quiz — Title

1. Question…
<details><summary>Answer</summary>

Answer and one-line why.
</details>
```

Mix: definitions, compare-the-clouds, scenario ("an agency wants X — what do you recommend and why?"), and spot-the-misconfiguration.

## `interview.md`

```markdown
# NN Interview Prep — Title

## Likely questions
### Q1 …
**Answer outline:** 3–5 bullets. **Strong signal:** what makes an answer stand out. **Avoid:** common weak answers.

## 60-second executive explanation
A script for explaining this to a non-technical agency leader.

## Whiteboard prompt
One scenario to draw from memory.

## What you can honestly claim
- **After reading + quiz:** …
- **After completing the lab:** …
- **Still requires (cert / production experience / clearance):** …
```
