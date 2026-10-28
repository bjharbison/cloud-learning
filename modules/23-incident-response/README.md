# 23 — Cloud incident response and forensics: evidence, containment, credential compromise playbooks

> **In one sentence:** you'll be able to run the first hours of a cloud incident — preserve the right evidence, contain a compromised credential or admin identity on any of the three clouds without destroying what you need, hunt for persistence, and recover — using NIST's current incident response guidance and the providers' own playbooks.

**Prereqs:** modules 00–22 (module 18 for evidence in logs; module 22 for the detections that start an incident; modules 14–15 for identities and tokens; module 20 for rebuild-from-code) · **Time:** ~4 hours incl. lab · **Phase:** 6

## Learning objectives

- Explain **NIST SP 800-61 Rev. 3** and how it reorganizes incident response around **CSF 2.0**.
- Identify **cloud evidence** sources (audit and sign-in logs, flow logs, snapshots, configuration history) and how to preserve them with chain of custody.
- Choose **containment** actions per cloud that stop the attacker without destroying evidence.
- Execute playbooks for a **leaked service-account key / access key** and a **compromised admin identity**.
- Hunt for **cloud persistence** and recover by rebuilding from code.
- Know the providers' **IR guides** and **IR services**, and federal reporting timelines.

## Why this matters for the target roles

