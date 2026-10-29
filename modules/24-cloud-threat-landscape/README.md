# 24 — Cloud threat landscape for CTI: nation-state and criminal TTPs against cloud and identity; vendor threat intel sources

> **In one sentence:** you'll be able to brief how real intrusions into cloud and identity systems happen — using six well-documented public cases, ATT&CK mappings, and the providers' own threat-intel products — and turn that reporting into collection requirements and detections for a cloud customer.

**Prereqs:** modules 00–23 (module 15 for tokens and federation; 18 for audit logs; 22 for detections; 23 for response) · **Time:** ~3 hours incl. lab · **Phase:** 6

> **How to read this module.** It's written as a CTI product: bottom line first, then case files, then cross-case analysis. Every assessment is attributed to whoever made it, with their confidence language. Public sources only.

## Learning objectives

- Summarize six public cloud/identity intrusion cases: actor, access, techniques, what defenders could see, and the lesson.
- Map each to **MITRE ATT&CK** (v20, October 2026) technique IDs.
- Explain the cross-case patterns: identity as the perimeter, tokens over passwords, trusted third parties, logging as the deciding factor.
- Name the **threat-intel products and teams** of Google, Microsoft, and AWS, and their actor-naming schemes.
- Describe how CTI feeds cloud detection: **STIX/TAXII**, threat lists, IOC matching, and behavioral rules.

## Why this matters for the target roles

- **Cloud CTI:** this is the job — knowing how cloud intrusions really unfold and writing for defenders and executives.
- **Customer engineer:** customers ask "what are you seeing?" A CE who can brief Storm-0558, the CSRB findings, and the Snowflake campaign — accurately, with sources — earns trust fast.
- **Your background:** you already do actor tracking, attribution discipline, and I&W. What's new is the terrain: control planes, identity providers, and SaaS tokens.

---

## Bottom line up front

1. **Identity is the main cloud attack surface.** In every case below, the adversary either used valid credentials or forged/stole tokens. Google's *Cloud Threat Horizons H1 2026* report says threat actors exploited identity issues to gain initial access in **83%** of the incidents it reviewed involving major cloud and SaaS environments.
2. **Tokens outlive passwords.** Forged signing-key tokens (Storm-0558), OAuth app grants (Midnight Blizzard, UNC6040), and stolen refresh tokens (UNC6395) bypass MFA and password resets.
3. **Trust relationships are the force multiplier.** Help desks, test tenants, OAuth integrations, and federation trusts let one foothold become broad access.
4. **Logging decides whether you see it.** A federal agency caught Storm-0558 only because it had premium Microsoft 365 audit logging (module 18).
5. **Criminal and state actors use the same playbook.** Scattered Spider and APT29 both social-engineer identities, register their own MFA devices, and abuse federation. Defenses overlap — which makes the investment easier to justify.

---

## Concepts

### Naming: one actor, many names

Each vendor names actors differently. Your intel-world habit of tracking aliases transfers directly.

| Vendor | Scheme | Example |
|---|---|---|
| **Microsoft** | Weather families by origin or motive (since April 2023): Typhoon = China, Blizzard = Russia, Sandstorm = Iran, Sleet = North Korea, Tempest = financially motivated; **Storm-####** = developing cluster | Midnight Blizzard; Octo Tempest; Storm-0558 (now listed as **Antique Typhoon** ⚠️ rename date not confirmed) |
| **Google (GTIG / Mandiant)** | **UNC####** for uncategorized clusters; **APT/FIN** numbers historically. In **July 2026** Google began moving to two-word cryptonyms whose second word marks origin or type (e.g., RELIC = Russia, CASTLE = China, COMET = cybercrime) | UNC5537, UNC3944; APT29 → **ICE RELIC** |
| **MITRE ATT&CK** | G#### group IDs; C#### campaign IDs | Scattered Spider = **G1015**; Salesforce data exfiltration campaign (UNC6040/UNC6240) = **C0059** |
| **Governments** | Usually the vendor name plus attribution to a state service | APT29 "almost certainly part of the SVR" (NCSC-UK and partners) |

