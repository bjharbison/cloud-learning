# 16 — Encryption and key management: KMS, customer-managed keys, HSMs, secrets managers

> **In one sentence:** you'll be able to explain what the clouds encrypt for you by default, how envelope encryption works, the ladder of key-control options from provider-managed to externally held keys, and how secrets managers replace passwords in code — and to answer the agency question "who can decrypt our data?" precisely.

**Prereqs:** modules 00–15 (module 08 for buckets; module 14 for IAM; module 05 for Confidential VMs) · **Time:** ~3.5 hours incl. lab · **Phase:** 4

## Learning objectives

- Explain **encryption at rest** and **in transit** defaults on all three clouds, and what they do and don't protect against.
- Describe **envelope encryption** (DEKs and KEKs) in plain language.
- Compare the key-control ladder: **provider-managed → customer-managed (CMEK) → customer-supplied (CSEK/SSE-C) → externally held (EKM/XKS)**, plus **HSM-backed** keys.
- Explain **Key Access Justifications** and why agencies insist on controlling keys.
- Use **secrets managers** instead of plaintext credentials.
- Map key and secret abuse to **ATT&CK** and public reporting.

## Why this matters for the target roles

- **Customer engineer / architect:** "Who holds the keys?" is one of the first questions any regulated customer asks. You need to answer it at the right level — default, CMEK, HSM, or external — and know what each costs in money and operational risk.
- **Cloud security:** keys and secrets are where encryption actually becomes access control. A bad key policy undoes good encryption.
- **CTI:** attackers rarely break encryption. They steal credentials, read secrets, or — in one 2025 campaign — used the customer's own encryption feature as ransomware.

---

## Concepts

### What's encrypted already (and why that isn't the whole answer)

All three providers **encrypt customer data at rest by default** and you can't turn it off:

- **Google Cloud** encrypts everything it stores with **AES-256** at the storage layer (a few very old disks used AES-128).
- **AWS** applies **SSE-S3** (AES-256) to every new S3 object since January 5, 2023. **EBS** encryption-by-default is still a **per-Region opt-in** — turn it on in every Region you use.
- **Azure** Storage and managed disks are always encrypted with 256-bit AES and **Microsoft-managed keys**.

**In transit:**

- Google: user traffic uses **TLS** to the **Google Front End**; Google's service-to-service traffic uses **ALTS** (Application Layer Transport Security). VM-to-VM traffic on internal IPs inside a VPC (or peered VPCs) is encrypted at the network layer. **Traffic to external IPs isn't automatically encrypted — that's your TLS.**
- Azure: **MACsec** (link-layer encryption, module 13) on Microsoft backbone traffic within and between regions, plus TLS 1.2+ on service endpoints.
- AWS: TLS on all service APIs ⚠️ (AWS's network-layer encryption details weren't re-verified this run).

**What default encryption protects against:** stolen disks, a decommissioned drive, someone reading raw storage media. **What it doesn't:** anyone with valid IAM access. If your service account can read the bucket, the platform decrypts for it automatically. Encryption at rest is a physical-security control; **IAM is still the access control** (module 14).

**Bridge:** default encryption is like a SCIF's locked safes — they matter if someone carries a drawer out the door. They don't stop a cleared person who is allowed in from reading what's inside.

### Envelope encryption, plainly

Encrypting petabytes with one key held in a vault would mean sending all your data to the vault. Instead:

1. A **data encryption key (DEK)** — a fresh random key — encrypts the data, right next to the data.
2. A **key encryption key (KEK)** encrypts ("wraps") the DEK.
3. The **wrapped DEK** is stored alongside the ciphertext. The plaintext DEK is thrown away.
4. To read, you send the small wrapped DEK to the key service, get the DEK back (if IAM allows), and decrypt locally.

Google's default encryption does this per data chunk, with KEKs held in an internal keystore protected by a chain of root keys. **The KEK never leaves the key service.** That's what makes the next part work: whoever controls the KEK controls every DEK under it.