- **Cloud security / CTI:** most cloud incidents are identity incidents. Knowing what *actually* revokes access (and what doesn't) is the difference between containment and a false sense of it.
- **Customer engineer:** "What happens when something goes wrong?" is a standard procurement and ATO question. Answer with shared responsibility, evidence, and named playbooks.
- **Your background:** this is where intel tradecraft — timelines, attribution discipline, evidence handling — maps most directly onto cloud.

---

## Concepts

### NIST SP 800-61 Rev. 3 — the current frame

- **Rev. 3** (final **April 2025**) is titled *Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile*. **Rev. 2 is withdrawn.**
- Rev. 3 treats incident response as part of overall risk management, organized by the **CSF 2.0 Functions**:
  - **Govern, Identify, Protect** — the preparation layer (policies, roles, logging, hardening).
  - **Detect, Respond, Recover** — the incident response itself.
  - **Improvement** runs across all of them continuously, not only at the end.
- The **Rev. 2 lifecycle** — *Preparation → Detection & Analysis → Containment, Eradication & Recovery → Post-Incident Activity* — is still the vocabulary most playbooks use, including AWS's IR guide (which says it follows Rev. 2). Know both, and say which you're using.

**Bridge from intel:** Rev. 3's shift mirrors the move from "after-action review at the end" to continuous lessons learned feeding collection and targeting. An incident is never just closed; it changes the requirements.

### What's different about cloud IR

| On-prem habit | Cloud reality |
|---|---|
| Pull the disk, image it | Evidence is mostly **API logs**; disks are **snapshots** you take via API in seconds |
| Isolate by unplugging | Isolate by **firewall/security group, IAM deny, disabling identities** |
| The attacker has a foothold on a host | The attacker often has **a credential** — and needs no host at all |
| Infrastructure persists | Resources are **ephemeral** — autoscaling may delete your evidence before you look |
| You own every layer | **Shared responsibility** — the provider investigates its layers; you investigate yours and can't image their hardware |
| Password reset ends access | **Tokens outlive passwords**: refresh tokens, OAuth grants, cloud sessions, and federation trusts must be revoked separately |

> **Shared responsibility — say it plainly:** providers respond to incidents in *their* infrastructure and notify you (Google's data incident process, for example). **Detecting, containing, investigating, and recovering from compromise of your identities, keys, configurations, firewall rules, VPNs, and workloads are always the customer's.** A provider IR service can help — you still own the decisions.

### Preparation (Govern / Identify / Protect)

- **Logging that exists before the incident** (module 18): Data Access / data events where it matters, centralized, retained 12+ months, Entra sign-in export.
- **IR access ready in advance:** a pre-approved responder role (read audit logs, snapshot, disable identities) and **break-glass accounts** (module 15), tested.
- **A forensics landing place:** a separate project/account/subscription where evidence copies go, with tight access and immutability — AWS's Security Reference Architecture describes a dedicated **forensics account**; Microsoft's **chain-of-custody** reference architecture uses a separate SOC subscription with immutable blob storage under **legal hold** and hashes stored in Key Vault.
- **Contacts:** Google **Essential Contacts**, AWS account security contacts, Microsoft tenant notification settings — so provider notices reach a human.
- **Playbooks and retainers:** written, exercised playbooks; optional retainers (Mandiant via Google Cloud; **AWS Security Incident Response**; **Microsoft Incident Response**, formerly DART).

### Evidence: what to collect and how to keep it

| Evidence | Google Cloud | AWS | Azure | Notes |
|---|---|---|---|---|
| Control-plane actions | Admin Activity (400 d) | CloudTrail management events | Activity Log | Always on |
| Data access | Data Access logs | CloudTrail data events | Resource logs | Only if enabled beforehand |
| Sign-ins / tokens | Cloud Identity / Workspace login audit | `ConsoleLogin`, STS events | Entra sign-in + audit logs | Entra keeps 7/30 days unless exported |
| Network | VPC Flow Logs (sampled metadata) | VPC Flow Logs | VNet flow logs (NSG flow logs retire Sept 30, 2027) | Metadata, no payloads |
| Disk state | `gcloud compute snapshots create` | `aws ec2 create-snapshot` | `az snapshot create` | Snapshot **before** you stop or delete |
| Config history | Cloud Asset Inventory ⚠️ (not covered in depth) | AWS Config | Resource Graph / change analysis ⚠️ | What did it look like before? |
| Object history | Object Versioning / soft delete (module 08) | S3 Versioning | Blob versioning / soft delete | Recover overwritten data |

**Chain of custody, cloud style:** export logs and snapshot metadata to the forensics project, **hash** each exported file (SHA-256), store in **versioned, retention-locked** storage (Bucket Lock / S3 Object Lock / immutable blob), restrict access, and record who did what, when — your own actions appear in the audit log too, which helps.

**Bridge from intel:** this is evidence handling for a report that may end up in front of lawyers or a review board. Document sources, preserve originals, work from copies, keep a timeline in UTC.

### Containment that doesn't destroy evidence

Order of operations: **preserve volatile evidence → contain → investigate → eradicate**. In practice you snapshot and export first (minutes), then cut access. Don't delete a compromised VM or identity in the first hour — **disable** it.

| Goal | Google Cloud | AWS | Azure / Entra |
|---|---|---|---|
| Stop a leaked key | Disable the SA key (`gcloud iam service-accounts keys disable`), then delete after rotation | Set access key **Inactive** (`aws iam update-access-key --status Inactive`) | Remove/rotate app secret or certificate ⚠️ (app registration credentials; not covered in the lab) |
| Stop tokens already issued | **Disable the service account** or apply an **IAM deny policy**; bearer tokens can live up to an hour | **Revoke active sessions** (inline `AWSRevokeOlderSessions` policy denying tokens issued before now) and/or a deny policy on the user | **Revoke sessions** (`revokeSignInSessions`); **CAE** propagates critical events, up to ~15 minutes |
| Stop a human | Revoke the user's OAuth grants and sessions; suspending or resetting a password alone does **not** kill existing tokens | Deactivate keys, remove console password, revoke role sessions; Identity Center sessions are revoked in Identity Center | Disable account, revoke sessions, reset password (twice for hybrid AD accounts), disable devices |
| Isolate a VM | Firewall rule / remove external IP; snapshot first | Isolation security group; snapshot first | NSG rule; snapshot first |
| Provider-applied quarantine | Auto-disables SA keys found leaked publicly (`iam.serviceAccountKeyExposureResponse`, default `DISABLE_KEY` since June 2024) | Attaches **`AWSCompromisedKeyQuarantineV3`** to an IAM user with exposed keys (don't remove it) | Entra ID Protection leaked-credential detection ⚠️ (not covered here) |

**The trap:** deactivating an AWS access key doesn't, by itself, invalidate temporary credentials the attacker already minted from it (`GetSessionToken`, `AssumeRole`). AWS's guidance is to also **change permissions** — deny by user or revoke sessions — because permissions are checked on every request. Google's equivalent warning: tokens issued by an SA stay valid until they expire, so disable the SA or deny it, and wait at least 60 minutes before re-enabling.

### Playbook 1 — leaked service-account key / access key

```
1 Triage     What key? Whose? Where was it exposed (repo, ticket, laptop)? When created, last used?
2 Preserve   Export audit logs for the principal (all projects/accounts/Regions) → hash → forensics store
3 Contain    Disable key → disable/deny the principal (tokens!) → block key creation by policy
4 Scope      Every action by the principal since key creation: new keys/users/roles (T1098.001/.003, T1136.003),
             discovery (T1580), data reads (T1530 — only if data logs on), transfers (T1537), log tampering (T1685.002),
             compute for mining (T1496.001), all Regions
5 Eradicate  Remove attacker-created keys, users, roles, trust-policy changes, functions, instances
6 Recover    New credential (better: workload identity federation, no key — module 15); redeploy from code
7 Improve    Secret scanning in CI, org policy blocking keys, detection for key use from new IPs (module 22)
```

Where the key came from matters: Google and AWS both scan public code for their key formats and act (auto-disable / quarantine) — but private repos, tickets, chat, and laptops aren't covered.

### Playbook 2 — compromised admin identity

```
1 Triage     Sign-in anomalies (new ASN/country, impossible travel, MFA fatigue — T1621), admin actions out of pattern
2 Preserve   Export sign-in + audit logs for the user and everything they touched; snapshot affected VMs
3 Contain    Disable the account AND revoke sessions/tokens; use break-glass if the admin was your only admin;
             check the attacker didn't add MFA methods or federation (T1556.007) to keep access
4 Scope      New users/SPs/apps and credentials (T1098.001, T1136.003), role grants (T1098.003), consent grants,
             token theft (T1528, T1550.001), SAML/federation changes (T1606.002 forged SAML tokens),
             policy/guardrail changes (T1666, module 20), logging changes (T1685.002), destructive actions (T1485, T1486, T1531)
5 Eradicate  Remove every persistence item found; rotate secrets the admin could read; re-verify federation trust
6 Recover    Re-enable with phishing-resistant MFA, least privilege, JIT (module 15); rebuild changed infra from code
7 Improve    Conditional access / context-aware access; alerts for each persistence path you found
```

**The cloud-specific lesson:** admins can create *other* ways in — a new service principal with a secret, a federated trust, a role assumable from an outside account. If you only reset the admin's password, the attacker walks back in through the door they built.

### Provider guides and services

| | Google Cloud | AWS | Microsoft |
|---|---|---|---|
| Customer guidance | *Respond to compromised Google Cloud credentials*; Google blog *Collecting and analyzing cloud forensics* (Dec 2025) | *AWS Security Incident Response Guide*; re:Post *unauthorized activity* article; SRA forensics guidance | Incident response playbooks (phishing, password spray, app consent grant, compromised apps); *Revoke user access in an emergency*; chain-of-custody architecture |
| Provider's own process | Data incident response process (Google's side) | — | — |
| IR service | **Mandiant** Incident Response / retainer | **AWS Security Incident Response** (Dec 2024; first 10,000 findings/month free; 24/7 CIRT; log-based, no disk forensics) | **Microsoft Incident Response** |
| Open-source tooling | **Cloud Forensics Utils** (multi-cloud), dftimewolf, Timesketch, Plaso | Automated IR and forensics framework (AWS Prescriptive Guidance) | Microsoft-Extractor-Suite (by Invictus IR, *not* Microsoft); CISA Untitled Goose Tool ⚠️ (maintenance status unverified) |

---

## Text diagram — first hour of a leaked SA key on Google Cloud

```
 T+0   Alert: SA key used from unfamiliar IP (module 22) ── or Google auto-disabled a publicly leaked key
 T+5   Preserve: gcloud logging read principalEmail=SA (aggregated sink, 400 d Admin Activity)
              → evidence.json → sha256sum → forensics project bucket (versioned, retention)
 T+15  Contain: keys disable → service-accounts disable (kills new tokens; existing ≤ 1 h)
              → deny policy on the SA if it must stay enabled → org policy: disable SA key creation
 T+30  Scope:  what did the SA do? keys/roles created? List*/Get* bursts? storage reads (Data Access on?)
              cross-project copies? sinks touched? new VMs (mining)?   → timeline in UTC
 T+60  Snapshot any VM it created or touched (before delete); then eradicate; rotate; rebuild from Terraform
 Later Lessons → detections (22), guardrails (20), posture checks (21); reporting clock (federal: 1 hour to CISA)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Disable a long-lived workload credential | `keys disable` / `keys delete` | `update-access-key --status Inactive` | Remove app secret/cert ⚠️ | |
| Kill already-issued tokens | Disable SA or deny policy (tokens ≤ 1 h) | Revoke sessions (`AWSRevokeOlderSessions`); deny | `revokeSignInSessions`; CAE (≤ ~15 min) | Each cloud handles token lifetime differently |
| Automatic action on public leaks | Auto-disable leaked SA keys (default since June 2024) | `AWSCompromisedKeyQuarantineV3` attached | ⚠️ not verified | Google acts by default; AWS acts via support case |
| Disk evidence | Snapshots (`snapshots create`) | EBS snapshots | Managed disk snapshots | All API-driven, seconds to start |
| Forensics landing zone | Separate forensics project ⚠️ (pattern, not a named Google product) | SRA forensics account | SOC subscription + immutable storage + Key Vault hashes | |
| Provider IR service | Mandiant (Google Cloud) | AWS Security Incident Response | Microsoft Incident Response | AWS's is a metered cloud service |
| Network evidence | VPC Flow Logs | VPC Flow Logs | VNet flow logs | NSG flow logs retire Sept 30, 2027 |

## Administer and monitor it

- **Exercise the playbooks** quarterly (tabletop) and annually (live, in a sandbox — this module's lab).
- **Pre-stage access:** responder roles with just-enough permissions; test break-glass; confirm log retention covers your dwell-time assumptions.
- **Track:** time to detect, time to contain, time to report; percentage of incidents where evidence was missing (that's a logging requirement, module 18).
- **Watch your own actions:** responders' activity is in the audit log; it should match the case notes.

## Security angle

1. **Deleting instead of disabling** — destroys evidence and the attacker's footprint.
2. **Password reset without token revocation** — the attacker keeps their session.
3. **Missing persistence** — new keys, roles, SPs, federation trusts, or functions left behind.
4. **Single-Region investigation** — attackers mine crypto in Regions you never use.
5. **No data-plane logs** — "we can't tell what they read" becomes the breach notification.
6. **IR roles granted during the incident** — slow, and the grant itself is noisy; pre-provision.
7. **Ignoring provider notifications** — auto-disabled keys and quarantine policies are signals, not inconveniences.

## Threat intel angle

| Stage | Techniques to hunt | Where it shows |
|---|---|---|
| Access | T1078.004 Valid Accounts: Cloud Accounts; T1621 MFA Request Generation | Sign-in logs, `ConsoleLogin`, SA use from new IPs |
| Persistence | T1098.001 Additional Cloud Credentials; T1098.003 Additional Cloud Roles; T1136.003 Create Account: Cloud Account; T1556.007 Hybrid Identity | Admin Activity / CloudTrail / Entra audit logs |
| Token abuse | T1528 Steal Application Access Token; T1550.001 Application Access Token; T1606.002 SAML Tokens | Sign-ins from unusual apps; tokens with no matching sign-in |
| Impairment | T1685.002 Disable or Modify Cloud Log; T1666 Modify Cloud Resource Hierarchy | Logging and org changes |
| Impact | T1537 Transfer Data to Cloud Account; T1485 Data Destruction; T1486 Data Encrypted for Impact; T1531 Account Access Removal | Snapshot sharing, mass deletes, SSE-C rewrites (module 08), admins locked out |

**Cases worth reading** (modules 15–18 covered them): Storm-0558's forged tokens (T1606), the SSE-C ransomware against S3 using stolen keys (module 08), and SolarWinds-era Golden SAML (T1606.002). Module 24 goes deeper on actors.

**Bridge to your CTI work:** the IR timeline *is* an intelligence product. Build it in UTC from audit logs, mark confidence on each inference ("data read — confirmed by Data Access log" vs "likely — no data logs"), and separate observed activity from attribution.

## Public sector notes

- **Federal agencies** must report incidents to **CISA within one hour** of identification by their top-level SOC/CSIRT (CISA's *Federal Incident Notification Guidelines*, effective April 2017).
- CISA's *Federal Government Cybersecurity Incident and Vulnerability Response Playbooks* (2021, under EO 14028; a 2024 revision appears on cisa.gov ⚠️ changes not reviewed) standardize agency IR steps.
- **CIRCIA** (critical infrastructure reporting: 72 hours for covered incidents, 24 hours for ransom payments once effective): the final rule went to OIRA for review on **October 1, 2026** and is **not yet in effect**.
- Cloud contracts and FedRAMP authorizations define provider-to-agency notification duties; know where those clauses live (module 26).

## Key takeaways

- **NIST SP 800-61 Rev. 3** (April 2025) frames IR in CSF 2.0 Functions; Rev. 2's four phases remain common vocabulary.
- Cloud evidence = **audit/sign-in logs, flow logs, snapshots, config and object history** — preserved, hashed, and stored immutably in a separate forensics project/account.
- **Disable, don't delete**; **snapshot before stopping**; **revoke tokens, not just passwords and keys**.
- Leaked key: disable key → disable/deny principal → scope all Regions → remove persistence → replace with keyless identity.
- Compromised admin: disable + revoke sessions → hunt every persistence path → recover with phishing-resistant MFA and JIT.
- Provider guides and services exist (Google, AWS Security Incident Response, Microsoft IR); **responding to compromise of your identities and configurations is always the customer's.**

## Sources

- [NIST — SP 800-61 Rev. 3 announcement](https://www.nist.gov/news-events/news/2025/04/nist-revises-sp-800-61-incident-response-recommendations-and-considerations), [SP 800-61 Rev. 3 (PDF)](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r3.pdf), [SP 800-61 Rev. 2 (withdrawn)](https://csrc.nist.gov/pubs/sp/800/61/r2/final)
- [Google Cloud — Respond to compromised credentials](https://docs.cloud.google.com/docs/security/compromised-credentials), [Restricting service accounts (key exposure response)](https://docs.cloud.google.com/organization-policy/restrict-service-accounts), [Leaked SA keys auto-disable (blog)](https://cloud.google.com/blog/products/identity-security/automatically-disabling-leaked-service-account-keys-what-you-need-to-know), [gcloud keys disable](https://docs.cloud.google.com/sdk/gcloud/reference/iam/service-accounts/keys/disable), [gcloud keys delete](https://docs.cloud.google.com/sdk/gcloud/reference/iam/service-accounts/keys/delete), [gcloud compute snapshots create](https://docs.cloud.google.com/sdk/gcloud/reference/compute/snapshots/create), [How Google does it: cloud forensics](https://cloud.google.com/transform/how-google-does-it-collecting-and-analyzing-cloud-forensics), [Container forensics](https://cloud.google.com/blog/products/containers-kubernetes/best-practices-for-performing-forensics-on-containers), [Data incident response process](https://docs.cloud.google.com/docs/security/incident-response), [VPC Flow Logs](https://docs.cloud.google.com/vpc/docs/flow-logs), [Mandiant IR services](https://cloud.google.com/security/consulting/mandiant-incident-response-services)
- [AWS — Security Incident Response Guide](https://docs.aws.amazon.com/whitepapers/latest/aws-security-incident-response-guide/welcome.html), [AWS Security Incident Response](https://docs.aws.amazon.com/security-ir/latest/userguide/what-is.html), [launch](https://aws.amazon.com/about-aws/whats-new/2024/12/aws-security-incident-response/), [metered pricing and free tier](https://aws.amazon.com/about-aws/whats-new/2025/11/security-incident-response-metered-pricing-free-tier/), [Unauthorized activity (re:Post)](https://repost.aws/knowledge-center/potential-account-compromise), [AWSCompromisedKeyQuarantineV3](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSCompromisedKeyQuarantineV3.html), [Revoke role sessions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_revoke-sessions.html), [Disable temporary credentials' permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_control-access_disable-perms.html), [update-access-key](https://docs.aws.amazon.com/cli/latest/reference/iam/update-access-key.html), [get-access-key-last-used](https://docs.aws.amazon.com/cli/latest/reference/iam/get-access-key-last-used.html), [create-snapshot](https://docs.aws.amazon.com/cli/latest/reference/ec2/create-snapshot.html), [SRA forensics account](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-cyber-forensics/forensics-account.html), [Automated IR and forensics pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/automate-incident-response-and-forensics.html), [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
- [Microsoft — Incident response playbooks](https://learn.microsoft.com/en-us/security/operations/incident-response-playbooks), [Revoke user access in an emergency](https://learn.microsoft.com/en-us/entra/identity/users/users-revoke-access), [revokeSignInSessions](https://learn.microsoft.com/en-us/graph/api/user-revokesigninsessions?view=graph-rest-1.0), [Continuous access evaluation](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-continuous-access-evaluation), [az ad user](https://learn.microsoft.com/en-us/cli/azure/ad/user), [az snapshot](https://learn.microsoft.com/en-us/cli/azure/snapshot), [Computer forensics chain of custody](https://learn.microsoft.com/en-us/azure/architecture/example-scenario/forensics/), [NSG flow logs migration](https://learn.microsoft.com/en-us/azure/network-watcher/nsg-flow-logs-migrate), [Microsoft Incident Response ransomware approach](https://learn.microsoft.com/en-us/security/ransomware/incident-response-playbook-dart-ransomware-approach)
- [CISA — Federal Incident Notification Guidelines](https://www.cisa.gov/federal-incident-notification-guidelines), [Federal IR and vulnerability response playbooks](https://www.cisa.gov/resources-tools/resources/federal-government-cybersecurity-incident-and-vulnerability-response-playbooks), [CIRCIA](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia), [CIRCIA final rule at OIRA (reginfo.gov)](https://www.reginfo.gov/public/do/eoDetails?rrid=1550967)
- [Google Cloud Forensics Utils](https://github.com/google/cloud-forensics-utils), [Microsoft-Extractor-Suite (Invictus IR)](https://www.powershellgallery.com/packages/Microsoft-Extractor-Suite), [CISA Untitled Goose Tool](https://github.com/cisagov/untitledgoosetool)
- [MITRE ATT&CK — T1098.001](https://attack.mitre.org/techniques/T1098/001/), [T1136.003](https://attack.mitre.org/techniques/T1136/003/), [T1528](https://attack.mitre.org/techniques/T1528/), [T1550.001](https://attack.mitre.org/techniques/T1550/001/), [T1606.002](https://attack.mitre.org/techniques/T1606/002/), [T1556.007](https://attack.mitre.org/techniques/T1556/007/), [T1531](https://attack.mitre.org/techniques/T1531/), [T1485](https://attack.mitre.org/techniques/T1485/), [T1486](https://attack.mitre.org/techniques/T1486/), [T1537](https://attack.mitre.org/techniques/T1537/)

Verified: 2026-10-28