**Bridge from intel:** treat vendor names as **source-specific designators**, not ground truth. Two vendors' clusters may overlap only partly. Say "Microsoft tracks as… Mandiant tracks as…", exactly as you'd caveat different agencies' reporting.

### The ATT&CK version caveat

ATT&CK **v19** (April 2026) split Defense Evasion into **Stealth (TA0005)** and **Defense Impairment (TA0112)** and revoked **T1562**. Older reports say **T1562.008**; current ATT&CK says **T1685.002 Disable or Modify Cloud Log** (module 22). v19 also added **T1684.001 Impersonation** under Social Engineering. When an ID below comes from an advisory written before v19, it's marked *(per advisory)*.

---

## Case files

Each card: **who said what**, how they got in, what they did, what defenders could have seen, and the lesson.

### Case 1 — Storm-0558: forged tokens from a stolen signing key (2023)

| | |
|---|---|
| **Reporter / attribution** | Microsoft assesses "with moderate confidence" a China-based espionage actor (July 14, 2023). CISA/FBI advisory **AA23-193A** (July 12, 2023). DHS **Cyber Safety Review Board (CSRB)** report (released April 2, 2024). |
| **Access** | The actor held a Microsoft **consumer (MSA) signing key**. A validation flaw let that key sign tokens that Exchange Online accepted for **enterprise** mailboxes. |
| **Activity** | Forged tokens to read Outlook Web Access and Outlook.com mail; began about May 15, 2023. Microsoft said about **25 organizations**, including government agencies, were affected. |
| **ATT&CK** | T1606 Forge Web Credentials; T1114.002 Remote Email Collection *(per advisory)*; T1078.004 Cloud Accounts |
| **How it was caught** | A federal civilian agency saw **MailItemsAccessed** events from an unexpected application ID — logging that then required a premium license. |
| **Twist** | Microsoft's September 2023 post said the key probably leaked in a 2021 crash dump. In **March 2024** Microsoft added a note: it had **not found** a crash dump containing the key. How the key was taken is still not publicly established. |

**CSRB findings (paraphrased):** the intrusion was **preventable**; a series of Microsoft decisions reflected a culture that **deprioritized enterprise security investment and rigorous risk management**. Recommendations for all cloud providers included modern identity and key-management controls, **default audit logging at no extra charge**, and better victim notification. The CSRB also recommended updating FedRAMP (module 26).

**Lesson:** customers couldn't have prevented a provider's key theft — signing keys sit on the provider's side of shared responsibility. What customers controlled was **visibility**: audit logging, a baseline of normal app behavior, and retention. Ask providers how they protect token-signing keys and what logs you get by default.

### Case 2 — Midnight Blizzard (APT29) inside Microsoft's corporate tenant (2023–2024)

| | |
|---|---|
| **Reporter / attribution** | Microsoft (January 25, 2024; update March 8, 2024). Microsoft notes the U.S. and UK governments attribute the actor to Russia's **SVR**. A Feb 2024 joint advisory led by NCSC-UK (with NSA, CISA, FBI, and others) says APT29 is "almost certainly part of the SVR." |
| **Access** | Low-volume **password spray** against a **legacy, non-production test tenant** account with **no MFA**, routed through **residential proxies** so IP blocklists didn't help. |
| **Activity** | Compromised a legacy test **OAuth application** that had elevated access to the corporate tenant; created more OAuth apps and a user to consent to them; granted the Exchange Online **full_access_as_app** role; read senior leaders' and security staff mailboxes. Microsoft's March update: the actor later used what it stole to reach **some source code repositories and internal systems**, and password spraying rose as much as **tenfold** in February 2024. |
| **ATT&CK** | T1110.003 Password Spraying; T1078.004; T1098.001 Additional Cloud Credentials; T1098.003 Additional Cloud Roles; T1550.001 Application Access Token *(per advisory)*; T1090.002 External Proxy *(per advisory)* |
| **Government response** | CISA **Emergency Directive 24-02** (April 2024) ordered agencies to analyze their email with Microsoft and rotate any credentials it exposed. |

