# 17 — Zero trust: BeyondCorp, identity-aware access, and federal zero-trust strategy

> **In one sentence:** you'll be able to explain zero trust as an architecture model rather than a product, trace it from Google's BeyondCorp to NIST SP 800-207, map each cloud's identity-aware access services onto that model, and speak accurately about OMB M-22-09, the CISA Zero Trust Maturity Model, and the DoD zero-trust strategy.

**Prereqs:** modules 00–16 (especially 05 for IAP TCP forwarding, 11 for VPC Service Controls, 15 for Conditional Access and phishing-resistant MFA) · **Time:** ~3 hours incl. lab · **Phase:** 4

## Learning objectives

- Define **zero trust** in plain language and with **NIST SP 800-207** vocabulary (policy engine, policy administrator, policy enforcement point).
- Tell the **BeyondCorp** story accurately and name Google's current products.
- Compare **identity-aware access** on all three clouds: Google **IAP** + **Context-Aware Access**, **AWS Verified Access**, Microsoft **Conditional Access** + **Entra Private Access**.
- Summarize **OMB M-22-09**, the **CISA Zero Trust Maturity Model 2.0**, and the **DoD Zero Trust Strategy** — and their current status.
- Explain why VPN and edge-appliance exploitation keeps showing up in advisories, and what zero trust changes.

## Why this matters for the target roles

- **Customer engineer:** "zero trust" is in nearly every federal RFP and strategy document. Being the person who can say *which pillar* a product addresses — and which it doesn't — is credibility.
- **Cloud security:** zero trust is how the identity (15), network (11), device, and logging (18) controls fit together into one argument.
- **CTI:** a large share of recent intrusions began at a VPN or edge appliance. Zero trust is partly a response to that reporting.

---

## Concepts

### Zero trust in one paragraph

**Plain version:** don't grant access because of *where* a request comes from (inside the network, on the VPN). Grant it **per request**, based on **who** is asking, **from what device**, **to which resource**, under **what conditions** — and keep checking. Assume the network is already hostile.

**NIST SP 800-207** (August 2020) is the reference definition. Its core parts:

- **Policy Engine (PE)** — decides grant, deny, or revoke, using a trust algorithm and signals.
- **Policy Administrator (PA)** — sets up or tears down the session based on that decision.
- Together they form the **Policy Decision Point (PDP)**.
- **Policy Enforcement Point (PEP)** — the gate in the data path that enforces the decision (a proxy, gateway, or agent).

NIST followed with **SP 1800-35**, *Implementing a Zero Trust Architecture* (final, June 2025): 19 example builds from 24 vendor collaborators. It's the practical companion to 800-207.

**Bridge to your intel background:** zero trust is need-to-know applied to every access, every time. A cleared badge gets you into the building, but not into every compartment — each read-in is checked against role, need, and current status, and access ends when the need does. A flat corporate network behind a VPN is the opposite: one badge, every room.

**What zero trust is not:** a product, a single purchase, or "no VPN." Every vendor sells a slice. The architecture is yours.

### BeyondCorp: where the cloud version started

- Google has said publicly that the **Operation Aurora** intrusion in late 2009 pushed it to redesign its security, and that **BeyondCorp** grew out of that work.
- The first paper, *BeyondCorp: A New Approach to Enterprise Security* (Ward and Beyer, USENIX *;login:*, December 2014), argued that perimeter security fails once breached, so Google would remove the privileged intranet and put internal applications on the internet behind an **access proxy** that checks user and device every time.
- Later papers covered design to deployment, the access proxy, migration, user experience, and fleet health.

**What it became commercially:**

| Era | Name | Notes |
|---|---|---|
| Internal program | BeyondCorp | Employees work from untrusted networks without a VPN |
| Product (2020–2024) | BeyondCorp Enterprise | Google's commercial zero-trust access |
| **Current** (announced April 2024) | **Chrome Enterprise Premium** | Context-aware access, threat and data protection in the Chrome browser (DLP, malware and phishing protection, URL filtering), reporting |

The "BeyondCorp" name survives in some APIs and `gcloud beta beyondcorp` commands. Two components have been retired: the **client connector** (shut down end of 2023) and the **App Connector** (formerly the BeyondCorp app connector; shut down **July 31, 2026**). Don't recommend either.

### Google Cloud's building blocks

