# 27 — Government clouds: Assured Workloads, AWS GovCloud and classified regions, Azure Government and classified clouds

> **In one sentence:** you'll be able to explain, accurately and with dates, how Google, AWS, and Microsoft each deliver cloud to the U.S. government — from controls on commercial regions to separate government partitions to air-gapped classified regions — and how the JWCC contract ties them to DoD.

**Prereqs:** modules 00–26 (module 02 previewed government regions; 03 for hierarchy; 16 for Key Access Justifications; 26 for FedRAMP classes and Impact Levels) · **Time:** ~3 hours incl. lab · **Phase:** 7

> **Date-stamp everything.** Authorizations, region lists, and contract status change. Every claim here was checked against official provider, DoD, or GSA pages on **2026-10-29**. Anything supported only by press reporting is labeled.

## Learning objectives

- Explain the **three delivery models**: controls on commercial regions, a separate government partition, and isolated classified regions.
- Describe **Google Assured Workloads** (control packages, pricing tiers, how it enforces) and Google's classified offering.
- Describe **AWS GovCloud (US)** and AWS's **Secret** and **Top Secret** regions.
- Describe **Azure Government**, its DoD regions, and **Azure Government Secret** and **Top Secret**.
- Summarize **JWCC** — vendors, ceiling, classification levels, and what's next.
- Compare the architectural consequences of each model for a federal customer.

## Why this matters for the target roles

- **Customer engineer (Google Public Sector):** "Why don't you have a GovCloud?" is a question you'll get. The answer — and its trade-offs — is core pitch material.
- **Solutions architect:** where a workload can live (region, partition, classification) decides the services, identities, and network paths you can design with.
- **Your background:** you've worked on the high side. This module shows how commercial providers built their way there.

---

## Concepts

### Three delivery models

| Model | Plain meaning | Who uses it |
|---|---|---|
| **Controls on commercial regions** | Same data centers and services as everyone else; a policy boundary restricts location, services, and support personnel | Google **Assured Workloads** (FedRAMP Moderate/High, IL2/4/5) |
| **Separate government partition** | Physically separate regions, separate identities and endpoints, U.S.-screened operators | **AWS GovCloud (US)**, **Azure Government** |
| **Isolated classified regions** | Air-gapped regions accredited for SECRET or TOP SECRET, reached only from classified networks | AWS Secret / Top Secret, Azure Government Secret / Top Secret, **Google Distributed Cloud air-gapped**, Oracle national security regions |

**Bridge from intel:** think of it as the difference between **compartments on a shared system** (Assured Workloads), a **separate unclassified-but-controlled network** (GovCloud, Azure Government), and **systems on SIPRNet or JWICS** (classified regions). Each has different cost, speed, and feature trade-offs.

### Google: Assured Workloads on commercial regions

**How it works:** you create an **Assured Workloads folder** under your organization and choose a **control package**. Every project in that folder inherits guardrails:

- **Data residency** — resources can be created only in allowed locations (U.S. regions for U.S. packages), enforced through organization policy constraints.
- **Service restrictions** — only services in scope for that package.
- **Personnel and support controls** — **Assured Support** routes support to screened staff in the U.S. (needs Enhanced or Premium Support).
- **Key controls** — CMEK and Cloud EKM; ITAR requires CMEK in a separate key project.
- **Visibility and veto** — **Access Transparency** logs Google staff actions; **Access Approval** lets you approve them first; **Key Access Justifications** (module 16) let you deny key use by reason, depending on package.
- **Violation monitoring** — alerts when someone changes a constraint or creates a non-compliant resource.

**U.S. control packages and pricing** (pricing as a percentage of spend inside the folder):

| Tier | Packages | Price |
|---|---|---|
| **Free** | US Data Boundary; Data Boundary for FedRAMP Moderate; US Data Boundary for Healthcare and Life Sciences | No charge |
| **Premium** | US Data Boundary and Support; Healthcare and Life Sciences with Support | 5% |
| **Premium** | Data Boundary for **FedRAMP High**, **IL2**, **IL4**, **IL5**, **CJIS**, **ITAR**, **IRS Publication 1075** | **20%** |

Google's own example: $1,500/month of spend in an IL4 folder adds $300. A 60-day Premium trial exists. Package names moved to a "Data Boundary for X" pattern in 2025; the `gcloud` CLI still accepts older values like `il4` and `fedramp-high`.

