# 16 Interview Prep — Encryption and key management

## Likely questions

### Q1. "Who can decrypt our data in Google Cloud?"

**Answer outline:**
- By default: anyone you grant IAM access to the data, through the service — Google's default encryption is transparent to authorized principals.
- With CMEK: additionally, the service agent you authorize on your key; you can disable or destroy the key and every use is logged.
- With Cloud EKM: the key never leaves your external key manager; Google must call it for each operation.
- With Key Access Justifications (Assured Workloads): every key request carries a reason you can deny. Access Transparency shows Google staff access.
- Then ask: what threat are we addressing — insider, compelled access, contract exit, physical theft?

**Strong signal:** separating access control (IAM) from key control, and asking what threat drives the requirement.
**Avoid:** "It's encrypted, so nobody can read it."

### Q2. "Explain envelope encryption."

**Answer outline:**
- Data key encrypts data locally; key-encryption key in KMS wraps the data key; store wrapped key with the data.
- Benefits: performance (bulk data never goes to KMS), central control and audit of the KEK, cheap rotation.
- Revoke the KEK and every wrapped DEK becomes useless — crypto-shredding.

### Q3. "Should we use customer-managed keys for everything?"

**Answer outline:**
- Not automatically: CMEK adds cost, IAM to manage, and the risk of locking yourself out.
- Use it where policy, compliance, or a real threat requires it; Autokey reduces toil if you do.
- Go higher (HSM, external) only for specific requirements — FIPS level, sovereignty, separation from the provider.
- Pair with separation of duties, destroy schedules, and alerting on key state changes.

**Strong signal:** recommending the lowest rung that meets the requirement and naming the operational risks.

### Q4. "How would you get passwords out of our application code?"

**Answer outline:**
- First, eliminate secrets: workload identity (service accounts, IAM roles, managed identities, federation — module 15).
- For the rest: Secret Manager / Secrets Manager / Key Vault with per-secret IAM to one workload identity.
- Rotation (native on AWS; notification-driven on Google; event-driven on Azure), Data Access logging on secret reads, and secret scanning in repos.

### Q5. "What's an attack you've seen against cloud encryption or keys?"

**Answer outline:**
- Attackers rarely break crypto; they abuse access. Secrets-store reads (T1555.006), credentials in files (T1552.001).
- The 2025 S3 SSE-C ransomware: stolen credentials + a legitimate encryption feature (T1486). AWS's mitigations and the April 2026 default block.
- Detection: unusual decrypt principals, key deletion scheduling, SSE-C request headers.

## 60-second executive explanation

"Everything we store in the cloud is already encrypted — that protects us if a disk ever walks out of a data center. The real question is who holds the keys. By default, the provider manages them and our access controls decide who reads data. If our policy calls for it, we can hold the master keys ourselves, in a key service we control or even in hardware outside the cloud. That gives us a kill switch — turn off the key and the data is unreadable everywhere — and a log of every time a key is used. It also means if we lose the key, we lose the data, so we only take on that responsibility where the mission or compliance requires it. And for passwords our software needs, we keep them in a managed vault instead of in code."

## Whiteboard prompt

Draw the key-control ladder for an agency workload: a BigQuery dataset and a Cloud Storage bucket using CMEK from a dedicated key project (key admins ≠ data users), one high-sensitivity bucket using Cloud EKM with an on-prem partner HSM, Key Access Justifications policy denying Google-initiated access, and a Cloud Run service reading a database password from Secret Manager. Mark where every decrypt is logged and which alerts fire on key disable/destroy.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud encryption and key management — default encryption, envelope encryption, customer-managed and external keys, HSM options, Key Access Justifications, and secrets managers on Google Cloud, AWS, and Azure — and can discuss the trade-offs for regulated customers."
- **After completing the lab:** "In a personal lab I configured Google Cloud KMS keys, performed envelope encryption, protected a Cloud Storage bucket with a customer-managed key and verified that disabling the key blocked access, and stored application credentials in Secret Manager." Add the AWS data-key and Azure Key Vault sentences only if you did them.
- **Still requires (cert / production experience / clearance):** designing key hierarchies, HSM or external key manager deployments, or key ceremonies for a real organization; operating KMS under an ATO; Key Access Justifications in an Assured Workloads environment (needs an organization and the right package). Don't claim "implemented CMEK/EKM for an enterprise." Google Professional Cloud Security Engineer covers this area; if you handled cryptographic or key-management policy in prior roles, describe it only at the level you can discuss publicly.
