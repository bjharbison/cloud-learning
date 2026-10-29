# 26 — Compliance: FedRAMP, DoD Impact Levels (IL2–IL6), CMMC, NIST 800-53, ATO

> **In one sentence:** you'll be able to explain how U.S. government cloud authorizations work today — FedRAMP's new classes and 20x process, DoD Impact Levels, CMMC, the NIST control catalogs, and the ATO process — and how each one changes the architecture you'd propose to a federal customer.

**Prereqs:** modules 00–25 (module 03 for hierarchy as boundary; 16 for keys; 18 for logging; 20 for policy as code; 21 for posture) · **Time:** ~3.5 hours incl. lab · **Phase:** 7

> **This area is changing fast.** FedRAMP renamed its levels and replaced its process in 2025–2026, and CMMC's rollout was paused in July 2026. Every date below is as verified on 2026-10-29. Check the official pages before quoting any of it to a customer.

## Learning objectives

- Explain **FIPS 199** categorization, the **NIST SP 800-53** catalog and baselines, and the **Risk Management Framework (RMF)**.
- Describe **FedRAMP** today: the 2022 law, OMB M-24-15, the end of the JAB, **FedRAMP 20x**, **Key Security Indicators**, and **Classes A–D**.
- Map **DoD Impact Levels** IL2, IL4, IL5, and IL6 to data types and cloud requirements.
- Summarize **CMMC** levels, assessment types, rule dates, and the 2026 suspension of Phase 2.
- Describe an **ATO**, its package, and **continuous ATO**.
- Translate each framework into concrete architecture decisions.

## Why this matters for the target roles

- **Customer engineer (public sector):** almost every federal conversation starts with "Is it FedRAMP authorized, at what level, and is it IL5?" Getting the vocabulary and current state right is table stakes.
- **Cloud security:** controls like AU-2 (logging) and SC-28 (encryption at rest) are where modules 16–23 turn into evidence.
- **Your background:** you've lived inside accredited systems. Now you see how the provider side of that accreditation is built.

---

## Concepts

### The building blocks

| Term | Plain meaning | Source |
|---|---|---|
| **FIPS 199** | Rate a system Low, Moderate, or High for confidentiality, integrity, and availability, based on the harm if it's compromised | NIST |
| **NIST SP 800-53 Rev. 5** | The catalog of security and privacy controls — **20 families** (AC access control, AU audit, SC system and communications protection, …). Current release **5.2.0** (August 2025) | NIST |
| **NIST SP 800-53B** | Which controls apply at Low, Moderate, and High (the **baselines**) | NIST |
| **RMF (SP 800-37 Rev. 2)** | Seven steps: **Prepare → Categorize → Select → Implement → Assess → Authorize → Monitor** | NIST |
| **ATO** | Authorization to Operate — an **Authorizing Official (AO)** formally accepts the remaining risk of running a system | Agency |

**Bridge from intel:** an ATO is the civilian cousin of accrediting a classified system. The AO plays the role a DAA or ISSM chain does on the high side: a named official signs for the residual risk. ICD 503 is the IC's version of the same idea.

### The ATO package

An AO decides based on a **package**:

- **System Security Plan (SSP):** what the system is, its **authorization boundary**, and how each control is implemented.
- **Security Assessment Plan / Report (SAP/SAR):** how an independent assessor tested it, and what they found.
- **Plan of Action and Milestones (POA&M):** open weaknesses and fix dates.

DoD's version (DoDI 8510.01, 2022) adds that the AO must be a government official and can't delegate the decision. An **IATT** (interim authorization to test) lets a system run for testing before the full ATO.

### Inheritance: why the cloud makes ATOs easier

A cloud provider's authorization covers the controls **it** implements — physical security, hypervisor patching, data-center staff screening. The agency **inherits** those and documents only the rest. This is shared responsibility written in control language:

