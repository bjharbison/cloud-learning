# Cloud Learning

A self-paced, multi-cloud curriculum for learning how to **set up, use, administer, monitor, and secure** cloud systems on **Google Cloud, AWS, and Microsoft Azure** — from novice to intermediate.

It is built for someone moving into cloud-facing security and architecture roles, not full-time sysadmin work:

- **Cyber threat intelligence** — how adversaries attack cloud environments and what telemetry exists to catch them
- **Cloud security** — identity, network controls, encryption, posture management, detection, incident response
- **Solutions architecture / customer engineering** — designing, scoping, and explaining secure cloud solutions, especially for public-sector and national-security customers

## Goals

1. Speak competently and accurately about cloud and cloud security in a technical interview.
2. Have a working baseline on day one in a role at Google, AWS, Microsoft, or a partner.
3. Keep a clear line between **knowledge I've studied** and **skills I've demonstrated** (labs completed, certifications earned) — so every resume claim is defensible.

## How the repo is organized

| Path | What's there |
|---|---|
| [`CURRICULUM.md`](CURRICULUM.md) | The full syllabus: 9 phases, 33 modules, and build status for each |
| [`PROGRESS.md`](PROGRESS.md) | My personal learning tracker — what I've studied, done hands-on, and can claim |
| [`modules/`](modules/) | One folder per module (built in scheduled batches, late Oct 2026) |
| [`reference/service-map.md`](reference/service-map.md) | Cross-cloud service equivalents (GCP ↔ AWS ↔ Azure) |
| [`reference/glossary.md`](reference/glossary.md) | Terms in plain language plus the vocabulary practitioners actually use |
| [`reference/certifications.md`](reference/certifications.md) | Certification roadmap across the three clouds |
| [`reference/lab-safety.md`](reference/lab-safety.md) | Free-tier, budget-alert, and cleanup rules — read before any lab |
| [`templates/module-template.md`](templates/module-template.md) | The structure every module follows |
| [`CLAUDE.md`](CLAUDE.md) | Authoring rules for the automated sessions that build modules |

## Every module contains

```
modules/NN-slug/
├── README.md      Lesson: plain-language first, then practitioner vocabulary,
│                  cross-cloud comparison, security + CTI angle
├── lab.md         Hands-on exercise on free tier, with cost warnings and cleanup
├── quiz.md        Self-check questions with a hidden answer key
└── interview.md   Likely interview questions, answer outlines, and
                   "what I can honestly claim" after this module
```

## How to use it

1. Read [`reference/lab-safety.md`](reference/lab-safety.md) and do **Module 00** first — it sets up accounts, MFA, and budget alerts on all three clouds.
2. Work the phases in order. Each module is roughly 2–4 hours including the lab.
3. Take the quiz before moving on. Update [`PROGRESS.md`](PROGRESS.md) honestly.
4. Use the interview file to practice out loud — whiteboard the diagrams, don't just read them.

## Ground rules

- **Nothing classified, CUI, proprietary, or employer-specific goes in this repo.** This repo is public.
- Product names, compliance authorizations, and free-tier limits change. Each module lists its sources and a "verified as of" date; check the official docs before quoting a fact in an interview.
- Labs run in my own personal accounts only. Offensive-security labs target only resources I own.

## License

Content is licensed under [CC BY 4.0](LICENSE).