| Zero-trust job | Google Cloud service |
|---|---|
| **PEP for web apps** | **Identity-Aware Proxy (IAP)** in front of App Engine, Compute Engine/GKE behind a load balancer, **Cloud Run directly** (GA March 2026), and on-prem apps |
| **PEP for admin protocols** | **IAP TCP forwarding** for SSH/RDP (module 05) — no public IPs |
| **Conditions (context)** | **Access Context Manager** access levels — IP ranges, geography, device attributes (basic or CEL custom levels) — used by IAP and **VPC Service Controls** |
| **Identity** | Cloud Identity / Workforce Identity Federation, phishing-resistant MFA via your IdP (module 15) |
| **Device trust** | **Endpoint Verification** device attributes — a paid **Chrome Enterprise Premium** feature |
| **Data-path boundary** | **VPC Service Controls** perimeters (module 11) |
| **Browser as PEP** | **Chrome Enterprise Premium** threat and data protection |

**How IAP works for a web app:** a request hits IAP; IAP sends unauthenticated users to Google sign-in; it checks the IAM role **IAP-secured Web App User** (`roles/iap.httpsResourceAccessor`) on that resource, plus any access level or IAM Condition; then forwards the request with a signed header, **`x-goog-iap-jwt-assertion`**. Apps should verify that JWT — the plain `x-goog-authenticated-user-email` header is unsigned and could be forged if someone found a way around IAP.

**Costs:** core IAP for Google Cloud resources is **free**. Custom access levels, device attributes, and proxying non-Google-Cloud apps are paid Chrome Enterprise Premium features.

**The bypass caveat (shared responsibility):** for Compute Engine and GKE, IAP protects only the path *through* the load balancer. Anyone who can reach the serving port another way bypasses it. Your **firewall rules** must allow only the load balancer and IAP ranges — that's the customer's job, as always.

**Homelab bridge:** if you've put Authelia, Authentik, or Cloudflare Access in front of Grafana or Proxmox instead of exposing them through a port-forward or VPN, you've built an identity-aware proxy. IAP is that pattern as a managed service, with IAM as the policy.

### AWS and Microsoft

**AWS** frames zero trust as a model and offers building blocks:

- **AWS Verified Access** — VPN-less access to private applications; evaluates every request against identity and device-trust providers using **Cedar** policies; logs every attempt. Non-HTTP(S) (TCP, SSH, RDP) support went GA February 2025. Priced per app-hour (about **$0.27/hour** per HTTP application in US East (Ohio) plus $0.02/GB) — no free tier. Available in GovCloud for HTTP(S) apps.
- **Amazon VPC Lattice** for service-to-service connectivity with auth policies, and **Amazon Verified Permissions** for fine-grained app authorization (both Cedar-based ⚠️ Lattice details not re-verified this run).
- **Systems Manager Session Manager** for no-inbound-port admin access (module 05).

**Microsoft** calls **Conditional Access** its "Zero Trust policy engine" (module 15) — that's the PDP. The PEP options:

- **Global Secure Access**, Microsoft's **Security Service Edge (SSE)**: **Entra Private Access** (per-app VPN replacement for TCP/UDP apps) and **Entra Internet Access** (identity-aware secure web gateway). Licensed in **Entra Suite** or standalone; both require Entra ID P1/P2.
- **Entra application proxy** — publishes on-prem web apps through an **outbound-only** connector, so no inbound firewall holes.
- Microsoft's framing: "verify explicitly, use least privilege, assume breach."

### Where each piece fits — NIST terms mapped

| NIST role | Google Cloud | AWS | Microsoft |
|---|---|---|---|
| Policy engine (decide) | IAM + Access Context Manager evaluated by IAP / VPC-SC | Verified Access Cedar policies + trust providers | Conditional Access |
| Policy enforcement point (gate) | IAP (web, TCP), VPC-SC perimeter, Chrome | Verified Access endpoints, Session Manager | Global Secure Access client/edge, app proxy |
| Identity signal | Cloud Identity / federated IdP | IAM Identity Center or OIDC IdP | Entra ID |
| Device signal | Endpoint Verification (paid) | Device trust providers (CrowdStrike, Jamf, JumpCloud…) | Intune compliance |
| Logging | Cloud Audit Logs (IAP Data Access logs) | Verified Access logs | Entra sign-in logs, GSA traffic logs |

### Federal zero trust: the documents to know

**OMB M-22-09** (*Moving the U.S. Government Toward Zero Trust Cybersecurity Principles*, January 26, 2022) set goals for agencies by the end of FY2024, organized by the CISA pillars:

- **Identity:** centralized enterprise identity; **phishing-resistant MFA**; at least one device-level signal in access decisions.
- **Devices:** complete inventory; EDR.
- **Networks:** encrypt DNS; HTTPS for all web and API traffic, including internal; plan to isolate environments.
- **Applications:** treat every application as internet-connected; make at least one FISMA-Moderate system fully usable over the internet.
- **Data:** categorize sensitive data; audit access to encrypted cloud data; logging per **M-21-31** (module 18).

**Status:** OMB's FY2025 guidance (**M-25-04**, January 2025) cites M-22-09 and tells agencies to keep advancing. Executive Order 14306 (June 2025) amended earlier cyber EOs without addressing zero trust. No rescission of M-22-09 was found on whitehouse.gov as of this module's verification date.

**CISA Zero Trust Maturity Model, version 2.0** (April 2023):

- **Five pillars:** Identity, Devices, Networks, Applications and Workloads, Data.
- **Three cross-cutting capabilities:** Visibility and Analytics, Automation and Orchestration, Governance.
- **Four stages:** Traditional → Initial → Advanced → Optimal.
- CISA has since added "Journey to Zero Trust" companion guides (e.g., microsegmentation, 2025) ⚠️ contents not reviewed this run.

**DoD Zero Trust Strategy** (dated October 2022, released November 2022):

- **Seven pillars:** User; Device; Network & Environment; Application & Workload; Data; Visibility & Analytics; Automation & Orchestration.
- **Target Level** (91 activities of 152) is the required minimum by the **end of FY2027**; **Advanced Level** is the full set.
- 2024 Execution Roadmap v1.1; in January 2026, NSA published Zero Trust Implementation Guidelines that phase the Target-level activities (Discovery, Phase One, Phase Two). Note that some 2026 defense documents use the "Department of War" name.
- **OT:** in April 2026, CISA and partners including the defense department, DOE, and FBI published *Adapting Zero Trust Principles to Operational Technology* — directly relevant to your OT background.

**Where the clouds fit:** each provider publishes mappings of its services to these pillars. Treat them as marketing until you can trace a specific control to a specific activity.

> **Shared responsibility — say it plainly:** providers supply the proxies, policy engines, and signals. **Which apps sit behind identity-aware access, the access policies and conditions, MFA strength, device requirements, firewall rules that prevent bypass, removing VPN and public exposure, and logging the decisions are always the customer's.** Zero trust is an architecture the customer owns.

---

## Text diagram — IAP as the policy enforcement point