**Lesson:** "test" and "legacy" tenants and apps are production attack surface. Inventory OAuth apps, flag app-only permissions to mail and files, and require MFA everywhere. The NCSC advisory adds the broader SVR cloud playbook: spraying service and dormant accounts, token theft (T1528), MFA bombing (T1621), and registering their own devices (T1098.005).

### Case 3 — UNC5537 and Snowflake customer instances (2024)

Module 09 introduced this case; here's the CTI view.

| | |
|---|---|
| **Reporter / attribution** | Mandiant (June 10, 2024): financially motivated cluster **UNC5537**; members assessed with moderate confidence to be in North America, with an associate in Turkey. |
| **Access** | Credentials from **infostealer** logs (some dating to 2020) used against customer Snowflake accounts with **no MFA**, no rotation, and **no network allowlists**. No breach of Snowflake's own platform was found. |
| **Activity** | Mandiant and Snowflake notified about **165** potentially exposed organizations. Data was staged and downloaded, then used for extortion. |
| **ATT&CK** | T1078.004; T1530 Data from Cloud Storage; T1213 Data from Information Repositories |
| **Law enforcement** | A Canadian defendant pleaded guilty in U.S. federal court (W.D. Wash., August 2026) to hacking and extorting customers of a U.S. cloud data company. Note DOJ's headline describes "hacking" the provider; Mandiant found no breach of Snowflake's own environment — compare sources' wording before you repeat either. |

**Lesson:** shared responsibility in SaaS: the platform was secure, but **customer identity settings** weren't. Credential-exposure monitoring (infostealer logs) is a legitimate CTI deliverable.

### Case 4 — Scattered Spider / UNC3944 / Octo Tempest: the help desk is the perimeter (2022–present)

| | |
|---|---|
| **Reporter** | CISA/FBI **AA23-320A** (Nov 2023; updated July 29, 2025 with Canadian, Australian, and UK partners); Microsoft (*Octo Tempest*, Oct 2023); Mandiant (*UNC3944 targets SaaS*, June 2024; hardening guide, May 2025). ATT&CK **G1015**. |
| **Access** | Calls to IT help desks impersonating employees to reset passwords and MFA; SIM swapping; **MFA fatigue**; SMS phishing. The 2025 update adds multi-call vishing and fake employee identities. |
| **Cloud and identity tradecraft** | Registered their own MFA devices; **added a federated identity provider** to the victim's SSO tenant; used **AWS Systems Manager Inventory** for discovery and **created EC2 instances**; Microsoft reports Azure role abuse up to the tenant root and theft of AD databases from **VM disk snapshots**; Mandiant reports new VMs in vSphere and **Azure** (no EDR on them) and **Golden SAML** via stolen ADFS certificates; exfiltration to attacker **S3** buckets and MEGA. |
| **Monetization** | Data extortion and ransomware affiliations (ALPHV/BlackCat; DragonForce per the 2025 update). |
| **ATT&CK** | T1566.004 Spearphishing Voice; T1684.001 Impersonation; T1621; T1098.005 Device Registration *(per advisory)*; T1484.002 Trust Modification *(per advisory)*; T1578.002 Create Cloud Instance; T1606.002 SAML Tokens *(per Mandiant/Microsoft reporting; module mapping)*; T1537 Transfer Data to Cloud Account *(module mapping)* |

**Lesson:** this is the case for **phishing-resistant MFA**, **verified help-desk resets** (video or in-person, per Mandiant), and alerts on **new federation trusts, MFA-method changes, and new VMs or keys** — all audit-log events you met in modules 15 and 18.

### Case 5 — Volt Typhoon: living off the land and pre-positioning (2021–present)

