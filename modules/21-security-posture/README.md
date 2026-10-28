# 21 — Security posture management: Security Command Center, Security Hub and GuardDuty, Defender for Cloud; CSPM/CNAPP; CIS benchmarks

> **In one sentence:** you'll be able to explain what posture management tools do (and don't do), compare Google Security Command Center, AWS Security Hub and GuardDuty, and Microsoft Defender for Cloud — including which parts are free — and walk a misconfiguration finding from detection to a closed ticket.

**Prereqs:** modules 00–20 (module 20 for guardrails and drift; module 18 for audit logs; modules 08, 11, 14 for the misconfigurations these tools find) · **Time:** ~3.5 hours incl. lab · **Phase:** 5

## Learning objectives

- Define **CSPM**, **CWPP**, **CIEM**, **DSPM**, and **CNAPP** in plain language.
- Distinguish **posture findings** (misconfigurations) from **threat findings** (something bad is happening).
- Compare **Security Command Center**, **AWS Security Hub / Security Hub CSPM / GuardDuty**, and **Microsoft Defender for Cloud** — tiers, what's free, and what each costs to try.
- Explain **CIS Benchmarks** (levels, versions, why tools lag) and how compliance views map to them.
- Run an open-source posture scan and turn one finding into a well-formed ticket.

## Why this matters for the target roles

- **Customer engineer:** "Show me my security posture across all projects" is a first-meeting question. Knowing the current SCC tiers — which changed in 2026 — keeps you credible.
- **Cloud security:** posture management is the detective control behind every guardrail from module 20; it finds the ClickOps and the drift.
- **CTI:** misconfiguration and weak credentials remain major initial-access vectors in Google's own threat reporting. Attackers run the same scanners you do.

---

## Concepts

### What posture management is

**Plain version:** a tool that continuously inspects your cloud settings and tells you which ones are risky — a public bucket, SSH open to the internet, a service account with Owner, MFA not enforced.

**Bridge from your background:** it's a vulnerability scanner (think Nessus) for **configuration** instead of software versions — or a standing inspection team that walks every room daily with a checklist. CIS Benchmarks are the checklist.

**Practitioner vocabulary:**

| Term | Plain meaning |
|---|---|
| **CSPM** (cloud security posture management) | Continuous checks of cloud configuration against best practice and compliance frameworks |
| **CWPP** (cloud workload protection platform) | Protecting what runs: VMs, containers, serverless — malware, vulnerabilities, runtime threats |
| **CIEM** (cloud infrastructure entitlement management) | Finding excess permissions and risky identity paths (module 14's least-privilege problem at scale) |
| **DSPM** (data security posture management) | Discovering where sensitive data lives and who can reach it |
| **CNAPP** (cloud-native application protection platform) | The umbrella: CSPM + CWPP + CIEM + DSPM + code/IaC scanning in one product |
| **Finding** | One detected issue on one resource, with severity, category, and remediation |
| **Toxic combination / attack path** | Several individually moderate findings that together create a real path to a crown jewel (public VM + over-privileged SA + reachable sensitive bucket) |

**Posture vs threat:** a posture finding says "this door is unlocked." A threat finding says "someone just walked through it." The products bundle both, but they come from different data: posture from **configuration and asset inventory**; threats from **logs and runtime telemetry** (module 18). Module 22 covers turning threat signals into detections.

### Google Cloud: Security Command Center (SCC)

**Tiers as of October 2026** — this changed this year, so check before any customer conversation:

| Tier | Status | What it adds |
|---|---|---|
| **Standard** / **Standard-legacy** | Free | Basic posture. **Standard** (organization-level, the new feature set since 2026) includes **Compliance Manager's "Security Essentials"** controls and vulnerability assessment; **Standard-legacy** is the older feature set that existing activations are being migrated from ⚠️ (Google's pages describe project-level Standard activations inconsistently; check the current tier page). |
| **Premium** | Paid (subscription or pay-as-you-go at org level; pay-as-you-go only at project level) | **Event Threat Detection** (log-based threats), **Container Threat Detection**, **VM Threat Detection**, full **Security Health Analytics**, **Web Security Scanner**, vulnerability assessment; at **org level**: **attack path simulations**, **security posture** service, compliance reporting |
| **Enterprise** | **Deprecated May 21, 2026**; shuts down on or after May 21, 2027, moving customers to Premium | Was the "multi-cloud CNAPP" tier (AWS/Azure collection, Google SecOps integration, CIEM) |