```
   User + device ──HTTPS──► Identity-Aware Proxy (PEP)  ◄── no VPN, no public admin ports
                              │ 1. authenticate (Google sign-in / federated IdP + phishing-resistant MFA)
                              │ 2. authorize: IAM roles/iap.httpsResourceAccessor
                              │              + IAM Condition (time) + access level (IP/geo/device)
                              │ 3. log decision (IAP Data Access audit log: granted true/false)
                              ▼
                     signed header x-goog-iap-jwt-assertion
                              ▼
                     Cloud Run service (no allUsers invoker; IAP service agent = run.invoker)
                              │
                     App verifies the JWT; uses its own least-privilege service account
                              ▼
                     Data in a VPC Service Controls perimeter (module 11), CMEK (module 16)

   Policy decision point = IAM + Access Context Manager (Google)  ≈ Conditional Access (Microsoft)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Identity-aware web access | **IAP** (free for Google Cloud resources) | **Verified Access** (per app-hour) | **Entra application proxy** / **Entra Private Access** | Only IAP has no hourly charge |
| Admin access without inbound ports | IAP TCP forwarding (needs firewall rule from IAP range) | Session Manager (no inbound rule) | Azure Bastion; Entra Private Access | Module 05 |
| Policy engine | IAM + Access Context Manager | Cedar policies + trust providers | **Conditional Access** (P1) | Microsoft's is the most featureful sign-in engine |
| Device signal | Endpoint Verification (Chrome Enterprise Premium) | Third-party device trust providers | Intune compliance | |
| Secure web gateway / SSE | Chrome Enterprise Premium (browser-based) | — (partners) | **Entra Internet Access** | Google puts the control in the browser |
| Data perimeter | VPC Service Controls | Data perimeter pattern (SCP/RCP + endpoint policies) | Private Endpoints + network security perimeter | Module 11 |
| GovCloud / sovereign availability | Assured Workloads controls ⚠️ per-service | Verified Access in GovCloud (HTTP(S) only) | ⚠️ Azure Government availability not checked | Check per service in module 27 |

## Administer and monitor it

- **Inventory exposure:** which apps are still reachable by VPN, public IP, or `allUsers`? Use `gcloud run services list`, firewall reviews (module 11), and Security Command Center findings (module 21).
- **Policy review:** IAP IAM bindings (`gcloud iap web get-iam-policy`), access levels, Conditional Access policies (use **report-only** first), Verified Access policies.
- **Logs:** IAP access decisions are **Data Access** audit logs (`authorizationInfo.granted`) — off by default; IAP policy changes are Admin Activity. Entra sign-in logs show which Conditional Access policies applied. Verified Access logs every request.
- **Measure maturity** against the CISA pillars rather than counting products.

## Security angle

1. **IAP bypass** — VMs reachable directly because firewall rules allow `0.0.0.0/0` on the serving port.
2. **App trusts unsigned identity headers** instead of verifying the IAP JWT.
3. **"Zero trust" with phishable MFA** — push or SMS defeats the identity pillar (module 15).
4. **Over-broad access** — `allAuthenticatedUsers` or a whole domain granted IAP access to an admin app.
5. **VPN kept "just in case"** — the old path remains the soft one.
6. **No device signal** — a valid identity on a compromised laptop still gets in.
7. **Decisions not logged** — no IAP Data Access logs, no evidence.

## Threat intel angle

| Technique | ATT&CK | Public reporting |
|---|---|---|
| Exploiting VPN and edge appliances | **T1190 Exploit Public-Facing Application** | CISA **AA24-060B** (Feb 29, 2024): Ivanti Connect Secure / Policy Secure exploitation; Ivanti's integrity checker could be deceived, and CISA advised weighing whether to keep running the devices |
| Using valid credentials on remote access services | **T1133 External Remote Services** | CISA **AA23-325A**: LockBit 3.0 affiliates exploiting Citrix Bleed (CVE-2023-4966) in NetScaler ⚠️ advisory page not re-read this run |
| Session token theft after MFA | T1539 / T1557 | Module 15 |
| Persistence on unmonitored edge devices | — | CISA **BOD 26-02** on end-of-support edge devices ⚠️ requirements not re-read this run |

**Why this matters for zero trust:** a VPN concentrator is a single, internet-facing, high-value box that, once owned, puts the attacker "inside." Identity-aware proxies shift the exposed surface to a provider-run service and make every request carry identity and device context. It doesn't eliminate risk — the proxy and IdP become the crown jewels — but it removes the flat network behind them.

**Note on ATT&CK versions:** ATT&CK v19 (April 2026) split the old Defense Evasion tactic into **Stealth** and **Defense Impairment** and renumbered the old "Impair Defenses" techniques (module 18 has details). Check versions when you read older reports.

**Bridge to your CTI and OT work:** the edge-device campaigns read like the OT pattern you know — long-lived appliances, weak visibility, vendor patch cycles. The April 2026 OT zero-trust guide and its use of zones and conduits will look familiar from IEC 62443 ⚠️ (62443 linkage stated from the guide's description, not re-read).

## Public sector notes

- **TIC 3.0** (module 11) and zero trust converge: CISA published a 2026 guide on SASE and TIC 3.0 ⚠️ not reviewed.
- Expect RFPs to ask for alignment to the **CISA ZTMM** pillars and, in defense, **DoD Target Level** activities — answer with specific capabilities, not slogans.
- Phishing-resistant MFA (PIV/CAC, FIDO2) is the identity-pillar baseline (module 15).

## Key takeaways

- Zero trust = per-request access decisions on identity, device, and context; assume the network is hostile. A model, not a product.
- NIST 800-207: **PE + PA = PDP**; **PEP** enforces. SP 1800-35 shows builds.
- BeyondCorp → BeyondCorp Enterprise → **Chrome Enterprise Premium**; **IAP** is the free core on Google Cloud (Cloud Run directly since March 2026).
- AWS: **Verified Access** (paid per app-hour). Microsoft: **Conditional Access** as PDP, **Global Secure Access** as PEP.
- Federal: **M-22-09** (no rescission found), **CISA ZTMM 2.0** (5 pillars, 3 cross-cutting, 4 stages), **DoD Target Level by end of FY2027**.
- Firewall rules that prevent bypass, policies, MFA strength, and logging are **always the customer's**.

## Sources

- [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final), [NIST SP 1800-35](https://csrc.nist.gov/pubs/sp/1800/35/final)
- [USENIX ;login: — BeyondCorp: A New Approach to Enterprise Security (2014)](https://www.usenix.org/publications/login/dec14/ward), [Google — BeyondCorp](https://cloud.google.com/beyondcorp), [Google blog — Transparency in the shadowy world of cyberattacks (2022)](https://blog.google/company-news/outreach-and-initiatives/public-policy/transparency-in-the-shadowy-world-of-cyberattacks/)
- [Google Cloud blog — Introducing Chrome Enterprise Premium (2024)](https://cloud.google.com/blog/products/identity-security/introducing-chrome-enterprise-premium), [Chrome Enterprise Premium deprecations](https://docs.cloud.google.com/chrome-enterprise-premium/docs/deprecations)
- [Google Cloud — IAP overview](https://docs.cloud.google.com/iap/docs/concepts-overview), [IAP for Cloud Run](https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run), [signed headers](https://docs.cloud.google.com/iap/docs/signed-headers-howto), [TCP forwarding](https://docs.cloud.google.com/iap/docs/using-tcp-forwarding), [IAP audit logging](https://docs.cloud.google.com/iap/docs/audit-log-howto), [IAP pricing](https://cloud.google.com/iap/pricing), [Cloud Run release notes](https://docs.cloud.google.com/run/docs/release-notes), [Access Context Manager](https://docs.cloud.google.com/access-context-manager/docs/overview), [Architecture Framework — Implement zero trust](https://docs.cloud.google.com/architecture/framework/security/implement-zero-trust)
- [AWS — Zero trust on AWS](https://aws.amazon.com/security/zero-trust/), [Verified Access user guide](https://docs.aws.amazon.com/verified-access/latest/ug/what-is-verified-access.html), [Verified Access policies](https://docs.aws.amazon.com/verified-access/latest/ug/auth-policies.html), [Verified Access pricing](https://aws.amazon.com/verified-access/pricing/), [non-HTTP(S) GA (2025)](https://aws.amazon.com/about-aws/whats-new/2025/02/aws-verified-access-zero-trust-resources-non-https-protocols/), [GovCloud Verified Access](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-verified-access.html)
- [Microsoft — Zero Trust guidance](https://learn.microsoft.com/en-us/security/zero-trust/), [Global Secure Access](https://learn.microsoft.com/en-us/entra/global-secure-access/overview-what-is-global-secure-access), [Conditional Access](https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview), [application proxy](https://learn.microsoft.com/en-us/entra/identity/app-proxy/overview-what-is-app-proxy)
- [OMB M-22-09](https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf), [OMB M-25-04](https://www.whitehouse.gov/wp-content/uploads/2025/01/M-25-04-Fiscal-Year-2025-Guidance-on-Federal-Information-Security-and-Privacy-Management-Requirements.pdf), [EO 14306](https://www.whitehouse.gov/wp-content/uploads/2025/06/eo-14306.pdf)
- [CISA — Zero Trust Maturity Model v2.0](https://www.cisa.gov/sites/default/files/2023-04/CISA_Zero_Trust_Maturity_Model_Version_2_508c.pdf) and [announcement](https://www.cisa.gov/news-events/alerts/2023/04/11/cisa-releases-zero-trust-maturity-model-version-2), [Microsegmentation guidance (2025)](https://www.cisa.gov/sites/default/files/2025-07/ZT-Microsegmentation-Guidance-Part-One_508c.pdf)
- [DoD Zero Trust Strategy](https://dodcio.defense.gov/Portals/0/Documents/Library/DoD-ZTStrategy.pdf), [strategy placemats](https://dodcio.defense.gov/Portals/0/Documents/Library/ZT-StrategyPlacemats.pdf), [Execution Roadmap v1.1](https://dodcio.defense.gov/Portals/0/Documents/Library/ZT-ExecutionRoadmap-v1.1.pdf), [NSA Zero Trust Implementation Guideline Primer (Jan 2026)](https://media.defense.gov/2026/Jan/08/2003852320/-1/-1/0/CTR_ZERO_TRUST_IMPLEMENTATION_GUIDELINE_PRIMER.PDF), [OT zero-trust guide announcement (Apr 2026)](https://dodcio.defense.gov/In-the-News/Article/4473613/cisa-and-us-government-partners-unveil-guide-to-accelerate-zero-trust-adoption/)
- [CISA AA24-060B](https://www.cisa.gov/news-events/alerts/2024/02/29/cisa-and-partners-release-advisory-threat-actors-exploiting-ivanti-connect-secure-and-policy-secure), [AA23-325A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-325a), [BOD 26-02](https://www.cisa.gov/news-events/directives/bod-26-02-mitigating-risk-end-support-edge-devices)
- [MITRE ATT&CK — T1190](https://attack.mitre.org/techniques/T1190/), [T1133](https://attack.mitre.org/techniques/T1133/)

Verified: 2026-10-27