| | |
|---|---|
| **Reporter / attribution** | CISA, NSA, FBI, and partners, **AA24-038A** (Feb 7, 2024): PRC state-sponsored. The authoring agencies assess **with high confidence** the actors are **pre-positioning** in IT networks to enable disruption of OT in U.S. critical infrastructure, with some footholds lasting **at least five years**. |
| **Access** | Exploited internet-facing edge devices; then relied mainly on **valid credentials**. |
| **Activity** | Built-in tools (**living off the land**) instead of malware; stole the AD database (**NTDS.dit**) with `ntdsutil`/`vssadmin` and cracked hashes offline; hid traffic through a botnet of end-of-life **SOHO routers** (the "KV botnet," disrupted by a court-authorized DOJ operation in Dec 2023). |
| **Cloud angle** | The advisory reports anomalous sign-ins to one victim's **Azure** tenant, possibly with credentials taken from AD — but says attribution of that activity was **inconclusive**. Don't overstate it. |
| **ATT&CK** | T1078 / T1078.004; T1003.003 NTDS *(per advisory)*; T1584.005 Botnet *(per advisory)*; T1110.002 Password Cracking |

**Lesson for cloud:** in **hybrid identity**, on-prem AD compromise is cloud compromise waiting to happen. LOTL leaves few indicators, so detection is **behavioral**: impossible travel, new admin sign-ins, and log clearing. Edge devices, VPNs, and identity sync are always the customer's responsibility.

### Case 6 — SaaS OAuth campaigns: UNC6040 and UNC6395 (2025)

| | |
|---|---|
| **Reporter** | Google Threat Intelligence Group (GTIG). UNC6040: June 4, 2025. UNC6395: Aug 26, 2025. ATT&CK campaign **C0059** covers UNC6040 (with UNC6240) only, not UNC6395. |
| **UNC6040** | Callers posing as IT support talked staff into authorizing a **modified Salesforce Data Loader** connected app (OAuth), then bulk-exported data. No Salesforce vulnerability. Extortion tracked separately (UNC6240, claiming "ShinyHunters"). Google's own corporate Salesforce instance was hit. |
| **UNC6395** | Used stolen **OAuth tokens for the Salesloft Drift integration** to query many Salesforce instances (Aug 8–18, 2025), then searched the data for **AWS access keys**, Snowflake tokens, and passwords. GTIG assesses the main goal was **credential harvesting**. |
| **ATT&CK** | UNC6040 (per C0059): T1598.004 Spearphishing Voice (for information); T1684.001 Impersonation; T1671 Cloud Application Integration; T1213.004 Data from CRM Software. UNC6395 *(module mapping)*: T1528 Steal Application Access Token; T1552 Unsecured Credentials |

**Lesson:** every OAuth integration is a **trusted relationship**. Govern connected apps, restrict API scopes, and scan SaaS records for secrets — UNC6395 turned a CRM breach into a cloud-credential harvest.

---

## Cross-case analysis

```
              INITIAL ACCESS                 ESCALATE / PERSIST                 OBJECTIVE
Storm-0558    stolen signing key ─► forged tokens (T1606) ──────────────────► mail collection
APT29         password spray, no-MFA test ─► OAuth app + full_access_as_app ─► mail, source code
UNC5537       infostealer creds, no MFA ─► (none needed) ───────────────────► bulk data, extortion
UNC3944       help-desk vishing, SIM swap ─► own MFA device, federation, VMs ─► data, ransomware
Volt Typhoon  edge exploit ─► NTDS theft, LOTL, valid accounts ──────────────► pre-positioning
UNC6040/6395  vishing / stolen OAuth tokens ─► connected apps ──────────────► CRM data, secrets
                                │
              Common thread: identity and tokens, not malware on a host
```

| Pattern | Cases | Telemetry that shows it (module 18) |
|---|---|---|
| Valid or forged credentials, no exploit | All six | Sign-in logs, token issuance, `MailItemsAccessed` |
| No MFA on a forgotten account | APT29, UNC5537 | Sign-ins without MFA; legacy auth |
| New OAuth app, consent, or app role | APT29, UNC6040, UNC6395 | Entra audit (consent, app role), SaaS connected-app logs |
| New federation trust / MFA device | UNC3944 | Entra audit, Okta system log |
| Cloud compute created for persistence | UNC3944 | Admin Activity `instances.insert`, CloudTrail `RunInstances`, Azure Activity |
| Bulk data pull | UNC5537, UNC6040 | Data Access logs / data events — **only if enabled** |

