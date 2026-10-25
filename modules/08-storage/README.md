# 08 — Storage: object, block, file; lifecycle, versioning, data protection

> **In one sentence:** you'll be able to pick the right kind of cloud storage, keep it from going public, make deletions recoverable (or impossible), and explain why "exposed bucket" keeps showing up in breach reporting.

**Prereqs:** modules 00–07 (module 05 for disks; module 04 for billing; module 03 for org policy) · **Time:** ~3 hours incl. lab · **Phase:** 2

## Learning objectives

- Distinguish **object**, **block**, and **file** storage and name each cloud's service for each.
- Choose a **storage class / access tier** and automate moves with **lifecycle rules** — without getting surprised by minimum-duration fees.
- Explain **versioning**, **soft delete**, and **retention locks** (WORM), and which one stops which threat.
- Configure **public-access prevention** on all three clouds: uniform bucket-level access + public access prevention, S3 Block Public Access, and Azure's anonymous-access setting.
- Read exposed-bucket incidents in ATT&CK terms and know which logs would have caught them.

## Why this matters for the target roles

- **Customer engineer / architect:** almost every workload stores data somewhere. "Which class, which region, how long, who can read it" is in every design review.
- **Cloud security:** a public bucket is the classic cloud breach, and storage is where ransomware-in-the-cloud lands. The controls are simple; leaving them off is common.
- **CTI:** "data from cloud storage" (T1530) appears in nation-state and criminal reporting alike. You need to tell a misconfiguration story from a stolen-credential story.

---

## Concepts

### Three kinds of storage

**Plain version:** block storage is a raw disk. File storage is a shared network drive. Object storage is a giant key-value store for whole files, reached over HTTPS.

| Kind | Plain meaning | Accessed by | Google Cloud | AWS | Azure |
|---|---|---|---|---|---|
| **Block** | A virtual hard drive attached to one VM (sometimes a few) | The VM's OS, as a device | **Persistent Disk**, **Hyperdisk**, Local SSD | **EBS** volumes | **Managed Disks** |
| **File** | A shared filesystem many machines mount | NFS / SMB | **Filestore** (managed NFS) | **EFS** (NFS), FSx family | **Azure Files** (SMB/NFS) |
| **Object** | Whole files ("objects") in flat containers ("buckets"), each with metadata | HTTPS API / CLI / SDK | **Cloud Storage** | **S3** | **Blob Storage** |

**Bridge to your homelab:** block is the virtual disk on your Proxmox VM. File is your NAS share mounted on several boxes. Object storage is the odd one out — think of a MinIO server: no mounting, no folders (just name prefixes that *look* like folders), everything via API calls that are authenticated and logged one by one.

**Why object storage dominates cloud designs:** it's cheap, effectively unlimited, highly durable, and every other service integrates with it — logs, backups, data lakes, ML training data, static websites. That ubiquity is also why it's the most-exposed resource type.

Block storage was covered in module 05 (boot disks). Two reminders: disks are zonal by default (regional/replicated options exist), and Local SSD data is lost when the VM stops. Everything below focuses on object storage, where the security decisions live.

### Buckets, objects, and where they live

- A **bucket** (Azure: a **container** inside a **storage account**) holds objects. Bucket names are globally unique on Google and AWS; Azure's storage account name is globally unique and becomes part of the URL (`<account>.blob.core.windows.net`).
- **Location** is chosen at creation: a region, a dual-region, or a multi-region (module 02). That's a data-residency decision — and on Google, the org policy from module 03 can restrict it.
- **Encryption at rest is on by default** on all three: Google encrypts all customer data at rest automatically; S3 applies SSE-S3 to every new object (since January 5, 2023); Azure Storage encrypts all data. Customer-managed keys are module 16.

### Storage classes and lifecycle rules

**Plain version:** you pay less per GB for data you rarely touch — but more to read it, and a penalty if you delete it too soon.