**Bridge:** it's the two-envelope courier procedure. The document goes in an inner envelope (DEK); the inner envelope's combination is sealed in an outer one (KEK) that only the key custodian can open. Revoke the custodian's cooperation, and every inner envelope stays shut.

### The key-control ladder

| Rung | Who generates / holds the KEK | Google Cloud | AWS | Azure |
|---|---|---|---|---|
| **Provider-managed** (default) | Provider, invisible to you | Google default encryption | **AWS owned keys**; legacy **AWS managed keys** (`aws/s3`, `aws/ebs`) | Microsoft-managed keys |
| **Customer-managed (CMEK)** | You create it in the provider's KMS; you control IAM, rotation, disable, destroy | **Cloud KMS** key set on the resource | **Customer managed key** in AWS KMS | **Customer-managed key** in **Key Vault** or **Managed HSM** |
| **HSM-backed** | Same, but key material lives in a validated hardware module | Cloud KMS `HSM` protection level; **Single-tenant Cloud HSM** (GA Dec 2025) | KMS keys are HSM-protected by default; **AWS CloudHSM** (single-tenant) | Key Vault **Premium**; **Managed HSM**; **Azure Cloud HSM** |
| **Customer-supplied** | You send the raw key with each request; provider keeps only a hash | **CSEK** (Cloud Storage objects, Compute Engine disks) | **SSE-C** (S3) — now **blocked by default** on new buckets (April 2026) | Customer-provided keys (Blob Storage requests) |
| **Externally held** | Key stays in a key manager **outside** the cloud; provider calls it each time | **Cloud External Key Manager (EKM)** — partners Fortanix, Futurex, Thales | KMS **external key store (XKS)** | Managed HSM external key management ⚠️ preview |

Notes that matter in a customer conversation:

- **AWS managed keys are legacy.** AWS hasn't created new ones for new services since 2021; new services use AWS owned keys. If a customer needs to see and control the key, it's a **customer managed key**.
- **CMEK is the common answer.** It gives the customer a kill switch (disable or destroy the key) and an audit trail of every use, without running hardware.
- **CSEK/SSE-C is fragile:** lose your copy of the key and the data is gone; Google's console can't even upload or download CSEK objects. It also became an attack tool (see Threat intel).
- **External keys** give the strongest "the provider can't decrypt without us" story — and make **your** key manager's availability part of the cloud's availability. AWS states plainly that external and CloudHSM key stores carry no AWS SLA because availability is yours.

**FIPS validation** (the federal question): Google software keys are FIPS 140-3 Level 1, Cloud HSM keys FIPS 140-2 Level 3; AWS KMS HSMs are FIPS 140-3 Level 3; Azure Key Vault Premium (current HSM platform), Managed HSM, and Cloud HSM are FIPS 140-3 Level 3, Standard (software) is 140-2 Level 1. NIST moved FIPS 140-2 certificates to the **Historical List** in September 2026 — existing systems may keep using them, but new procurements increasingly ask for 140-3. Ask which certificate a given control relies on.

### Cloud KMS in particular