> **Shared responsibility — say it plainly:** only Storm-0558 began on the provider's side. In every other case the opening was something the **customer** controls: MFA, help-desk procedure, OAuth app governance, network allowlists, hybrid identity, and edge devices. **Identity, access control, firewall rules, VPN configuration, and remote-access exposure are always the customer's.**

## Google Cloud vs AWS vs Azure — threat intelligence

| Capability | Google Cloud | AWS | Azure / Microsoft | Notable difference |
|---|---|---|---|---|
| Threat-intel team | **Google Threat Intelligence Group (GTIG)** — Mandiant + former TAG | AWS security teams publish on the AWS Security Blog; internal sensors **MadPot** (honeypots), **Mithra** (domain-reputation graph), **Sonaris** (active defense) | **Microsoft Threat Intelligence** (formerly MSTIC) | AWS's intel mostly drives automatic protections, not a sold feed |
| Sold intel product | **Google Threat Intelligence** (2024): Mandiant intel + **VirusTotal** + Google telemetry + Gemini | No standalone intel product ⚠️ (none found) | **Microsoft Defender Threat Intelligence** capabilities, now folded into **Defender XDR and Sentinel** (standalone MDTI retired Aug 2026 ⚠️ date from secondary summary) | Google and Microsoft sell intel; AWS embeds it |
| Intel inside detection | SecOps **Applied Threat Intelligence** (IOC matching, curated detections) | **GuardDuty** findings, incl. **Extended Threat Detection** attack sequences (no extra charge) | Sentinel TI matching analytics; Defender XDR | |
| Bring your own intel | SecOps IOC ingestion ⚠️ (specifics not verified) | GuardDuty **threat / trusted entity lists** (IPs, CIDRs, domains; threat lists also SHA-256) | Sentinel **TAXII 2.x** connector and **upload API** (STIX) | AWS limits: 6 threat lists, 1 trusted list per Region |
| Periodic public reporting | **Cloud Threat Horizons** (latest: H1 2026), **M-Trends** | AWS Security Blog posts | **Microsoft Digital Defense Report** ⚠️ (not re-verified this run) | |
| Actor naming | UNC numbers; new two-word cryptonyms (2026) | No public scheme | Weather families + Storm-#### | |

## Administer and monitor it — CTI into detection

The flow from intel to detection is the module 22 lifecycle, fed by your reporting:

```
 Report (CISA / GTIG / Microsoft) ─► extract cloud TTPs ─► ATT&CK IDs ─► detection strategy (module 22)
        │                                                                      │
        └─► atomic IOCs (IPs, domains, hashes) ─► STIX/TAXII / threat lists ───┤
                                                                               ▼
                                         SIEM: behavior rules + IOC matching ─► runbook (module 23)
```

- **STIX** is the JSON format for threat data; **TAXII** is the protocol for exchanging it. Sentinel pulls from TAXII 2.0/2.1 servers into the **ThreatIntelIndicators** and **ThreatIntelObjects** tables (the legacy `ThreatIntelligenceIndicator` table stopped receiving data July 31, 2025).
- **GuardDuty entity lists** let you add your own malicious IPs and domains; matches become findings.
- **Indicators decay fast.** APT29's residential proxies made IP blocking useless. Put most effort into **behavior** (new OAuth grant + mail access; new federation trust; MFA reset then new device) and treat IOCs as enrichment.
- **CISA advisories** are free, public, and usually include ATT&CK tables. They're your best starting point with federal customers.

## Security angle

What a cloud customer should do, case by case:

1. **Phishing-resistant MFA everywhere**, including test tenants and service desks (APT29, UNC3944, UNC5537).
2. **Help-desk identity verification** before any password or MFA reset (UNC3944, UNC6040).
3. **OAuth and connected-app governance:** admin consent only, review app-only permissions, alert on new grants (APT29, UNC6040, UNC6395).
4. **Alert on identity-plane persistence:** new federation, new MFA method, new service principal credential (UNC3944; module 22).
5. **Turn on the logs that matter** and keep them 12+ months (Storm-0558; module 18).
6. **Treat on-prem AD and edge devices as cloud attack paths** (Volt Typhoon).
7. **Scan SaaS and tickets for secrets** (UNC6395).

## Threat intel angle — writing it up

- **Use estimative language and say whose it is.** "Microsoft assesses with moderate confidence…" — not "China did it."
- **Separate fact from assessment** the way the CSRB report does: what was observed, what was concluded, what's still unknown (the Storm-0558 key-theft path).
- **Write for two readers.** Executives want "what does this mean for us." Engineers want ATT&CK IDs, log sources, and queries.
- **Close the loop:** each report should end with collection gaps ("we don't log OAuth consents") and detection requests.

## Public sector notes

- **CSRB → FedRAMP.** The CSRB urged changes to FedRAMP and default logging; Microsoft expanded free audit logging after Storm-0558 (module 18). Expect agencies to ask every provider about key custody and default logs.
- **Emergency Directive 24-02** shows CISA can direct civilian agencies to act on a provider's breach. Know where to find ED and BOD texts on cisa.gov.
- **Volt Typhoon** is the reason critical-infrastructure and DoD customers ask about OT, edge devices, and LOTL detection — your OT/ICS background is directly relevant here.

## Key takeaways

- Six cases, one theme: **identity and tokens** — not malware on servers — drive cloud intrusions.
- **Storm-0558** was a provider-side key failure; the **CSRB** called it preventable and pushed default logging.
- **APT29** got into Microsoft through a **no-MFA test tenant** and an **OAuth app**.
- **UNC5537** needed no exploit: stolen passwords and no MFA.
- **Scattered Spider** proves the **help desk** is part of the identity perimeter.
- **Volt Typhoon**: LOTL and valid accounts; hybrid identity links on-prem compromise to cloud.
- Attribute every assessment to its source; map to current ATT&CK IDs (v19+ renumbered defense evasion).

## Sources

