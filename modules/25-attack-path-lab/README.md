# 25 — Attack-path lab (purple team): emulate cloud TTPs in my own account and detect them

> **In one sentence:** you'll be able to plan and run a small, safe **purple-team** exercise in a throwaway cloud project — emulate real attacker techniques with an open-source tool, find each one in the audit logs, test whether your detections fire, and report the gaps.

**Prereqs:** modules 00–24 (module 18 for log anatomy; 22 for the detections you'll test; 23 for evidence and containment; 24 for the TTPs you're emulating) · **Time:** ~4 hours incl. lab · **Phase:** 6

## Learning objectives

- Explain **purple teaming**, **adversary emulation**, and **detection validation**, and how they differ from a penetration test.
- Write **rules of engagement** for cloud emulation in your own account, including what's off-limits.
- Use **Stratus Red Team** to warm up, detonate, and clean up cloud techniques.
- Map each technique to **ATT&CK**, the **audit-log event** it produces, and whether that log is on by default.
- Score detection coverage and turn gaps into backlog items.

## Why this matters for the target roles

- **Cloud security / detection:** a rule that has never fired against a real behavior is a hypothesis. Emulation turns it into evidence.
- **CTI:** this closes the loop from module 24 — reporting becomes requirements, requirements become tested detections.
- **Customer engineer:** "How do we know our detections work?" is a common customer question. A safe, repeatable emulation plan is a strong answer, and a good proof-of-concept design.

---

## Concepts

### Red, blue, purple