| | Google Cloud Storage | Amazon S3 | Azure Blob |
|---|---|---|---|
| Hot | **Standard** (no minimum) | **S3 Standard** (no minimum) | **Hot** (no minimum; default for new accounts) |
| Infrequent | **Nearline** — 30-day minimum | **Standard-IA** / One Zone-IA — 30 days | **Cool** — 30 days |
| Cold | **Coldline** — 90 days | **Glacier Instant Retrieval** — 90 days | **Cold** — 90 days |
| Archive | **Archive** — 365 days, still millisecond access | **Glacier Flexible Retrieval** (90 days) / **Glacier Deep Archive** (180 days) — restore takes minutes to hours | **Archive** — 180 days, **offline**: rehydration takes up to 15 hours |
| Automatic tiering | **Autoclass** | **S3 Intelligent-Tiering** | Lifecycle rules; Microsoft also documents a newer "smart tier" option ⚠️ not explored this run |

**The real difference:** Google's Archive class is still online — reads come back in milliseconds, just with retrieval fees. S3's Glacier Flexible/Deep Archive and Azure Archive are offline: you request a restore and wait. That matters for an agency that says "we need seven-year retention, and investigators must pull records same-day."

**Minimum storage duration** means if you delete (or move) an object early, you're billed as if it stayed the minimum. A 1 GB file put in Coldline and deleted after 10 days is billed for 90.

**Lifecycle rules** automate the boring part: "move to Nearline after 30 days, delete after 365," or "delete noncurrent versions after 7 days." Google calls this **Object Lifecycle Management**; AWS **S3 Lifecycle**; Azure **lifecycle management policies**.

**Bridge:** it's records management. Your old shop's retention schedule — active files, then the records center, then destruction after N years — expressed as JSON.

### Making deletion recoverable: versioning and soft delete

Two different safety nets:

- **Object versioning** keeps the old copy when an object is overwritten or deleted. The current copy is **live**; older ones are **noncurrent**. Google **Object Versioning**, **S3 Versioning**, **Azure blob versioning**. Off by default on all three; every version is billed.
- **Soft delete** keeps deleted things for a window so you can restore them. On Google, **soft delete is on by default** for buckets that support it — **7 days**, configurable 7–90 days or off — and soft-deleted bytes are billed until they expire. Azure has **blob soft delete** and **container soft delete** (1–365 days, set per account). S3 has no separate soft-delete feature; versioning plus delete markers fills that role.

How they combine on Google: with both on, deleting a live object makes it noncurrent; deleting a noncurrent version makes it soft-deleted; soft-deleted objects vanish when the window ends.

**What these protect against:** fat fingers and buggy scripts. They do **not** stop an attacker with admin rights, who can delete versions, shorten soft delete, or turn versioning off. For that you need a lock.

### Making deletion impossible: retention and WORM

**WORM** = write once, read many. The data can be read but not changed or deleted until a date.

| | Google Cloud Storage | Amazon S3 | Azure Blob |
|---|---|---|---|
| Bucket-wide minimum age | **Retention policy** (up to 100 years) | Object Lock default retention | **Time-based retention policy** (1 day to ~400 years), container- or version-level |
| Per-object retention | **Object Retention Lock** (enable at bucket creation with `--enable-per-object-retention`) | **Object Lock** retain-until date per version | Version-level immutability |
| "Even admins can't undo it" | **Bucket Lock** — locking a retention policy is irreversible; the period can be lengthened, never shortened or removed | **Compliance mode** — no user, including root, can delete before the date | **Locked** policy — can only be extended (container-level: at most 5 times) |
| Testing mode | Unlocked policy (removable) | **Governance mode** — users with `s3:BypassGovernanceRetention` can override | **Unlocked** policy (Microsoft says lock within ~24 hours; unlocked is for testing) |
| Indefinite hold | Event-based and temporary holds | **Legal hold** | **Legal hold** (tagged) |
| Prerequisite | — | **Versioning must be on** | Version-level WORM needs versioning |