**Authorizations (Google's FedRAMP/DoD scope page, updated October 2026):**

- Google Cloud and Google Workspace: **FedRAMP High**; DISA **IL2** and **IL4**.
- **IL5:** Google Cloud holds it for in-scope services (first PA December 2022); several Workspace services show IL5 as **in DISA review** — don't claim Workspace IL5 as held.
- Only **U.S. regions** are appropriate for FedRAMP High and IL2/4/5.
- Check every service on the scope page; Google doesn't publish a single count you should quote.

**Google's classified offering:** **Google Distributed Cloud (GDC) air-gapped** — hardware and software Google provides that runs in a customer or partner facility with **no connection to Google Cloud or the internet**. Google reported authorization for U.S. Intelligence Community **Top Secret and Secret** missions and DoD Top Secret missions (April 2024), and **DoD IL6** for GDC and the GDC air-gapped appliance (May 2025). Module 28 covers how it works.

**Google Public Sector** is the Google division (a subsidiary of Google LLC, announced 2022) that sells Google Cloud and Workspace to U.S. government and education.

### AWS: GovCloud (US) and classified regions

**AWS GovCloud (US)** is two isolated regions — **AWS GovCloud (US-West)** (`us-gov-west-1`) and **AWS GovCloud (US-East)** (`us-gov-east-1`).

- **Separate partition:** resource names start with `arn:aws-us-gov:` instead of `arn:aws:`. IAM, endpoints, and console are separate from commercial AWS.
- **Who can use it:** U.S.-incorporated entities, with a U.S. person as account holder; operated by U.S. citizens, with support from U.S.-citizen engineers in the U.S.
- **How you get in:** create a standard AWS account, then request GovCloud access from the root user's account settings and accept the GovCloud terms; AWS Organizations can create linked account pairs. Billing goes through the linked commercial account. A GovCloud account needs **its own AWS Organization** — it can't share one with commercial accounts.
- **Authorizations:** AWS's GovCloud FAQ cites a FedRAMP authorization covering GovCloud and DoD **IL2, IL4, and IL5**. AWS supports ITAR compliance there but notes there's no formal ITAR certification. (Check the services-in-scope page for the High/Class D listing per service.)

**Classified regions:**

| Region | Status (per AWS) |
|---|---|
| **AWS Top Secret-East** | Launched 2014 for the Intelligence Community |
| **AWS Secret Region** | Announced November 2017; accredited under ICD 503 for SECRET workloads |
| **AWS Top Secret-West** | Announced December 2021; accredited for TOP SECRET under ICD 503 |
| **AWS Secret-West** | Available October 2025 — second Secret region; services authorized at ICD 503 and DoD **IL6** |

### Microsoft: Azure Government and classified clouds

**Azure Government** is a physically isolated instance of Azure for U.S. government customers and their partners.

- **Regions:** **US Gov Virginia, US Gov Arizona, US Gov Texas** (federal, state, local, and partners) and **US DoD Central, US DoD East** (exclusively DoD).
- **Authorizations:** FedRAMP High and DISA **IL2/IL4/IL5** in the three US Gov regions (IL5 needs extra isolation configuration there); **IL5** in the DoD regions.
- **Eligibility:** customers are **validated** before getting access; access to systems processing customer data is limited to **screened U.S. persons**.
- **Separate endpoints:** portal **portal.azure.us**, Entra sign-in **login.microsoftonline.us**, Resource Manager **management.usgovcloudapi.net**. In the CLI: `az cloud set --name AzureUSGovernment`.
- **Commercial Azure** also holds **FedRAMP High** for its U.S. regions — but IL5 lives in Azure Government.

**Classified clouds:**

| Cloud | Status (per Microsoft) |
|---|---|
| **Azure Government Secret** | DoD **IL6** PA and ICD 503 accreditation (announced March 2020) |
| **Azure Government Top Secret** | Generally available August 2021; ICD 503 ATO, air-gapped regions |

**Microsoft 365 government environments** (often what agencies mean by "Microsoft cloud"):

| Environment | For | Level |
|---|---|---|
| **GCC** | Federal civilian, state/local, contractors | FedRAMP Moderate-level |
| **GCC High** | Defense agencies and contractors with CUI | FedRAMP High; DFARS; ITAR/EAR support |
| **DoD** | DoD | IL5 |

### Oracle, briefly

Oracle is the fourth JWCC vendor. Oracle says DoD authorized its **Oracle National Security Regions** for Top Secret missions (February 2022) and that its defense cloud offerings cover IL2–IL5 plus IL6 ⚠️ (vendor pages only; not verified on DoD sites).

### JWCC: the DoD contract vehicle

**JWCC (Joint Warfighting Cloud Capability)** is how DoD buys commercial cloud at scale.

- **Awarded December 7, 2022** as four separate IDIQ (indefinite-delivery, indefinite-quantity) contracts — **Google, Oracle, AWS, and Microsoft** — sharing a **$9 billion** ceiling (each award lists the same $9B figure) and an estimated completion of **June 2028** (DoD contract announcement).
- **Scope:** all classification levels — **unclassified, SECRET, and TOP SECRET** — from the continental U.S. to the **tactical edge** (DoD CIO).
- **Who orders:** DoD components place **task orders** against it. Press reports DISA officials saying more than $3 billion in task orders had been awarded by mid-2025 ⚠️ (press only).
- **What's next:** DoD has discussed a follow-on, **"JWCC Next,"** with a broader marketplace and longer term; press reported a solicitation planned for FY2026 and award in 2027 ⚠️ (press only — no official solicitation verified as of this date).

**Bridge from intel:** for IC customers, the equivalent multi-vendor vehicle is the CIA's **C2E** (Commercial Cloud Enterprise) ⚠️ — reported in the press in 2020 as awarded to several providers; no primary source was found, so don't cite details.

### Other buying vehicles worth knowing

GSA's **OneGov** agreements (2025) set government-wide discounts: AWS (up to $1 billion in credits for civilian agencies, through 2028), Google (**Gemini for Government** at $0.47 per agency through 2026), and Microsoft (multi-year discounts including Microsoft 365 Copilot offers). Pricing details belong to the contract, not a CE's memory — point customers to GSA.

---

## Text diagram — where a workload can live

```
 Classification ▲
   TOP SECRET   │  AWS Top Secret-East/West │ Azure Gov Top Secret │ GDC air-gapped │ Oracle NSR*
                │                    (ICD 503 accreditation; JWICS-side; air-gapped)
   SECRET (IL6) │  AWS Secret, Secret-West  │ Azure Gov Secret     │ GDC air-gapped (IL6)
                │                    (SIPRNet-side; cleared operators)
   ─────────────┼──────────────────────────────────────────────────────────────────────────
   IL5          │  GovCloud (US)            │ Azure Gov (US Gov + DoD regions) │ Google Cloud U.S. regions
   IL4 / High   │  GovCloud (US)            │ Azure Gov; commercial (High)     │   + Assured Workloads folder
   Moderate/IL2 │  commercial U.S. regions  │ commercial U.S. regions          │ commercial (free packages)
                └──────────────────────────────────────────────────────────────────────────►
                   separate partition                separate instance               policy boundary
 * vendor-reported
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Unclassified government model | **Assured Workloads** folder on commercial U.S. regions | **GovCloud (US)** partition (2 regions) | **Azure Government** instance (5 regions incl. 2 DoD) | Policy boundary vs separate environment |
| Identity | Same Cloud Identity / org; folder-level controls | Separate GovCloud accounts and IAM; own Organization | Separate Entra tenant on `login.microsoftonline.us` | Google needs no second identity plane |
| Endpoints | Same APIs and console | `*.us-gov-*.amazonaws.com`; `arn:aws-us-gov` | `*.usgovcloudapi.net`; `portal.azure.us` | Code ported to AWS/Azure gov needs endpoint changes |
| FedRAMP High | Yes (U.S. regions, with package) | GovCloud (check per service) | Commercial and Azure Government | |
| IL5 | Yes (in-scope services, U.S. regions) | GovCloud | Azure Government | |
| Eligibility gate | Org + billing; premium packages cost 20% | U.S. entity, U.S.-person account holder | Validated government customers and partners | |
| SECRET / IL6 | GDC air-gapped (IL6, May 2025) | Secret Region; Secret-West (Oct 2025) | Azure Government Secret (2020) | |
| TOP SECRET | GDC air-gapped (Apr 2024) | Top Secret-East (2014), -West (2021) | Azure Government Top Secret (2021) | AWS had the longest IC track record |
| Feature parity | Most features available, minus out-of-scope services | GovCloud gets services later; check availability | Azure Government gets services later; check availability | Google's model avoids most parity lag |
| JWCC | Yes (awardee, Dec 2022) | Yes | Yes | Plus Oracle |

## Administer and monitor it

- **Google:** watch Assured Workloads **violations** (constraint changes, non-compliant resources); keep the folder's org policies under IaC (module 20); review Access Transparency logs (module 18).
- **AWS GovCloud:** a second Organization and partition to administer — separate SSO, SCPs, CloudTrail, and Security Hub; tooling must know the `aws-us-gov` partition.
- **Azure Government:** a separate tenant with its own Entra ID, Sentinel workspace, and Defender plans; check feature availability before designing (Microsoft publishes a comparison page).
- **All:** keep a **service availability matrix** for your boundary — what's authorized, at what level, in which region.

## Security angle

- **A government environment doesn't secure your tenant.** Identity, access control, firewall rules, VPNs, and SSH/RDP exposure are still yours in GovCloud, Azure Government, or an Assured Workloads folder.
- **Boundary leaks:** a project created **outside** the Assured Workloads folder, a GovCloud workload calling a commercial endpoint, or a commercial Entra tenant federated into a government one can move data out of scope.
- **Two control planes = two attack surfaces** (AWS and Azure): duplicated admin roles, logging, and detections. Gaps between them are where mistakes hide.
- **Support channels:** premium support packages exist so that people touching your data are screened. Use them — and log their access (Access Transparency, Customer Lockbox).

> **Shared responsibility — say it plainly:** the provider screens its staff, isolates its regions, and holds the authorizations. **Your identities, access policies, network rules, VPN configuration, and remote-access exposure are always yours** — in every government cloud.

## Threat intel angle

- Government clouds concentrate high-value targets, so **identity tradecraft** from module 24 applies directly: APT29's cloud techniques and Storm-0558's token forgery were aimed at government mail.
- **Storm-0558 crossed the consumer/enterprise boundary** inside one provider. Ask each provider how government token-signing keys and identity systems are separated from commercial ones.
- **Insider and supply-chain risk** drive personnel screening requirements (U.S. persons, cleared staff). CTI on foreign-intelligence targeting of cloud employees is a legitimate customer concern.
- Classified regions are reached only from classified networks; threat models there emphasize insiders and cross-domain transfers more than internet-borne attack (module 28).

## Public sector notes

- **The Google pitch, fairly:** IL5 and FedRAMP High on commercial regions means fewer feature gaps and one identity plane; the trade-off is that some customers prefer — or their policies require — physically separate environments, and premium packages add cost.
- **Don't overclaim.** Quote authorizations from the provider's scope page and the FedRAMP Marketplace with a date. "Generally available" in a blog post isn't the same as "in scope at IL5 for your service."
- **Contract vehicles matter as much as tech:** JWCC for DoD, GSA schedules and OneGov for civilian agencies.

## Key takeaways

- Three models: **policy boundary** (Google Assured Workloads), **separate partition** (AWS GovCloud, Azure Government), **air-gapped classified** (all four JWCC vendors).
- **Assured Workloads:** folder + control package; free tier includes US Data Boundary and FedRAMP Moderate; **FedRAMP High / IL2 / IL4 / IL5 / ITAR / CJIS / IRS 1075 are premium at 20%** of in-folder spend.
- **GovCloud:** `us-gov-west-1`, `us-gov-east-1`, `arn:aws-us-gov`, own Organization, U.S.-person account holder; IL2/4/5.
- **Azure Government:** 3 US Gov + 2 DoD regions, `.us` endpoints, eligibility validation; Secret (IL6, 2020) and Top Secret (2021).
- **Classified:** AWS Secret, Secret-West (2025), Top Secret-East/West; Azure Gov Secret/Top Secret; GDC air-gapped (TS/Secret 2024, IL6 2025).
- **JWCC:** Dec 2022, Google/Oracle/AWS/Microsoft, $9B ceiling, all classification levels, ends ~June 2028; "JWCC Next" is press-reported.

## Sources

- Google: [Assured Workloads overview](https://docs.cloud.google.com/assured-workloads/docs/overview), [Control packages](https://docs.cloud.google.com/assured-workloads/docs/control-packages), [Pricing](https://cloud.google.com/assured-workloads/pricing), [gcloud assured workloads create](https://docs.cloud.google.com/sdk/gcloud/reference/assured/workloads/create), [FedRAMP and DoD compliance scope](https://docs.cloud.google.com/docs/security/compliance/fedramp-dod-compliance-scope), [DISA compliance](https://cloud.google.com/security/compliance/disa), [IL5 support (Dec 2022)](https://cloud.google.com/blog/products/identity-security/introducing-google-cloud-support-for-impact-level-5-workloads), [GDC Top Secret and Secret authorization (Apr 2024)](https://cloud.google.com/blog/topics/public-sector/google-public-sector-achieves-top-secret-and-secret-cloud-authorization), [GDC IL6 (May 2025)](https://cloud.google.com/blog/topics/public-sector/google-distributed-cloud-gdc-gdc-air-gapped-appliance-achieve-dod-impact-level-6-il6-authorization), [GDC air-gapped](https://cloud.google.com/distributed-cloud-air-gapped), [Announcing Google Public Sector (2022)](https://cloud.google.com/blog/topics/public-sector/announcing-google-public-sector)
- AWS: [GovCloud ARNs](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/using-govcloud-arns.html), [GovCloud FAQs](https://aws.amazon.com/govcloud-us/faqs/), [GovCloud sign-up](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/getting-started-sign-up.html), [Secret Region (2017)](https://aws.amazon.com/blogs/publicsector/announcing-the-new-aws-secret-region/), [Secret-West (Oct 2025)](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-secret-west-region-is-now-available/), [Top Secret-West (Dec 2021)](https://aws.amazon.com/blogs/publicsector/announcing-second-aws-top-secret-region-extending-support-us-government-classified-missions/), [FedRAMP services in scope](https://aws.amazon.com/compliance/services-in-scope/FedRAMP/)
- Microsoft: [Azure Government overview](https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-welcome), [Azure Government for DoD](https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-dod), [Compliance planning](https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-plan-compliance), [Compare Azure Government and global Azure](https://learn.microsoft.com/en-us/azure/azure-government/compare-azure-government-global-azure), [FedRAMP offering](https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-fedramp), [Azure Government Secret IL6 (2020)](https://azure.microsoft.com/en-us/blog/azure-government-secret-accredited-at-dod-il6-icd-503-with-iaas-and-paas/), [Azure Government Top Secret GA (2021)](https://azure.microsoft.com/en-us/blog/azure-government-top-secret-now-generally-available-for-us-national-security-missions/), [Microsoft 365 government environments](https://learn.microsoft.com/en-us/microsoft-365/copilot/gov-overview)
- Oracle: [DoD accredits OCI for Top Secret (Feb 2022)](https://www.oracle.com/news/announcement/dod-accredits-oracle-cloud-infrastructure-for-top-secret-missions-2022-02-15/), [Oracle US Defense Cloud](https://www.oracle.com/government/govcloud/defense/)
- DoD / GSA: [JWCC contract announcement (Dec 7, 2022)](https://www.defense.gov/News/Contracts/Contract/Article/3239197/), [DoD CIO — JWCC vendors named](https://dodcio.defense.gov/In-the-News/Article/3267572/department-names-vendors-to-provide-joint-warfighting-cloud-capability/), [GSA OneGov — AWS](https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-announces-onegov-agreement-with-aws-08072025), [GSA OneGov — Google](https://www.gsa.gov/about-gsa/newsroom/news-releases/gsa-google-announce-gemini-onegov-agreement-08212025), [GSA OneGov — Microsoft](https://www.gsa.gov/about-gsa/newsroom/news-releases/multibillion-dollar-gsa-onegov-agreement-with-microsoft-brings-steep-discounts-09022025)
- Press (labeled ⚠️ in text): [DefenseScoop — JWCC Next plans (Aug 2025)](https://defensescoop.com/2025/08/07/jwcc-next-enterprise-cloud-program-dod-solicitation-plans/)

Verified: 2026-10-29