Key facts:

- **Security Health Analytics (SHA)** is SCC's built-in misconfiguration scanner. Finding categories you'll recognize: `PUBLIC_BUCKET_ACL`, `OPEN_SSH_PORT`, `OPEN_RDP_PORT`, `USER_MANAGED_SERVICE_ACCOUNT_KEY`, `MFA_NOT_ENFORCED`, `DEFAULT_NETWORK`, `AUDIT_LOGGING_DISABLED`. In 2026 Google moved several detectors (e.g., open firewall and open SSH/RDP) into Compliance Manager controls, and new Standard activations no longer get SHA the way they used to ⚠️ (Google's pages disagree on Standard-tier SHA coverage; check the current tier page).
- **Activation needs an organization** — even a project-level activation requires the project to belong to one. No-org personal projects can't use SCC (module 03 Path 2).
- **Premium trial:** 30 days for a project-level activation, then it **converts to pay-as-you-go automatically** unless you downgrade. Calendar it.
- **Export:** `gcloud scc notifications create` streams findings to **Pub/Sub** (to a ticketing function or SIEM); `gcloud scc findings list` queries them.
- **Also retiring:** SCC's DSPM feature (shuts down on or after February 1, 2027).
- **Wiz:** Google completed its acquisition of **Wiz**, a multicloud CNAPP, in **March 2026**. Wiz continues to support AWS, Azure, and other clouds; how it will relate to SCC isn't stated in the announcement — don't speculate in an interview.

### AWS: Security Hub, Security Hub CSPM, GuardDuty

AWS reorganized its security products in late 2025:

- **AWS Security Hub** (the **new** unified product, GA **December 2025**) correlates signals from GuardDuty, Inspector, Macie, and Security Hub CSPM into **exposure findings** and **attack path** views, in **OCSF** format, with **Jira Cloud** and **ServiceNow** ticketing. Doesn't require AWS Config. 30-day free trial of its Essentials plan.
- **AWS Security Hub CSPM** is the **original** Security Hub, renamed. It runs posture checks against **security standards** — AWS Foundational Security Best Practices (FSBP), **CIS AWS Foundations Benchmark** (v1.2.0, v1.4.0, v3.0.0, v5.0.0; AWS recommends v5.0.0), NIST SP 800-53 Rev. 5, PCI DSS. It **requires AWS Config recording**, uses the older **ASFF** finding format, and bills per security check after a 30-day trial.
- **Amazon GuardDuty** is the **threat detection** service: it reads CloudTrail management events, VPC Flow Logs, and DNS logs on its own (you don't need to turn those on for it), with optional **protection plans** (S3, EKS, Runtime Monitoring, Malware Protection, RDS, Lambda, AI). **Extended Threat Detection** (on by default) correlates events into **attack sequence** findings such as `AttackSequence:IAM/CompromisedCredentials`. Classic examples: `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS` (instance credentials used from outside AWS — module 05's metadata theft) and `CryptoCurrency:EC2/BitcoinTool.B!DNS`. 30-day free trial.
- **Free plan warning:** AWS's new-account **Free plan** doesn't support GuardDuty or Security Hub; you must upgrade to the paid plan (module 00). AWS Config and CloudTrail are available on the Free plan.

### Azure: Microsoft Defender for Cloud

Microsoft describes Defender for Cloud as a **CNAPP** made of CSPM, CWPP, and DevSecOps:

- **Foundational CSPM — free:** **secure score**, **recommendations**, the **Microsoft cloud security benchmark (MCSB)** as the default standard (v1 assessed by default; v2 in preview), asset inventory, and **connectors for AWS and Google Cloud**.
- **Defender CSPM — paid** (per billable resource per month, 30-day trial): **attack path analysis**, **cloud security explorer** (graph queries), **governance rules** (owners + due dates), regulatory compliance dashboards, **CIEM**, **DSPM**, AI security posture.
- **Workload plans (CWPP):** e.g., **Defender for Servers Plan 1/2** (EDR via Defender for Endpoint; Plan 2 adds agentless vulnerability and secrets scanning, file integrity monitoring, just-in-time VM access), plus Storage, Databases, Containers, and others.
- **Direction of travel:** cloud posture is moving into the **Microsoft Defender portal** and **Microsoft Security Exposure Management**; onboarding is still in the Azure portal.

### CIS Benchmarks

- Consensus configuration checklists from the **Center for Internet Security**. Current cloud versions on cisecurity.org: **Google Cloud Platform Foundation 5.0.0**, **AWS Foundations 7.1.0**, **Microsoft Azure Foundations 6.0.0** (plus GKE, EKS, AKS benchmarks).
- **Level 1:** baseline, low operational impact. **Level 2:** defense in depth for high-security environments; can break things if applied blindly.
- **Free PDF for non-commercial use**; machine-readable formats are for CIS SecureSuite members.
- **Tools lag the benchmarks:** SCC's CIS posture template is v2.0.0; Security Hub CSPM tops out at CIS AWS v5.0.0. When a customer says "we're CIS compliant," ask "which version, checked by what?"
- Provider benchmarks (Google's **security baseline**, AWS **FSBP**, Microsoft **MCSB**) often cover newer services sooner than CIS.

### From finding to closed ticket

A finding nobody owns is noise. The workflow:

```
 Detect ──► Triage ──► Assign ──► Remediate ──► Verify ──► Close
 (scanner)  severity ×  owner from   fix in CODE    rescan shows   or: exception
            exposure ×  labels/tags  (module 20),   PASS           with expiry +
            asset value              not console                   risk owner (POA&M)
```

1. **Triage:** severity alone misleads. A "high" on an isolated dev project matters less than a "medium" that's part of an attack path to production data. Toxic-combination and attack-path features exist for this.
2. **Deduplicate and route:** one ticket per root cause, not per resource. Use **labels/tags** (module 04) to find the owner.
3. **Ticket content:** resource, finding category, evidence, why it matters (attack path, ATT&CK), the fix, an SLA by severity, and how to verify.
4. **Fix in code** where the resource is Terraform-managed — otherwise the next apply reintroduces the problem, or the console fix is drift.
5. **Exceptions** are decisions, not silence: documented, approved by a risk owner, with an expiry (in federal terms, a **POA&M** entry or an accepted risk — module 26).
6. **Prevent recurrence:** add a guardrail (module 20) so the finding can't come back.

**Plumbing per cloud:** SCC notification → **Pub/Sub** → a Cloud Run function → Jira/ServiceNow (or the SIEM, module 22); Security Hub → native **Jira Cloud / ServiceNow** integrations or **EventBridge**; Defender for Cloud → **workflow automation** (Logic Apps), **governance rules**, and a **ServiceNow** integration.

**Bridge to intel:** this is the collection → analysis → dissemination → feedback cycle. A finding is raw reporting; triage is analysis; the ticket is the finished product with a consumer and a deadline; verification is the feedback loop.

---

## Text diagram — posture management in a multi-cloud agency

```
   Google Cloud org ──► SCC (Standard/Premium) ─┐  findings ──► Pub/Sub ──► function ──► ServiceNow / Jira
   AWS org ──► Security Hub CSPM (+ Config) ────┤                                         │
             GuardDuty (threats) ───────────────┼──► AWS Security Hub ──► Jira / ServiceNow│
   Azure tenant ──► Defender for Cloud ─────────┤                                         ▼
     (Foundational CSPM free; connectors can ───┘      Owner fixes in Terraform (module 20) ──► rescan PASS
      also pull AWS and GCP posture)                   Exception ──► risk owner + expiry (POA&M)
   Open source (Prowler) ─► CSV/OCSF ─► same ticket queue        Repeat offenders ──► new guardrail
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Native posture (CSPM) | **SCC** Standard (free) / Premium | **Security Hub CSPM** (needs AWS Config) | **Defender for Cloud** Foundational CSPM (free) / Defender CSPM | SCC needs an organization |
| Threat detection | SCC Premium: Event / Container / VM Threat Detection | **GuardDuty** (+ protection plans, Extended Threat Detection) | Defender workload plans (Servers, Storage, Containers…) | AWS sells it as a separate service |
| Unified risk view / attack paths | SCC Premium (org level): attack path simulations | **AWS Security Hub** (new, Dec 2025) | Defender CSPM attack path analysis; Exposure Management | |
| Default benchmark | Google security baseline; Compliance Manager frameworks | AWS FSBP | Microsoft cloud security benchmark (MCSB) | |
| CIS support | CIS GCP posture template (v2.0.0) | CIS AWS v1.2–v5.0.0 | CIS Azure via regulatory compliance ⚠️ (version not verified) | All lag current CIS releases |
| Multicloud | (Enterprise tier deprecated); Wiz acquired Mar 2026 | — | AWS and GCP connectors in Foundational CSPM | Azure's free tier is the only native multicloud posture view |
| Finding format | SCC finding | OCSF (new Hub) / ASFF (CSPM) | Defender recommendations/alerts | OCSF is becoming the common schema |
| Free / trial | Standard free; Premium 30-day project trial → auto pay-as-you-go | 30-day trials; **not on the Free plan** | Foundational free; plans 30-day trial | |
| Ticketing | Pub/Sub → your integration | Native Jira Cloud / ServiceNow | Logic Apps; ServiceNow; governance rules | |

## Administer and monitor it

- **Coverage first:** every project/account/subscription onboarded, including new ones (org-level activation; delegated admin for Security Hub/GuardDuty; Defender enabled by Azure Policy at the management group).
- **Tune, don't mute:** suppress with documented rules and expiry; muted findings are an attacker's best friend.
- **Track the numbers that matter:** open criticals by age, mean time to remediate, exception count and expiry, coverage gaps.
- **Watch the watchers:** alert when someone disables SCC services, GuardDuty detectors (`DeleteDetector`), or Defender plans — another T1685 pattern (module 18).
- **Cost:** trials auto-convert (SCC Premium project trial, Defender plans); per-check (Security Hub CSPM) and per-resource (Defender CSPM) billing scales with estate size.

## Security angle

1. **Partial coverage** — the unmonitored account is where the intrusion starts.
2. **Severity-only triage** — misses toxic combinations; overwhelms teams with lows.
3. **Fixing in the console** a resource that Terraform manages — the fix gets reverted.
4. **Permanent suppressions** — no owner, no expiry.
5. **Read-only scanner identity with too much access** — a CSPM role often can read every configuration in the org; it's a high-value credential (CIEM applies to your tools too).
6. **Assuming CSPM = secure** — it sees configuration, not intent; it won't tell you a correctly configured admin account was phished.

> **Shared responsibility — say it plainly:** providers supply the scanners and the findings. **Turning them on everywhere, triaging, fixing, and the identity, firewall, and access settings the findings point to are always the customer's.** SCC reporting `OPEN_SSH_PORT` doesn't close the port.

## Threat intel angle

**What the reporting says:** Google's *Cloud Threat Horizons Report* (H1 2026, covering the second half of 2025) found **software and third-party exploitation (44.5%)** overtook **weak or missing credentials (27.2%)** as the top initial-access vector in Google Cloud incidents for the first time, with **misconfiguration at 21%** — down from earlier reports, but still roughly one in five. Mandiant's separate incident-response data in the same report found identity issues in a large majority of cases. Posture management addresses the misconfiguration and part of the credential problem; patching (CWPP, vulnerability scanning) addresses the first.

| Adversary activity | ATT&CK | Posture/threat signal |
|---|---|---|
| Enumerate cloud resources after access | **T1580** Cloud Infrastructure Discovery | Burst of `List*`/`Describe*` calls; GuardDuty/ETD discovery findings |
| Discover enabled services | **T1526** Cloud Service Discovery | Same; also attackers checking whether GuardDuty or SCC is on |
| Use the console to browse | **T1538** Cloud Service Dashboard | Console sign-ins from unusual locations |
| Enumerate storage objects | **T1619** Cloud Storage Object Discovery | Data Access / data events (module 18) |
| Use valid cloud credentials | **T1078.004** | SA keys flagged by `USER_MANAGED_SERVICE_ACCOUNT_KEY`; GuardDuty credential findings |

**Attackers use your tools:** open-source posture scanners (Prowler and others) are as useful for an intruder's reconnaissance as for your audit. A burst of read-only API calls across every service from one identity looks exactly like a CSPM scan — which is why you should know your scanner's identity and alert on anyone else doing the same thing.

**Bridge to your CTI work:** posture data is your own-force readiness picture. Pair it with adversary reporting — "this actor uses exposed SA keys" — and you can prioritize the findings that match current TTPs instead of working the list top-down.

## Public sector notes

- **Continuous monitoring (ConMon):** FedRAMP and agency ATOs require ongoing scanning and monthly reporting; posture findings feed the **POA&M** (module 26).
- **CISA BOD 25-01** (issued December 2024 ⚠️ date from news coverage; CISA's page lists the deadlines) requires federal agencies to run CISA's **SCuBA** assessment tools against in-scope SaaS tenants — Microsoft 365 at issuance — and implement the mandatory secure configuration baselines (deadline June 20, 2025). It's posture management mandated by directive, for SaaS rather than IaaS.
- Check that the posture service and its data stay inside the authorization boundary — e.g., which SCC features are available under Assured Workloads, or Defender in Azure Government (module 27).

## Key takeaways

- **CSPM** finds misconfigurations; **CWPP** protects workloads; **CIEM** finds excess permissions; **CNAPP** bundles them.
- **SCC:** Standard (free) and Premium; **Enterprise deprecated May 2026**; needs an organization; Premium project trial auto-converts after 30 days.
- **AWS:** new **Security Hub** (Dec 2025, OCSF, attack paths) + **Security Hub CSPM** (standards, Config) + **GuardDuty** (threats) — none on the Free plan.
- **Azure:** **Foundational CSPM is free** (secure score, MCSB, AWS/GCP connectors); Defender CSPM and workload plans are paid.
- **CIS Benchmarks** are the shared checklist (L1/L2); tools lag the latest versions.
- A finding becomes useful only when it's triaged, owned, fixed in code, verified, and prevented by a guardrail.
- Acting on findings is **always the customer's** job.

## Sources

- [Google Cloud — SCC service tiers](https://docs.cloud.google.com/security-command-center/docs/service-tiers), [SCC deprecations](https://docs.cloud.google.com/security-command-center/docs/deprecations), [SCC release notes](https://docs.cloud.google.com/security-command-center/docs/release-notes), [Activation overview](https://docs.cloud.google.com/security-command-center/docs/activate-scc-overview), [Activate for a project](https://docs.cloud.google.com/security-command-center/docs/activate-scc-for-a-project), [Security Health Analytics](https://docs.cloud.google.com/security-command-center/docs/concepts-security-health-analytics), [CIS 2.0 posture template](https://docs.cloud.google.com/security-command-center/docs/security-posture-cis-20-template), [Security posture overview](https://docs.cloud.google.com/security-command-center/docs/security-posture-overview), [gcloud scc findings list](https://docs.cloud.google.com/sdk/gcloud/reference/scc/findings/list), [gcloud scc notifications create](https://docs.cloud.google.com/sdk/gcloud/reference/scc/notifications/create), [Role recommendations](https://docs.cloud.google.com/policy-intelligence/docs/role-recommendations-overview), [Google completes acquisition of Wiz](https://cloud.google.com/blog/products/identity-security/google-completes-acquisition-of-wiz), [Cloud Threat Horizons H1 2026](https://cloud.google.com/security/report/resources/cloud-threat-horizons-report-h1-2026)
- [AWS — What is the new Security Hub](https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub-v2.html), [Security Hub GA announcement (Dec 2025)](https://aws.amazon.com/about-aws/whats-new/2025/12/security-hub-near-real-time-risk-analytics/), [Security Hub CSPM](https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html), [Security Hub pricing](https://aws.amazon.com/security-hub/pricing/), [Security Hub CSPM pricing](https://aws.amazon.com/security-hub/cspm/pricing/), [CIS AWS Foundations in CSPM](https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html), [Jira Cloud integration](https://docs.aws.amazon.com/securityhub/latest/userguide/jiracloud.html), [ServiceNow integration](https://docs.aws.amazon.com/securityhub/latest/userguide/servicenow-create-ticket.html), [What is GuardDuty](https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html), [Extended Threat Detection](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty-extended-threat-detection.html), [GuardDuty IAM finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-iam.html), [EC2 finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-ec2.html), [Sample findings](https://docs.aws.amazon.com/guardduty/latest/ug/sample_findings.html), [Services on the Free plan](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html)
- [Microsoft — Defender for Cloud introduction](https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-for-cloud-introduction), [Defender for Cloud pricing](https://azure.microsoft.com/pricing/details/defender-for-cloud), [Defender for Servers](https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-for-servers-overview), [Regulatory compliance / MCSB](https://learn.microsoft.com/en-us/azure/defender-for-cloud/concept-regulatory-compliance), [Workflow automation](https://learn.microsoft.com/en-us/azure/defender-for-cloud/workflow-automations), [ServiceNow integration](https://learn.microsoft.com/en-us/azure/defender-for-cloud/integration-servicenow), [Defender for Cloud in the Defender portal](https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-portal/defender-for-cloud-defender-portal), [CIEM](https://learn.microsoft.com/en-us/azure/defender-for-cloud/permissions-management), [DSPM](https://learn.microsoft.com/en-us/azure/defender-for-cloud/concept-data-security-posture), [az security secure-scores](https://learn.microsoft.com/cli/azure/security/secure-scores)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks), [CIS GCP](https://www.cisecurity.org/benchmark/google_cloud_computing_platform), [CIS AWS](https://www.cisecurity.org/benchmark/amazon_web_services), [CIS Azure](https://www.cisecurity.org/benchmark/azure), [CIS Benchmarks FAQ](https://www.cisecurity.org/cis-benchmarks/cis-benchmarks-faq)
- [Prowler CLI docs](https://docs.prowler.com/getting-started/basic-usage/prowler-cli), [Prowler GCP authentication](https://docs.prowler.com/user-guide/providers/gcp/authentication)
- [CISA — BOD 25-01](https://www.cisa.gov/news-events/directives/bod-25-01-implementing-secure-practices-cloud-services)
- [MITRE ATT&CK — T1580](https://attack.mitre.org/techniques/T1580/), [T1526](https://attack.mitre.org/techniques/T1526/), [T1538](https://attack.mitre.org/techniques/T1538/), [T1619](https://attack.mitre.org/techniques/T1619/), [T1078.004](https://attack.mitre.org/techniques/T1078/004/)

Verified: 2026-10-28