**Why this is a big deal:** a locked retention policy is the cloud answer to ransomware and insider destruction — and to records law. Microsoft cites a third-party assessment of its immutable storage against SEC 17a-4(f), FINRA 4511, and CFTC 1.31.

**Why it's dangerous in a lab:** a locked policy can't be removed, and a bucket with locked data can't be deleted until every object ages out. In S3, compliance-mode objects can't be deleted early even by root — AWS's docs say closing the account is the only way. **Never lock a retention policy in your personal lab.** The lab uses an unlocked 60-second policy.

### Who can read it: identity first, then the "public" switch

Object storage access is decided by two things:

1. **Identity-based permissions** — IAM on the bucket or project (Google), IAM policies plus **bucket policies** (AWS), Azure RBAC data roles such as **Storage Blob Data Reader** (Azure).
2. **Legacy per-object permissions and anonymous access** — **ACLs** (Google, AWS) or container **anonymous access levels** (Azure). This is where accidental exposure usually comes from.

Each cloud now has a "turn off the legacy mess, and block public" control:

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Turn off per-object ACLs | **Uniform bucket-level access (UBLA)** — IAM only. Can be reverted only within 90 days | **Object Ownership: bucket owner enforced** (ACLs disabled) | No object ACLs; access via RBAC, keys, or SAS |
| Block public access | **Public access prevention (PAP)** — `allUsers` / `allAuthenticatedUsers` grants fail; existing ones are overridden | **S3 Block Public Access** — four settings, at account and bucket level | Storage account **`AllowBlobPublicAccess = false`** overrides every container's setting |
| Default for new buckets | UBLA: enforced by a default org policy on organizations created on or after May 3, 2024 (some created Feb–Apr 2024 too) — check yours under **IAM & Admin → Organization Policies**; PAP: set per bucket or by the `storage.publicAccessPrevention` org policy | Block Public Access **on** and ACLs **off** for all new buckets since April 2023 | Anonymous access never permitted unless explicitly enabled |
| Org-wide guardrail | Org policies `storage.uniformBucketLevelAccess`, `storage.publicAccessPrevention` | Account-level Block Public Access; SCPs/RCPs | Azure Policy |

**Azure-specific trap: keys and SAS tokens.** A storage account has two **account keys** that grant full access, and anyone holding a key can mint **shared access signatures (SAS)** — URLs with a token embedded. A SAS is a bearer credential: whoever has the URL has the access. Microsoft recommends one hour or less for SAS lifetimes, and you can disable shared-key access entirely to force Entra ID authorization.

**Google's equivalent bearer URL** is a **signed URL**; AWS has **presigned URLs**. All three are fine when short-lived and narrowly scoped, and dangerous when pasted into a repo.

**Bridge to your intel background:** UBLA + PAP is the difference between controlling access at the compartment level (one roster, centrally managed) and at the individual-document level (every page with its own dissemination markings — someone eventually gets one wrong). PAP is the rule "nothing in this compartment may ever be marked for public release," enforced by the system rather than by reviewers.

> **Shared responsibility:** the provider encrypts the disks, replicates the data, and builds the guardrails. **Who can read, write, and delete; whether a bucket can go public; whether versioning, soft delete, and retention are on; and how keys and SAS tokens are handled — always the customer's.** No provider will stop you from granting `allUsers` if you've turned the guardrail off.

---

## Text diagram — a protected bucket