| Term | Plain meaning | Goal |
|---|---|---|
| **Penetration test** | Testers try to break in and report what they found | Find exploitable weaknesses |
| **Red team** | A realistic adversary campaign, often without the defenders knowing | Test people, process, and tech end to end |
| **Purple team** | Attack and defense work side by side, technique by technique | Improve detection and response, fast |
| **Adversary emulation** | Reproducing a specific actor's known techniques | Test against the threats you actually face |
| **Detection validation** | Running a behavior to prove a rule fires (or doesn't) | Coverage you can show, not assume |

**Bridge from intel:** purple teaming is a **red-cell exercise against your own I&W**. You know the indicator list; now you run the observable and see whether the warning arrives, how fast, and with what context.

### Emulation vs simulation

- **Emulation** performs the real API calls an attacker would make — real `CreateServiceAccountKey`, real `DeleteSink`. The logs are genuine.
- **Simulation** injects fake log events or replays recorded ones. Safer and cheaper, but it tests only the rule, not log delivery.

In cloud, emulation is usually safe *if* you control the blast radius: a **dedicated project or account**, nothing shared outside it, and everything torn down afterward.

### Rules of engagement (ROE)

Write these down before running anything. The ROE for this module:

1. **Scope:** one new, dedicated Google Cloud project (and optionally a separate AWS sandbox account). Nothing else.
2. **Identities:** only your own lab admin identity and service accounts created inside the lab project.
3. **No external principals.** Skip any technique that grants access to an outside account, shares disks, images, or snapshots, or invites users. Some tools default to a maintainer-owned "attacker" account — never use those techniques here.
4. **No organization-level actions,** and nothing that targets other projects, other people's resources, or provider infrastructure.
5. **Cost cap:** IAM, logging, and small storage techniques only — no compute, GPUs, or notebooks.
6. **Cleanup:** tool cleanup, then delete the whole project, then verify.

**Provider policies:** Google says customers don't need to notify it before testing their own Google Cloud resources, but must follow the Acceptable Use Policy. AWS allows testing of listed services in your own account without prior approval, under its penetration testing policy. Microsoft dropped pre-approval in 2017 but requires its Rules of Engagement. Emulating control-plane API calls in your own project is well inside all three.

### The tool: Stratus Red Team

**Stratus Red Team** is an open-source, Apache-licensed tool from Datadog — "Atomic Red Team for the cloud." As of late October 2026 the current release is **v2.37.2**, and it's actively maintained.

- Covers **AWS, Google Cloud, Azure, Entra ID, Kubernetes,** and **EKS**. Each technique has an ID like `gcp.persistence.create-service-account-key`, grouped by ATT&CK tactic.
- **Lifecycle:** `warmup` creates prerequisites (via Terraform it downloads itself) → `detonate` performs the attack → `revert` undoes the attack → `cleanup` removes everything. `status` shows COLD / WARM / DETONATED.
- **Auth:** on Google Cloud it uses Application Default Credentials and the `GOOGLE_PROJECT` environment variable. State lives in `~/.stratus-red-team/`.
- Its docs tell you to run it **only in a sandbox account** — the same principle as this module's ROE.

**Alternatives worth knowing:** **Atomic Red Team** (Red Canary) has cloud tests, mostly for AWS and Azure. For Azure and Entra ID, **MicroBurst** (NetSPI) and **ROADtools** are common open-source assessment tools. Commercial **breach and attack simulation (BAS)** platforms do the same at scale.

### Choosing techniques for this lab

From the 25 Google Cloud techniques Stratus offers, the lab uses five that are cheap, confined to the project, and need no external account:

| Stratus technique | What it does | ATT&CK | Log event (Google Cloud) | Default on? |
|---|---|---|---|---|
| `gcp.persistence.create-admin-service-account` | Creates an SA and grants it Owner | T1136.003 Create Cloud Account; T1098.003 | `CreateServiceAccount`, `SetIamPolicy` (Admin Activity) | Yes |
| `gcp.persistence.create-service-account-key` | Creates a key for an existing SA | T1098.001 | `google.iam.admin.v1.CreateServiceAccountKey` (Admin Activity) | Yes |
| `gcp.privilege-escalation.impersonate-service-accounts` | Tries to impersonate 10 SAs; one succeeds | T1548.005 Temporary Elevated Cloud Access | `GenerateAccessToken` (**Data Access**, iamcredentials) | **No** |
| `gcp.defense-evasion.delete-logging-sink` | Deletes a log sink | T1685.002 | `google.logging.v2.ConfigServiceV2.DeleteSink` (Admin Activity) | Yes |
| `gcp.credential-access.secretmanager-retrieve-secrets` | Lists secrets and reads each one | T1555.006 Cloud Secrets Management Stores | `AccessSecretVersion` (**Data Access**) | **No** |

ATT&CK IDs are this module's mapping — Stratus's pages give the tactic, not always the technique ID.

**Excluded on purpose:** `share-compute-disk`, `share-compute-image`, `share-compute-snapshot`, `invite-external-user`, and `backdoor-service-account-policy` (all grant access to an outside "attacker" account); `remove-project-from-organization` (org-level); and anything that creates VMs, GPUs, or notebooks (cost).

### Detection coverage, scored honestly

For each technique, record one of four outcomes — a simple scale many purple teams use:

| Outcome | Meaning |
|---|---|
| **Detected** | A deployed rule fired with useful context |
| **Logged only** | The event is in the logs but no rule fired — a hunt would find it |
| **Not logged** | No telemetry (for example, Data Access was off) — invisible |
| **Prevented** | A guardrail blocked it (for example, an org policy) |

"Logged only" is the most common result, and the most useful one: it's a detection backlog item with the data already in hand.

---

## Text diagram — the purple-team loop in one project

```
   ┌──────────────── dedicated project: lab25-purple-xxxx (deleted at the end) ───────────────┐
   │                                                                                           │
   │  RED (you, via Stratus)          LOGS (module 18)                 BLUE (you, module 22)    │
   │  warmup → detonate ──────► Admin Activity (always on) ─────► log-based alert policies    │
   │                       └──► Data Access (enabled first) ──┐                │               │
   │                                                          └─► gcloud logging read hunts    │
   │  revert / cleanup ◄────────── scorecard: Detected / Logged only / Not logged ◄─┘          │
   └───────────────────────────────────────────────────────────────────────────────────────────┘
            No external principals · no org-level actions · no compute · project deleted
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Disposable blast radius | New **project** (delete = 30-day pending deletion) | Separate **account** (needs AWS Organizations, which ends the free plan — module 00) | Separate **subscription** or resource group | Google projects are the cheapest sandbox |
| Stratus coverage | 25 techniques | Largest set (incl. EC2, IAM, S3, CloudTrail) | Azure and Entra ID techniques | |
| Provider testing policy | No notice needed for own resources; follow AUP | Listed services allowed without approval; policy page | No pre-approval since 2017; Rules of Engagement | All prohibit attacking other customers or provider infrastructure |
| Built-in detections to test | SCC Event Threat Detection (Premium/Enterprise), log-based alerts | GuardDuty (e.g., `Stealth:IAMUser/CloudTrailLoggingDisabled`) | Defender for Cloud alerts; Sentinel analytics | AWS's GuardDuty trial makes managed-detection testing easiest |
| Logs off by default that hide techniques | Data Access (impersonation, secret reads, storage reads) | Data events (S3 reads, Lambda invokes) | Resource logs; Entra logs beyond 7/30 days | Same lesson everywhere |

## Administer and monitor it

- Keep a **technique library**: technique ID, ATT&CK ID, expected log event, detection rule, last test date, outcome.
- **Re-run on change:** after a parser update, a new SIEM, or a log-routing change, re-detonate the core set. This is **continuous detection validation**.
- Watch for **tool residue:** Stratus keeps Terraform state in `~/.stratus-red-team/`. A failed cleanup can leave resources behind, which is why this lab deletes the whole project.

## Security angle

- **Blast radius is the control.** Never run emulation in a project that holds real data or real credentials.
- **Tool defaults can reach outside your account.** Read `stratus show <id>` before each detonation. Several techniques share resources with an external principal by default.
- **The emulation identity is powerful.** It needs near-Owner rights in the sandbox. Use your lab admin, not a long-lived key, and never reuse it elsewhere.
- **Expect your own alerts.** Detonation should trigger your module 22 rules — and possibly provider detections. That's the point; note what fired.

> **Shared responsibility — say it plainly:** providers supply the logs and some managed detections. **Choosing which logs to enable, writing and testing detections, and running exercises like this are always the customer's** — as are the identity, firewall, and access settings the techniques abuse.

## Threat intel angle

| Module 24 case | Technique you'll emulate | Why it maps |
|---|---|---|
| Scattered Spider (AA23-320A) | Create admin SA; SA key | Persistence via new cloud identities and credentials |
| Midnight Blizzard | Create admin SA / role grant | New identities and elevated roles after initial access |
| UNC6395 (Salesloft Drift) | Retrieve secrets | Harvesting stored credentials to pivot |
| Many actors (DET0289) | Delete logging sink | Blinding the defender (T1685.002) |
| SA impersonation abuse | Impersonate SAs | Privilege escalation that only Data Access logs show |

**CTI loop:** after the lab, your scorecard tells you which reported TTPs your environment would miss. That's an intelligence gap — write it up as one.

## Public sector notes

- Federal agencies run assessments under CISA services and their own red teams; **continuous monitoring** under FedRAMP and RMF (module 26) increasingly expects evidence that detections work, not just that logs exist ⚠️ (no specific mandate for emulation verified this run).
- Always get written authorization (an ROE signed by the system owner) before emulating in any customer environment. In your own personal project, you are the system owner.

## Key takeaways

- **Purple teaming** = attack and defend together, technique by technique, to improve detection.
- Emulate in a **dedicated project**, with written ROE: no external principals, no org-level actions, cost-capped, fully deleted.
- **Stratus Red Team** (v2.37.2, late Oct 2026): `warmup → detonate → revert → cleanup`; read `show` first.
- Some techniques are **invisible without Data Access logs** — impersonation and secret reads among them.
- Score each technique: Detected / Logged only / Not logged / Prevented. "Logged only" is your backlog.
- Re-run the core set whenever logging or detections change.

## Sources

- Stratus Red Team: [Getting started](https://stratus-red-team.cloud/user-guide/getting-started/), [Commands](https://stratus-red-team.cloud/user-guide/commands/), [GCP techniques](https://stratus-red-team.cloud/attack-techniques/GCP/), [AWS techniques](https://stratus-red-team.cloud/attack-techniques/AWS/), [FAQ](https://stratus-red-team.cloud/faq/), [Comparison with other tools](https://stratus-red-team.cloud/comparison/), [GitHub releases (v2.37.2)](https://github.com/DataDog/stratus-red-team/releases/tag/v2.37.2)
- Other tools: [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team), [MicroBurst](https://github.com/NetSPI/MicroBurst), [ROADtools](https://github.com/dirkjanm/roadtools)
- Google Cloud: [Configure Data Access audit logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access), [IAM Credentials audit logging](https://docs.cloud.google.com/iam/docs/audit-logging/audit-logging-iamcreds), [Create and manage projects](https://docs.cloud.google.com/resource-manager/docs/creating-managing-projects), [Delete and restore projects](https://docs.cloud.google.com/resource-manager/docs/delete-restore-projects), [Cloud Security FAQ (penetration testing)](https://support.google.com/cloud/answer/6262505), [Acceptable Use Policy](https://cloud.google.com/terms/aup)
- AWS: [Penetration testing policy](https://aws.amazon.com/security/penetration-testing/), [GuardDuty finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html)
- Microsoft: [Penetration testing (Azure)](https://learn.microsoft.com/en-us/azure/security/fundamentals/pen-testing)
- MITRE ATT&CK: [T1136.003](https://attack.mitre.org/techniques/T1136/003/), [T1098.001](https://attack.mitre.org/techniques/T1098/001/), [T1548.005](https://attack.mitre.org/techniques/T1548/005/), [T1555.006](https://attack.mitre.org/techniques/T1555/006/), [T1685.002](https://attack.mitre.org/techniques/T1685/002/), [DET0289](https://attack.mitre.org/detectionstrategies/DET0289/)

Verified: 2026-10-29