- **Hierarchy:** **key ring** (a location-bound folder) → **key** (purpose, protection level, rotation schedule) → **key versions** (the actual key material). One version is **primary** for new encryption; older versions still decrypt what they encrypted.
- **Protection levels:** `SOFTWARE`, `HSM`, `HSM_SINGLE_TENANT`, `EXTERNAL`, `EXTERNAL_VPC`. Fixed at creation.
- **Location matters:** a CMEK key must be in the same location as the resource it protects (e.g., a `us-central1` bucket needs a `us-central1` key ring). That doubles as a **data-residency** control.
- **Rotation** creates a new primary version; it does **not** re-encrypt existing data.
- **Disable vs destroy:** disable is reversible; destroy is **scheduled** (default 30 days, configurable 24 hours to 120 days) and then permanent. Data under a destroyed version is unrecoverable — **crypto-shredding**.
- **Deletion:** Google now lets you delete destroyed key versions and then empty keys (GA March 2, 2026), and empty key rings (GA August 24, 2026); before that, key rings and keys lived forever. Check `gcloud kms keyrings delete --help` — older SDKs lack it.
- **Autokey** creates key rings, keys, and the service-agent grants automatically when a resource needs CMEK — the fix for "CMEK is too much toil." Autokey keys get a free tier (100 active key versions and 10,000 operations per month per billing account).
- **Who needs permission:** for CMEK, the **service agent** of the consuming service (e.g., the Cloud Storage service agent `service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com`) needs `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key. That grant *is* the switch: remove it or disable the version and the service can no longer read.

**Costs (small, but they surprise people):** about **$0.06/month per active software key version**, ~$1.00 for HSM (symmetric), ~$3.00 for external; **$0.03 per 10,000** operations. Enabled, disabled, **and scheduled-for-destruction** versions all bill; only destroyed versions are free. AWS: **$1/month per customer managed key** (each of the first two rotations adds $1/month), 20,000 free requests/month, and **keys pending deletion aren't billed**. Azure Key Vault Standard bills per operation with no monthly fee for software keys ⚠️ (current dollar figures not confirmed).

### Key Access Justifications: "why is Google touching my key?"

**Key Access Justifications (KAJ)** attaches a **reason code** to every request to use a key (e.g., customer-initiated access, Google-initiated support, system maintenance). Your policy — enforced in Cloud KMS or, with EKM, at your external key manager — can **deny** requests whose reason you don't accept. KAJ is available **only with Assured Workloads** control packages (module 27), and what you get depends on the package: justification logging only, approve/deny by reason, or partner-side enforcement.

Paired with **Access Transparency** logs (module 18), this is how an agency moves from "trust us" to "show us, and let us say no."

### Why agencies insist on controlling keys

1. **Revocation as a last resort.** If a contract ends, a legal dispute arises, or compromise is suspected, disabling the key renders data unreadable everywhere at once.
2. **Separation of duties.** A key custodian (security office) is separate from the data owner and from the cloud provider — a structure NIST SP 800-57 (key management guidance; Rev. 5 final, Rev. 6 in draft) has long recommended.
3. **Sovereignty and compelled access.** External keys mean the provider can't produce plaintext alone.
4. **Audit.** Every decrypt is a logged event with a principal — evidence for an ATO package.
5. **Compliance packages** (FedRAMP High, DoD IL5, CJIS) frequently specify customer-managed keys and FIPS-validated modules. Exact requirements belong to module 26.

**The trade-off to say out loud:** every rung up the ladder adds cost, operational burden, and a new way to lose your own data. Recommend the lowest rung that meets the requirement.

### Secrets managers

A **secret** is a credential your code needs: database password, API key, TLS private key. Hard-coding it in source, environment variables, or container images is how it leaks (module 07 warned you).

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Service | **Secret Manager** | **AWS Secrets Manager** (also SSM Parameter Store SecureString) | **Azure Key Vault** (secrets, keys, and certificates in one vault) |
| Model | Secret → immutable **versions**; IAM per secret | Secret with versions/staging labels; resource policy + IAM | Vault-level; **Azure RBAC is now the default** for new vaults (API version 2026-02-01) |
| Rotation | **Notifications only** — Pub/Sub on a schedule; your code rotates | **Built-in rotation** via Lambda (managed rotation for some services) | Rotation policies for keys; secret rotation via Event Grid + your code |
| Deletion safety | Destroy versions | Recovery window (7–30 days) or force delete | **Soft delete** (mandatory, 7–90 days, default 90) + optional **purge protection** (irreversible once on) |
| Cost | 6 active versions + 10,000 accesses/month free; then ~$0.06/version/location/month | $0.40/secret/month + $0.05 per 10,000 calls | Per-operation ⚠️ |

**The better pattern:** where you can, don't have a secret at all. Use the workload's own identity (service account, IAM role, managed identity — modules 14–15) to get short-lived tokens. Secrets managers are for the credentials you can't eliminate.

**Homelab bridge:** if you've used Docker secrets, Ansible Vault, or a `.env` file with `chmod 600`, Secret Manager is the networked, IAM-controlled, audited version — with every read logged (once you turn on Data Access logs, module 18).

> **Shared responsibility — say it plainly:** the provider runs the KMS, HSMs, and default encryption. **Who can use or administer keys (IAM), whether you use CMEK or external keys, rotation, destroy schedules, which secrets exist and who reads them, client-side TLS to external IPs, and keeping your own copy of any customer-supplied key are always the customer's.**

---

## Text diagram — CMEK on a bucket

```
 You (key admin)          Cloud KMS: key ring lab16-kr (us-central1)
   │ create/rotate/disable    └─ key lab16-key ── v1 (primary, ENABLED) ── v2 ...
   ▼                                 ▲  wrap / unwrap DEK
 IAM on the key:                     │  (only the KEK lives here)
   gs-project-accounts SA ──── cryptoKeyEncrypterDecrypter
                                     │
 Cloud Storage bucket (us-central1) ─┘
   object = AES-256 ciphertext  +  wrapped DEK  +  kmsKeyName=.../cryptoKeyVersions/1
                                     │
  Disable v1 ──► reads of objects under v1 FAIL (list/delete still work)
  Destroy v1 ──► after scheduled period, data is unrecoverable (crypto-shred)

 Every Encrypt/Decrypt ─► Cloud Audit Logs (Data Access — turn it on, module 18)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Default at rest | AES-256, always on | SSE-S3 always on; **EBS default is per-Region opt-in** | AES-256, always on | AWS EBS is the one to check |