```
 Uploader SA ── IAM: objectCreator ──┐
 Analyst group ─ IAM: objectViewer ──┤      ┌──────────── bucket: agency-records (us-central1) ───────────┐
 allUsers ───── (grant attempt) ──✗ 412     │ UBLA on (no ACLs)      PAP enforced (no public)            │
                                    └─────► │ Versioning on ── overwrite/delete → noncurrent version     │
                                            │ Soft delete 7 d ── deleted version → restorable 7 days      │
                                            │ Retention policy 7 y (LOCKED) ── no delete until age ≥ 7 y │
                                            │ Lifecycle: Standard → Coldline at 90 d → Archive at 1 y     │
                                            └──────────────┬───────────────────────────────────────────────┘
                                                           ▼
                Cloud Audit Logs: Admin Activity (always on) · Data Access (OFF until you enable it)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Object storage | Cloud Storage (buckets) | S3 (buckets) | Blob Storage (storage account → containers) | Azure adds the storage-account layer, which carries keys and network settings |
| Block storage | Persistent Disk, Hyperdisk, Local SSD | EBS | Managed Disks | Module 05 |
| Managed file storage | Filestore | EFS, FSx | Azure Files | Azure Files speaks SMB natively — the Windows file-share migration path |
| Coldest class | Archive (online, ms access, 365-day min) | Glacier Deep Archive (offline restore, 180-day min) | Archive (offline, up to 15 h rehydrate, 180-day min) | Google's archive is still online |
| Auto-tiering | Autoclass | Intelligent-Tiering | Lifecycle rules (+ smart tier ⚠️) | |
| Recover deletes | Soft delete **on by default** (7 d) + Object Versioning | Versioning (+ delete markers) | Blob/container soft delete + versioning | Only Google turns soft delete on for you |
| WORM | Retention policy + Bucket Lock; Object Retention Lock | Object Lock (governance / compliance) + legal hold | Immutable storage (unlocked/locked) + legal hold | S3 requires versioning; lock is irreversible on all three |
| Block public | UBLA + public access prevention | Block Public Access (default on) + ACLs disabled | `AllowBlobPublicAccess=false` | All three now default toward private |
| Bearer URLs | Signed URLs | Presigned URLs | SAS tokens (account keys can mint them) | Azure account keys are the biggest standing secret |
| Free allowance | 5 GB-month regional Standard in us-central1/us-east1/us-west1, 5k Class A + 50k Class B ops, 100 GB egress | Covered by free-plan credits ⚠️ specific S3 allowance not verified this run | 12 months: 5 GB Hot LRS block blob, 20k reads, 10k writes | |

## Administer and monitor it

- **Inventory:** `gcloud storage buckets list`; `aws s3api list-buckets`; `az storage account list`. Label/tag `lab=08`.
- **Config audit:** on Google, check every bucket for UBLA, PAP, versioning, soft delete, retention (`gcloud storage buckets describe`). AWS: `get-public-access-block`, `get-bucket-versioning`. Azure: `allowBlobPublicAccess`, `allowSharedKeyAccess`, data-protection settings.
- **Logs — the gap that bites:**
  - Google: bucket config changes are **Admin Activity** logs (always on). **Object reads and writes are Data Access logs, off by default** — and access through public (`allUsers`) grants isn't recorded in audit logs at all; Google points to usage logs for that.
  - AWS: bucket config is a CloudTrail **management event**; object-level reads/writes are **data events**, not logged by default and always billed when enabled. S3 server access logs are an alternative.
  - Azure: management operations hit the **Activity Log**; data operations need **diagnostic settings** for Storage resource logs (module 18).
- **Cost:** watch storage by class, operations, early-deletion charges, soft-deleted bytes, noncurrent versions, and egress.

## Security angle

Most common storage failures:

1. **Public bucket or container** — an `allUsers` grant, a public ACL, or anonymous container access. Fix: UBLA + PAP / Block Public Access / `AllowBlobPublicAccess=false`, enforced by org policy.
2. **Leaked bearer credentials** — long-lived SAS tokens, account keys, access keys, or signed URLs in code repos or logs.
3. **Over-broad identity grants** — `storage.admin` on the project for an app that only reads one bucket.
4. **No recovery path** — versioning off, soft delete disabled, no locked retention for critical records. Ransomware or a malicious insider then has the final say.
5. **No data-access logging** — you can't answer "what was taken?" during the incident.
6. **Wrong location** — data in a region outside the residency boundary.

## Threat intel angle

- **T1530 Data from Cloud Storage** — collecting data from object storage, often via misconfigured permissions or leaked credentials. MITRE lists ShinyHunters collecting from insecure buckets and Storm-0501 changing Azure Storage settings to expose accounts for exfiltration. Pacu and Peirates automate S3 enumeration and download.
- **T1619 Cloud Storage Object Discovery** — listing buckets and objects to find what's worth taking.
- **T1485 / T1486 Data Destruction / Data Encrypted for Impact** — in January 2025 AWS's incident response team reported attackers using stolen long-term access keys to rewrite S3 objects encrypted with keys only the attacker held (SSE-C). AWS's guidance: short-term credentials, versioning or backups, monitoring — and S3 has since begun disabling SSE-C by default on new buckets (announced November 2025, rolling out from April 2026; also applies to existing buckets in accounts with no SSE-C data).

**Recurring patterns from public reporting:**

- **Misconfiguration at scale.** The U.S. Justice Department's case against the Capital One intruder (convicted June 2022) described a tool that scanned AWS for misconfigured accounts, then used them to download data from more than 30 organizations and mine cryptocurrency.
- **Over-permissive bearer tokens.** In 2023 Microsoft disclosed that an employee published a storage URL with an overly permissive SAS token in a public GitHub repo, exposing internal data including workstation backups; Microsoft found no customer data affected and tightened its secret scanning.
- **Tradecraft is commoditized.** Microsoft's October 2025 threat write-up on Azure Blob Storage describes name-guessing tools, public indexes of exposed containers, use of native tools such as AzCopy to blend in, and attackers disabling soft delete and immutability before destructive actions.

**Bridge to your CTI work:** the analytic question is always "misconfiguration or credential?" A public bucket leaves no identity in the logs (and on Google may leave no audit record at all); a stolen key leaves a principal, a source IP, and a burst of `GetObject`/`CopyObject` calls. Collection requirements follow: enable data-access logging on high-value buckets *before* the incident.

## Public sector notes

- **Records retention** is a natural fit for locked retention policies — agency records schedules map directly to retention periods. Get the period right before locking; it can't be shortened.
- **Data residency:** pick region and storage class within the authorized boundary. Multi-regions span several regions — confirm they're all inside it (modules 26–27).
- **Cold-storage retrieval time** is a mission question: offline archive tiers can take hours. Google's online Archive class is a genuine differentiator for "rarely accessed but must be fast when needed."
- **Exfiltration boundaries:** a perfectly private bucket can still be copied out by an insider with valid credentials. Module 11 covers VPC Service Controls, Google's answer to that.

## Key takeaways

- Block = a disk, file = a shared drive, object = API-accessed files at massive scale. Object storage is where most data — and most exposure — lives.
- Colder classes cost less to keep and more to read, with minimum-duration charges. Google's Archive stays online; AWS and Azure archive tiers are offline.
- Versioning and soft delete protect against mistakes; only a **locked** retention policy protects against an admin-level attacker. Never lock one in a lab.
- Turn off legacy ACLs and block public access: UBLA + PAP on Google, Block Public Access on AWS, `AllowBlobPublicAccess=false` on Azure — enforced org-wide.
- Object-level access logs are off by default on Google and AWS. Turn them on for buckets that matter.
- Access, public exposure, data protection settings, and credential handling are **always the customer's**.

## Sources

- [Google Cloud — Storage classes](https://docs.cloud.google.com/storage/docs/storage-classes)
- [Google Cloud — Object Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle) and [Autoclass](https://docs.cloud.google.com/storage/docs/autoclass)
- [Google Cloud — Soft delete overview](https://docs.cloud.google.com/storage/docs/soft-delete)
- [Google Cloud — Bucket Lock (retention policies)](https://docs.cloud.google.com/storage/docs/bucket-lock) and [Use and lock retention policies](https://docs.cloud.google.com/storage/docs/using-bucket-lock)
- [Google Cloud — Uniform bucket-level access](https://docs.cloud.google.com/storage/docs/uniform-bucket-level-access)
- [Google Cloud — Public access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention)
- [Google Cloud Blog — Introducing stronger default Org Policies (Mar 2024)](https://cloud.google.com/blog/products/identity-security/introducing-stronger-default-org-policies-for-our-customers) and [Manage security baseline constraints](https://docs.cloud.google.com/resource-manager/docs/manage-baseline-constraints)
- [Google Cloud — Cloud Audit Logs with Cloud Storage](https://docs.cloud.google.com/storage/docs/audit-logging)
- [Google Cloud — Default encryption at rest](https://docs.cloud.google.com/docs/security/encryption/default-encryption)
- [Google Cloud — Choose a disk type](https://docs.cloud.google.com/compute/docs/disks) and [Filestore overview](https://docs.cloud.google.com/filestore/docs/overview)
- [Google Cloud — Free cloud features](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [AWS — S3 storage classes](https://aws.amazon.com/s3/storage-classes/)
- [AWS — Locking objects with Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [AWS — S3 applies Block Public Access and disables ACLs on new buckets by default (Apr 2023)](https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/)
- [AWS — S3 automatically encrypts all new objects (Jan 2023)](https://aws.amazon.com/about-aws/whats-new/2023/01/amazon-s3-automatically-encrypts-new-objects/)
- [AWS — Logging data events with CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html)
- [AWS Security Blog — Preventing unintended encryption of Amazon S3 objects (Jan 2025)](https://aws.amazon.com/blogs/security/preventing-unintended-encryption-of-amazon-s3-objects/)
- [AWS — S3 new default bucket security setting: SSE-C disabled (Apr 2026)](https://aws.amazon.com/about-aws/whats-new/2026/04/s3-default-bucket-security-setting/) and [advance notice (Nov 2025)](https://aws.amazon.com/blogs/storage/advanced-notice-amazon-s3-to-disable-the-use-of-sse-c-encryption-by-default-for-all-new-buckets-and-select-existing-buckets-in-april-2026/)
- [Microsoft — Access tiers for blob data](https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-overview)
- [Microsoft — Overview of remediating anonymous read access](https://learn.microsoft.com/en-us/azure/storage/blobs/anonymous-read-access-overview)
- [Microsoft — Immutable storage for blob data](https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview)
- [Microsoft — `az storage account blob-service-properties`](https://learn.microsoft.com/en-us/cli/azure/storage/account/blob-service-properties?view=azure-cli-latest)
- [Microsoft — Explore free Azure services](https://azure.microsoft.com/en-gb/pricing/free-services)
- [Microsoft MSRC — Exposure due to overly permissive SAS token (Sep 2023)](https://www.microsoft.com/en-us/msrc/blog/2023/09/microsoft-mitigated-exposure-of-internal-information-in-a-storage-account-due-to-overly-permissive-sas-token)
- [Microsoft Security Blog — Threat activity targeting Azure Blob Storage (Oct 2025)](https://www.microsoft.com/en-us/security/blog/2025/10/20/inside-the-attack-chain-threat-activity-targeting-azure-blob-storage/)
- [U.S. DOJ — Former Seattle tech worker convicted (Jun 2022)](https://www.justice.gov/usao-wdwa/pr/former-seattle-tech-worker-convicted-wire-fraud-and-computer-intrusions)
- [MITRE ATT&CK — T1530](https://attack.mitre.org/techniques/T1530/), [T1619](https://attack.mitre.org/techniques/T1619/)

Verified: 2026-10-25