```
        Agency system ATO (agency AO signs)
        ├── Customer-implemented controls: IAM (AC-2, AC-6), logging config (AU-2, AU-11),
        │   firewall rules (SC-7), key choices (SC-12/13), backups, app security
        ├── Shared controls: encryption at rest (provider default + customer CMEK), incident response
        └── Inherited from the provider's FedRAMP authorization: PE (physical), MA, parts of SC, CP …
```

> **Shared responsibility — say it plainly:** a FedRAMP-authorized cloud **does not** make your system compliant. **Identity, access control, firewall rules, VPN configuration, SSH/RDP exposure, logging settings, and key choices are always the customer's controls**, assessed in the customer's ATO.

### FedRAMP: what changed

**FedRAMP** is the government-wide program, run by GSA, for authorizing cloud services used by federal agencies for unclassified, non-national-security systems.

| Date | Change |
|---|---|
| Dec 2022 | **FedRAMP Authorization Act** (in the FY23 NDAA) puts FedRAMP into law, under GSA, with a FedRAMP Board |
| July 2024 | **OMB M-24-15** rewrites FedRAMP policy: a **presumption of adequacy** (agencies should accept existing authorizations unless there's a documented need), push toward **machine-readable** packages (naming NIST **OSCAL**), and more reliance on provider change processes |
| Aug 2024 | The **Joint Authorization Board (JAB)** "P-ATO" path ends; one "FedRAMP Authorized" designation |
| Mar 2025 | **FedRAMP 20x** announced: a cloud-native, automation-first process |
| 2025–2026 | 20x pilots: Phase 1 (Low) and Phase 2 (Moderate) complete; first Moderate pilot authorizations March 2026 |
| Feb 2026 | New labels: **"FedRAMP Certified"** and **Classes A–D** |
| June 2026 | **Consolidated Rules for 2026 (CR26)**: one rulebook for 20x and the older Rev5 path, mandatory Jan 1, 2027 |
| June 11, 2027 | No new applications on the **Rev5** path after this date |

**The new classes** (chosen partly to avoid confusion with DoD Impact Levels):

| Class | Equivalent to | Rough Rev5 control count |
|---|---|---|
| **A** | New pilot baseline, no prior equivalent | — |
| **B** | LI-SaaS + Low | Low ≈ 156 |
| **C** | Moderate | ≈ 323 |
| **D** | High | ≈ 410 |

Counts are FedRAMP's Rev5 baseline figures (2023 presentation) — FedRAMP adds controls on top of NIST's own baselines. The 20x path for Class D was still a future pilot as of October 2026, so High-level offerings, including the big IaaS providers, remain on Rev5 for now. Expect to hear both vocabularies: "FedRAMP High" in contracts and older docs, "Class D" in new ones. AWS's services-in-scope page reportedly already writes "Class D (formerly High)" ⚠️ (noted in module 16; not re-checked this run).

**Key Security Indicators (KSIs)** are 20x's core idea: instead of narrative answers to hundreds of controls, the provider proves a smaller set of **capabilities** (identity, logging, change management, inventory, and so on) — ideally with **automated, machine-checkable evidence**. Think "continuous telemetry" rather than "a binder."

**Continuous monitoring (ConMon)** still applies: monthly vulnerability scans, an updated POA&M and inventory, and an annual independent assessment by a **third-party assessment organization (3PAO)**.

**Where to look:** the **FedRAMP Marketplace** now lives at **fedramp.gov/marketplace** (the old marketplace.fedramp.gov is deprecated).

### DoD Impact Levels

DoD uses its own layer on top of FedRAMP, defined by DISA's **Cloud Service Provider Security Requirements Guide (CSP SRG)** — v1r1, June 2024, the successor to the older Cloud Computing SRG. DISA grants a **Provisional Authorization (PA)** per cloud offering; the mission owner still issues the ATO.

| Level | Data | Baseline | Key requirements |
|---|---|---|---|
| **IL2** | Public or non-CUI | FedRAMP Moderate | Commercial cloud is fine |
| **IL4** | **CUI** (Controlled Unclassified Information) | FedRAMP Moderate + DoD **FedRAMP+** controls | Traffic through a DoD **Cloud Access Point (CAP)** |
| **IL5** | Higher-sensitivity CUI and unclassified **National Security Systems** | FedRAMP High + FedRAMP+ | Separation from non-federal tenants; CAP; U.S. citizens/nationals/persons screening |
| **IL6** | Classified up to **SECRET** | Classified overlays | Cleared personnel and facilities; classified network connectivity such as SIPRNet ⚠️ (general SRG wording not verified) |

- IL1 and IL3 no longer exist (merged into IL2 and IL4).
- **Above SECRET** is outside the SRG — Top Secret clouds are accredited under IC policy (**ICD 503**). Module 27 covers which providers hold what.
- **IL5 separation** doesn't always mean separate buildings. Microsoft describes logical separation from other federal tenants but physical separation from non-federal ones; Google meets IL5 on commercial regions with Assured Workloads controls (module 27).

### CMMC: the defense contractor side

**CMMC (Cybersecurity Maturity Model Certification)** checks that **defense contractors** protect contract information on their own systems — including the cloud services they use.

| Level | Protects | Requirements | Assessment |
|---|---|---|---|
| **1** | Federal Contract Information (FCI) | **15** requirements from FAR 52.204-21 | Annual self-assessment |
| **2** | **CUI** | **110** requirements of **NIST SP 800-171 Rev. 2** | Self-assessment or **C3PAO** (certified third-party assessor) every 3 years, per contract |
| **3** | CUI facing advanced threats | Level 2 + **24** from **NIST SP 800-172** | Government assessment (DCMA DIBCAC) |

- **Rules:** the program rule (**32 CFR Part 170**) took effect **Dec 16, 2024**; the contracting rule (**DFARS**, 48 CFR) took effect **Nov 10, 2025**, starting **Phase 1** (self-assessments in solicitations).
- **Suspension:** on **July 13, 2026** the department suspended **Phase 2** (third-party Level 2 assessments, due Nov 10, 2026) and pending CMMC milestones, pending a reform task force. Phase 1 self-assessments and the underlying obligations stay in effect. As of late October 2026 no public outcome was found ⚠️.
- **POA&Ms** are limited: Level 2 needs a minimum score of 88 of 110, with open items closed within 180 days.
- **800-171 revision:** NIST published **Rev. 3** in May 2024, but CMMC still assesses against **Rev. 2** until future rulemaking.

**The cloud angle:** under **DFARS 252.204-7012**, a cloud service that stores, processes, or transmits a contractor's CUI must be **FedRAMP Moderate or equivalent** (a December 2023 DoD memo defines "equivalent"). Encrypting CUI doesn't get around that. This is why so many contractors use Microsoft 365 **GCC High** and AWS **GovCloud** (module 27).

### Continuous ATO and where DoD is heading

- **cATO** (DoD memo, Feb 2022): instead of reauthorizing every few years, a system keeps its ATO by showing **continuous monitoring**, **active cyber defense**, and an approved **DevSecOps** pipeline.
- **Software Fast Track (SWFT)** (April 2025) aims to speed up software authorizations.
- **Cybersecurity Risk Management Construct (CSRMC)** (Sept 2025): DoD's framework to move from point-in-time assessments to continuous, automated monitoring. Whether it formally replaces DoDI 8510.01 isn't settled in public documents ⚠️.

**Bridge to earlier modules:** cATO and FedRAMP 20x both reward what you built in modules 18–22 — centralized logs, policy as code, posture scanning, and tested detections are the evidence.

### Other frameworks you'll hear

| Framework | One line |
|---|---|
| **GovRAMP** | StateRAMP's new name (Feb 2025): a FedRAMP-like program for state and local government |
| **CJIS Security Policy** | FBI requirements for criminal justice data; v6.0 Dec 2024, with a v6.1 file dated June 2026 on the FBI site ⚠️ (contents not reviewed) |
| **IRS Publication 1075** | Federal tax information in the cloud: FedRAMP Moderate or higher, U.S.-only, FIPS-validated encryption, 45 days' notice to the IRS |
| **ITAR** | Export-controlled technical data; storing it encrypted end to end (FIPS 140 validated) outside proscribed countries isn't an export — but providers still sell ITAR-oriented environments for U.S.-persons support |

---

## How compliance shapes architecture

| Requirement | Architecture consequence |
|---|---|
| FedRAMP class / IL of each **service** | Use only in-scope services at the needed level; the service list is a design constraint (check each provider's scope page) |
| Data residency (FedRAMP High, IL4/5, ITAR, CJIS) | U.S. regions only; enforce with org policy / SCP / Azure Policy (module 20) |
| Personnel screening | Government environments or support packages (Assured Workloads, GovCloud, Azure Government) — module 27 |
| IL4/5 network path | Route through a DoD **Cloud Access Point**; no direct internet paths |
| Key management (SC-12/13/28) | FIPS-validated modules; customer-managed keys often expected (module 16) |
| Logging (AU family; OMB M-21-31) | Centralized, retained audit logs; Data Access where it matters (module 18) |
| Authorization boundary | Map folders/accounts/subscriptions to ATO boundaries (module 03) |
| Continuous monitoring / cATO | Policy as code, posture scanning, tested detections, IaC change records (modules 20–22, 25) |

## Text diagram — who authorizes what

```
                         ┌───────────────────── Provider side ─────────────────────┐
  NIST 800-53 Rev5 ──►   FedRAMP (GSA): Class B / C / D  ──►  DISA PA: IL2 / IL4 / IL5 / IL6
  (+ FedRAMP 20x KSIs)   3PAO assessment, ConMon            FedRAMP+ controls, CAP
                         └──────────────────────────┬──────────────────────────────┘
                                                    │ inherit
                         ┌─────────────────── Customer side ──────────────────────┐
  Agency / mission ──►    RMF: categorize → select → implement → assess → AUTHORIZE (AO signs ATO)
                          → monitor (ConMon / cATO)
  Defense contractor ──►  CMMC L1/L2/L3 on contractor systems; cloud must be FedRAMP Moderate or equivalent
                         └─────────────────────────────────────────────────────────┘
  Above SECRET: IC accreditation (ICD 503) — outside FedRAMP and the SRG
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Get the provider's compliance docs | Compliance documents download (Audit Manager docs; Compliance Reports Manager) | **AWS Artifact** (incl. FedRAMP customer package) | **Service Trust Portal** | All free with an account |
| Check your config against 800-53 / FedRAMP | **Compliance Manager** frameworks (SCC); Assured Workloads violation monitoring | **Security Hub CSPM** NIST SP 800-53 Rev. 5 standard; Config conformance packs | **Azure Policy** regulatory compliance initiatives (FedRAMP High, NIST SP 800-53 Rev. 5, NIST SP 800-171 Rev. 2); Defender for Cloud dashboard | Azure's initiatives are free to assign for Azure resources |
| Enforce a compliance boundary | **Assured Workloads** folder with a control package | Separate **GovCloud** partition (plus SCPs) | Separate **Azure Government** cloud (plus Policy) | Policy boundary vs separate environment (module 27) |
| FedRAMP High / IL5 in commercial regions | Yes, with Assured Workloads (U.S. regions) | No — GovCloud for High/IL4/IL5 | Commercial Azure holds FedRAMP High; IL5 is in Azure Government | Google's biggest architectural difference |
| Machine-readable evidence (20x direction) | Compliance Manager automation (Google blog, 2026) | Published guidance on 20x evidence on AWS | Policy compliance data via APIs ⚠️ (20x-specific tooling not verified) | All moving toward automated evidence |

## Administer and monitor it

- **Know your boundary:** keep a diagram and an inventory of every service in the ATO boundary; check each against the provider's current scope page.
- **ConMon rhythm:** monthly scans, POA&M updates, inventory; annual assessment. Automate the evidence: posture findings (module 21), log retention reports (module 18), IaC diffs (module 20).
- **Watch for scope changes:** a new provider service isn't automatically in scope; a new feature in an in-scope service may not be either.

## Security angle

- **Compliance ≠ security.** Storm-0558 hit a FedRAMP-authorized service (module 24). Authorizations reduce risk; they don't eliminate it.
- **Common failures:** using an out-of-scope service inside the boundary; data drifting to a non-U.S. region; logs not retained to policy; POA&M items aging out; personal accounts with admin rights outside the identity provider.
- **Evidence integrity:** treat compliance evidence like forensic evidence (module 23) — tamper-resistant, timestamped, traceable.

## Threat intel angle

- Adversaries target the **compliance supply chain** too: contractors handling CUI are a long-standing espionage target, which is the reason CMMC exists.
- The **CSRB's Storm-0558 report** recommended FedRAMP changes and default logging — CTI findings feeding compliance policy.
- **Data-type labels guide targeting:** IL5 and CUI markers tell an adversary where the valuable data is. Boundary design and least privilege matter more there, not less.

## Public sector notes

- **The CE's job here:** know where each service sits (class, IL, region), point customers to official scope pages and the FedRAMP Marketplace, and never promise an ATO — only the customer's AO can grant one.
- **Reciprocity:** M-24-15's presumption of adequacy and DoD's reciprocity language mean an existing authorization should usually be reused, not re-done. That's a strong sales and delivery argument.
- **Timing:** FedRAMP's Rev5-to-20x transition runs through 2027. Expect customers to ask "which path are you on?"

## Key takeaways

- **NIST 800-53 Rev5** (20 families, release 5.2.0) is the control catalog; **FIPS 199** sets Low/Moderate/High; **RMF** has 7 steps ending in an AO-signed **ATO**.
- **FedRAMP** is now law (2022), shaped by **M-24-15** (2024), has no JAB, uses **"Certified" + Classes A–D** (2026), and is moving to **20x** with KSIs. No new Rev5 applications after **June 11, 2027**.
- **DoD IL2/4/5/6** = public / CUI / sensitive CUI and NSS / SECRET; defined in DISA's **CSP SRG** (v1r1, 2024); TS is outside it.
- **CMMC**: L1 = 15, L2 = 110 (800-171 Rev 2), L3 = +24 (800-172); **Phase 2 suspended July 2026**; contractors' clouds must be **FedRAMP Moderate or equivalent**.
- **cATO** and **20x** both reward automation — logs, policy as code, posture, tested detections.
- A provider's authorization covers its controls; **identity, access, firewalls, VPNs, logging, and keys stay yours**.

## Sources

- FedRAMP / GSA / OMB / Congress: [FedRAMP Authorization Act](https://www.fedramp.gov/2026/authority/law/), [OMB M-24-15 (PDF)](https://www.whitehouse.gov/wp-content/uploads/2024/07/M-24-15-Modernizing-the-Federal-Risk-and-Authorization-Management-Program.pdf), [JAB transition (Aug 2024)](https://www.fedramp.gov/archive/2024-08-12-moving-to-one-fedramp-authorization-an-update-on-the-jab-transition/), [GSA — FedRAMP 20x announcement (Mar 2025)](https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-announces-fedramp-20x-03242025), [FedRAMP 20x phases](https://www.fedramp.gov/20x/), [RFC-0006 Key Security Indicators](https://www.fedramp.gov/rfcs/0006/), [NTC-0004 designations and classes](https://www.fedramp.gov/notices/0004/), [Certification classes](https://www.fedramp.gov/2026/agencies/use/classes/), [Consolidated Rules for 2026](https://www.fedramp.gov/2026-06-25-propelling-change-fedramp-launches-consolidated-rules-for-2026/), [Status update (Oct 2026)](https://www.fedramp.gov/2026-10-08-from-foundation-to-implementation/), [Rev5 baselines presentation (PDF)](https://www.fedramp.gov/resources/documents/Rev-5-Transition-Overview-Presentation.pdf), [ConMon Playbook (PDF)](https://www.fedramp.gov/resources/documents/Continuous_Monitoring_Playbook.pdf), [NTC-0009 machine-readable packages](https://www.fedramp.gov/notices/0009/)
- DoD: [Cloud Security Playbook Vol. 1 (PDF)](https://dodcio.defense.gov/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf), [CC SRG Impact Level definitions (archive)](https://dl.dod.cyber.mil/wp-content/uploads/cloud/SRG/index-old.html), [DoDI 8510.01 (PDF)](https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/851001p.pdf), [cATO memo (PDF)](https://dodcio.defense.gov/Portals/0/Documents/Library/20220204-cATO-memo-Signed-Cleared.pdf), [Software Fast Track](https://dowcio.war.gov/In-the-News/Article/4367436/software-fast-track-initiative/), [CSRMC announcement](https://dodcio.defense.gov/In-the-News/Article/4367432/department-of-war-announces-new-cybersecurity-risk-management-construct/)
- CMMC: [32 CFR Part 170 (Federal Register)](https://www.federalregister.gov/documents/2024/10/15/2024-22905/cybersecurity-maturity-model-certification-cmmc-program), [DFARS rule (Federal Register)](https://www.federalregister.gov/documents/2025/09/10/2025-17359/defense-federal-acquisition-regulation-supplement-assessing-contractor-implementation-of), [Phase II suspension (Office of Small Business Programs)](https://business.defense.gov/Engage/News/Article/4542563/forging-the-arsenal-of-freedom-department-of-war-suspends-cmmc-phase-ii-require/), [DoD CIO CMMC FAQs](https://dodcio.defense.gov/CMMC/FAQs)
- NIST: [SP 800-53 Release 5.2.0 news](https://csrc.nist.gov/News/2025/nist-releases-revision-to-sp-800-53-controls), [SP 800-37 Rev. 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), [SP 800-171 Rev. 3](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/800-171r3/NIST.SP.800-171r3.html)
- Other: [GovRAMP rebrand](https://govramp.org/news/blog/stateramp-announces-rebrand-to-govramp-reflecting-mission-to-unite-public-and-private-sectors-in-advancing-cybersecurity), [IRS — Cloud computing environment (Pub 1075)](https://www.irs.gov/privacy-disclosure/cloud-computing-environment), [22 CFR 120.54 (eCFR)](https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M/part-120/subpart-C/section-120.54), [Microsoft — DoD IL5 offering](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-dod-il5)
- Provider tooling: [Google — Download compliance documents](https://docs.cloud.google.com/audit-manager/docs/download_compliance_documents), [Google — Accelerating FedRAMP 20x](https://cloud.google.com/blog/topics/public-sector/accelerating-fedramp-20x-how-google-cloud-is-automating-compliance), [AWS — FedRAMP package via Artifact](https://aws.amazon.com/premiumsupport/knowledge-center/artifact-fedramp-security-compliance/), [AWS — FedRAMP services in scope](https://aws.amazon.com/compliance/services-in-scope/FedRAMP/), [AWS — 20x evidence on AWS](https://aws.amazon.com/blogs/publicsector/building-machine-readable-fedramp-20x-evidence-on-aws/), [Azure Policy — FedRAMP High initiative](https://learn.microsoft.com/en-us/azure/governance/policy/samples/fedramp-high), [Azure Policy — NIST SP 800-171 R2](https://learn.microsoft.com/en-us/azure/governance/policy/samples/nist-sp-800-171-r2)

Verified: 2026-10-29