| Managed key service | **Cloud KMS** | **AWS KMS** | **Azure Key Vault** (Standard/Premium); **Managed HSM** | Key Vault also stores secrets and certificates |
| Key structure | Key ring → key → versions | KMS key (with key material, rotations) + aliases | Vault → key → versions | |
| Single-tenant HSM | Single-tenant Cloud HSM (quorum approval) | AWS CloudHSM (hsm2m.medium, FIPS 140-3 L3) | Managed HSM; Azure Cloud HSM (Dedicated HSM retiring 2028) | |
| External key | Cloud EKM (internet or VPC) | XKS external key store | Managed HSM external key ⚠️ preview | Your HSM's uptime becomes the cloud's |
| Access justification | **Key Access Justifications** (Assured Workloads) | — ⚠️ no direct equivalent found | — ⚠️ (Customer Lockbox covers support access, module 18) | Google-specific capability |
| Key deletion | Destroy (24 h–120 d schedule), then delete | Schedule deletion 7–30 d (not billed while pending) | Soft delete 7–90 d; purge protection | |
| Secrets | Secret Manager | Secrets Manager | Key Vault secrets | Only AWS rotates natively |
| Automated CMEK | **Autokey** | — | — | |

## Administer and monitor it

- **Inventory:** `gcloud kms keys list --keyring=... --location=...`; `aws kms list-keys` / `list-aliases`; `az keyvault list`. Know which resources use which key (`gcloud kms inventory` ⚠️ not checked this run; the console's key **Inventory** and **Key usage** views help).
- **Logs:** key creation, IAM changes, disable/destroy are **Admin Activity** / CloudTrail management / Activity Log events. **Encrypt/Decrypt** calls are **Data Access** logs on Google (off by default); in AWS, KMS crypto operations are CloudTrail **management events** and appear by default; Key Vault data-plane operations need **diagnostic settings** (module 18).
- **Alert on:** key version disable/destroy, schedule-key-deletion, key policy changes, new principals with encrypt/decrypt, secret access by a *human* (Google documents exactly this log-based alert, module 19).
- **Rotation:** set rotation schedules on CMEK keys; rotate secrets with your own automation.

## Security angle

1. **Over-broad key IAM** — granting `cloudkms.admin` and `cryptoKeyEncrypterDecrypter` to the same group defeats separation of duties.
2. **Secrets in code, env vars, images, or Terraform state** — still the most common leak.
3. **Destroying a key you still need** — crypto-shredding by accident. Use the scheduled-destroy window and alert on it.
4. **CMEK key in the wrong project or with no owner** — key projects should be dedicated and tightly held.
5. **SSE-C left enabled** on S3 buckets that don't need it (now blocked by default on new buckets).
6. **Key Vault without soft-delete awareness** — names stay reserved; purge protection is irreversible.
7. **Assuming CMEK stops an insider with data access** — it doesn't; IAM on the data does.

## Threat intel angle

| Technique | ATT&CK | Notes / public reporting |
|---|---|---|
| Reading secrets from a cloud secrets store | **T1555.006 Credentials from Password Stores: Cloud Secrets Management Stores** | ATT&CK's examples are exactly `get-secret-value`, `gcloud secrets` and Key Vault reads |
| Credentials in files, code, images | **T1552.001 Unsecured Credentials: Credentials In Files** | |
| Stealing tokens via the metadata service | **T1552.005 Cloud Instance Metadata API** | Module 05 |
| Ransomware using the victim's own encryption feature | **T1486 Data Encrypted for Impact** ⚠️ page not re-read this run | AWS Security Blog, Jan 15, 2025: actors with stolen credentials re-encrypted S3 objects with **SSE-C** via `CopyObject`, so only they held the key. AWS's mitigations: block SSE-C by bucket policy or RCP, short-term credentials, versioning, backups. (Third-party reporting named the campaign "Codefinger"; AWS didn't.) |
| Disabling or scheduling deletion of keys to destroy data | T1485 Data Destruction ⚠️ not re-checked | A KMS key is a single point of failure for every resource it protects |

**Detection ideas:** decrypts from a principal that never decrypted before; KMS `ScheduleKeyDeletion` / Cloud KMS `DestroyCryptoKeyVersion`; S3 `CopyObject` with SSE-C headers; bulk secret reads after a new access key appears.

**Bridge to your CTI work:** the SSE-C case is a living-off-the-land story — no malware, just the platform's own feature with stolen credentials. Same analytic habit as LOTL in OT: look for legitimate functions used by the wrong principal at the wrong time.

## Public sector notes

- Agencies routinely require **FIPS-validated** cryptography; check whether the control relies on a 140-2 (now Historical) or 140-3 certificate.
- **Key Access Justifications** and **external keys** are core to Google's sovereignty and Assured Workloads story (module 27); AWS GovCloud and Azure Government carry their own KMS/Key Vault instances.
- Google lists Secret Manager in FedRAMP Moderate/High and DoD IL2/IL4/IL5 scope; AWS lists KMS, CloudHSM, and Secrets Manager — and has relabeled FedRAMP levels as **"Class C (formerly Moderate)"** and **"Class D (formerly High)"** on its services-in-scope page. Treat that labeling as new and confirm it in module 26.

## Key takeaways

- Data at rest is encrypted by default everywhere (check EBS); in transit to external IPs is your TLS.
- **Envelope encryption:** DEK encrypts data; KEK in KMS wraps the DEK; control the KEK, control the data.
- The ladder: provider-managed → **CMEK** → HSM → customer-supplied → **external**. Recommend the lowest rung that meets the requirement.
- Disable is reversible; destroy is crypto-shredding. Both bill until destroyed on Google.
- **KAJ** + Access Transparency = "show us, and let us say no" (Assured Workloads).
- Prefer workload identity to secrets; put unavoidable secrets in a secrets manager.
- Key IAM, CMEK choices, rotation, and secrets are **always the customer's**.

## Sources

- [Google Cloud — Default encryption at rest](https://docs.cloud.google.com/docs/security/encryption/default-encryption), [Encryption in transit](https://docs.cloud.google.com/docs/security/encryption-in-transit)
- [Google Cloud — Cloud KMS overview](https://docs.cloud.google.com/kms/docs/key-management-service), [algorithms and protection levels](https://docs.cloud.google.com/kms/docs/algorithms), [key states](https://docs.cloud.google.com/kms/docs/key-states), [delete KMS resources](https://docs.cloud.google.com/kms/docs/delete-kms-resources), [release notes](https://docs.cloud.google.com/kms/docs/release-notes), [pricing](https://cloud.google.com/kms/pricing)
- [Google Cloud — CMEK for Cloud Storage](https://docs.cloud.google.com/storage/docs/encryption/customer-managed-keys), [using CMEK](https://docs.cloud.google.com/storage/docs/encryption/using-customer-managed-keys), [customer-supplied keys](https://docs.cloud.google.com/storage/docs/encryption/customer-supplied-keys)
- [Google Cloud — Cloud EKM](https://docs.cloud.google.com/kms/docs/ekm), [Key Access Justifications](https://docs.cloud.google.com/assured-workloads/key-access-justifications/docs/overview)
- [Google Cloud — Secret Manager overview](https://docs.cloud.google.com/secret-manager/docs/overview), [pricing](https://cloud.google.com/secret-manager/pricing), [rotation](https://docs.cloud.google.com/secret-manager/docs/rotation-recommendations), [compliance](https://docs.cloud.google.com/secret-manager/docs/compliance)
- [AWS — S3 default encryption FAQ](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-encryption-faq.html), [SSE-C default setting FAQ](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html), [EBS encryption by default](https://docs.aws.amazon.com/ebs/latest/userguide/encryption-by-default.html)
- [AWS — KMS concepts](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html), [key stores](https://docs.aws.amazon.com/kms/latest/developerguide/key-store-overview.html), [deleting keys](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys-scheduling-key-deletion.html), [data protection / FIPS](https://docs.aws.amazon.com/kms/latest/developerguide/data-protection.html), [pricing](https://aws.amazon.com/kms/pricing/), [CloudHSM FIPS validation](https://docs.aws.amazon.com/cloudhsm/latest/userguide/fips-validation.html), [Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/), [FedRAMP services in scope](https://aws.amazon.com/compliance/services-in-scope/FedRAMP/)
- [AWS Security Blog — Preventing unintended encryption of S3 objects (Jan 2025)](https://aws.amazon.com/blogs/security/preventing-unintended-encryption-of-amazon-s3-objects/)
- [Microsoft — Azure Storage encryption](https://learn.microsoft.com/en-us/azure/storage/common/storage-service-encryption), [encryption overview](https://learn.microsoft.com/en-us/azure/security/fundamentals/encryption-overview), [choose a key management solution](https://learn.microsoft.com/en-us/azure/security/fundamentals/key-management-choose), [Key Vault keys](https://learn.microsoft.com/en-us/azure/key-vault/keys/about-keys), [soft delete](https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview), [RBAC default](https://learn.microsoft.com/en-us/azure/key-vault/general/access-control-default), [Dedicated HSM](https://learn.microsoft.com/en-us/azure/dedicated-hsm/overview), [Double Key Encryption](https://learn.microsoft.com/en-us/purview/double-key-encryption)
- [NIST — Key management guidelines (SP 800-57)](https://csrc.nist.gov/projects/key-management/key-management-guidelines), [FIPS 140-3 transition](https://csrc.nist.gov/projects/fips-140-3-transition-effort)
- [MITRE ATT&CK — T1555.006](https://attack.mitre.org/techniques/T1555/006/), [T1552.001](https://attack.mitre.org/techniques/T1552/001/), [T1552.005](https://attack.mitre.org/techniques/T1552/005/), [T1486](https://attack.mitre.org/techniques/T1486/)

Verified: 2026-10-27