- Microsoft: [Storm-0558 mitigation (MSRC, Jul 2023)](https://www.microsoft.com/en-us/msrc/blog/2023/07/microsoft-mitigates-china-based-threat-actor-storm-0558-targeting-of-customer-email), [Analysis of Storm-0558 techniques (Jul 14, 2023)](https://www.microsoft.com/en-us/security/blog/2023/07/14/analysis-of-storm-0558-techniques-for-unauthorized-email-access/), [Storm-0558 key acquisition (Sep 2023; Mar 12, 2024 update)](https://www.microsoft.com/en-us/msrc/blog/2023/09/results-of-major-technical-investigations-for-storm-0558-key-acquisition), [Midnight Blizzard guidance (Jan 25, 2024)](https://www.microsoft.com/en-us/security/blog/2024/01/25/midnight-blizzard-guidance-for-responders-on-nation-state-attack/), [Midnight Blizzard update (Mar 8, 2024)](https://www.microsoft.com/en-us/msrc/blog/2024/03/update-on-microsoft-actions-following-attack-by-nation-state-actor-midnight-blizzard), [Octo Tempest (Oct 2023)](https://www.microsoft.com/en-us/security/blog/2023/10/25/octo-tempest-crosses-boundaries-to-facilitate-extortion-encryption-and-destruction/), [Threat actor naming](https://learn.microsoft.com/en-us/defender-xdr/microsoft-threat-actor-naming), [Sentinel threat intelligence](https://learn.microsoft.com/en-us/azure/sentinel/understand-threat-intelligence), [MDTI convergence (Tech Community, Jul 2026)](https://techcommunity.microsoft.com/blog/microsoftthreatprotectionblog/mdti-convergence-in-microsoft-sentinel-and-defender-xdr-is-complete/4541279)
- CISA / DHS / DOJ / NCSC: [AA23-193A (Jul 2023)](https://www.cisa.gov/sites/default/files/2023-07/aa23-193a_joint_csa_enhanced_monitoring_to_detect_apt_activity_targeting_outlook_online.pdf), [CSRB report page](https://www.cisa.gov/resources-tools/resources/CSRB-Review-Summer-2023-MEO-Intrusion) and [DHS release (Apr 2, 2024)](https://www.dhs.gov/news/2024/04/02/cyber-safety-review-board-releases-report-microsoft-online-exchange-incident-summer), [ED 24-02](https://www.cisa.gov/news-events/directives/ed-24-02-mitigating-significant-risk-nation-state-compromise-microsoft-corporate-email-system), [NCSC-UK et al. — SVR cloud access (Feb 2024)](https://www.ncsc.gov.uk/news/svr-cyber-actors-adapt-tactics-for-initial-cloud-access), [AA23-320A Scattered Spider](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a) and [July 2025 update (PDF)](https://www.ic3.gov/CSA/2025/250729.pdf), [AA24-038A Volt Typhoon (PDF)](https://www.ic3.gov/CSA/2024/240207.pdf), [DOJ — KV botnet disruption (Jan 2024)](https://www.justice.gov/usao-sdtx/pr/us-government-disrupts-botnet-peoples-republic-china-used-conceal-hacking-critical), [DOJ — guilty plea in cloud-customer extortion case (Aug 2026)](https://www.justice.gov/usao-wdwa/pr/canadian-pleads-guilty-hacking-us-cloud-storage-provider-and-extorting-its-customers)
- Google: [UNC5537 / Snowflake (Jun 2024)](https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion), [UNC3944 targets SaaS (Jun 2024)](https://cloud.google.com/blog/topics/threat-intelligence/unc3944-targets-saas-applications/), [UNC3944 hardening (May 2025)](https://cloud.google.com/blog/topics/threat-intelligence/unc3944-proactive-hardening-recommendations), [UNC6040 vishing (Jun 2025)](https://cloud.google.com/blog/topics/threat-intelligence/voice-phishing-data-extortion), [UNC6395 Salesloft Drift (Aug 2025)](https://cloud.google.com/blog/topics/threat-intelligence/data-theft-salesforce-instances-via-salesloft-drift), [Updated actor naming (Jul 2026)](https://cloud.google.com/blog/topics/threat-intelligence/updated-cyber-threat-actor-naming-system), [Google Threat Intelligence](https://cloud.google.com/security/products/threat-intelligence), [Cloud Threat Horizons H1 2026](https://cloud.google.com/security/report/resources/cloud-threat-horizons-report-h1-2026), [M-Trends 2026](https://cloud.google.com/blog/topics/threat-intelligence/m-trends-2026), [SecOps ATI curated detections](https://docs.cloud.google.com/chronicle/docs/detection/ati-curated-detections)
- AWS: [How AWS uses active defense (Oct 2024)](https://aws.amazon.com/blogs/security/how-aws-uses-active-defense-to-help-protect-customers-from-security-threats/), [GuardDuty Extended Threat Detection](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty-extended-threat-detection.html), [GuardDuty entity and IP lists](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_upload-lists.html)
- MITRE ATT&CK: [April 2026 (v19) updates](https://attack.mitre.org/resources/updates/updates-april-2026/), [T1606](https://attack.mitre.org/techniques/T1606/), [T1110.003](https://attack.mitre.org/techniques/T1110/003/), [T1621](https://attack.mitre.org/techniques/T1621/), [T1684](https://attack.mitre.org/techniques/T1684/), [T1685](https://attack.mitre.org/techniques/T1685/), [G1015 Scattered Spider](https://attack.mitre.org/groups/G1015/), [C0059](https://attack.mitre.org/campaigns/C0059/)

Verified: 2026-10-29
