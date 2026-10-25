# 08 Quiz — Storage

1. Match each to block, file, or object storage: Hyperdisk; Amazon EFS; Azure Blob Storage; Filestore; Amazon EBS; Cloud Storage.
<details><summary>Answer</summary>

Block: Hyperdisk, EBS. File: EFS, Filestore. Object: Azure Blob Storage, Cloud Storage. Block = a VM's disk; file = a shared NFS/SMB mount; object = files over an HTTPS API.
</details>

2. You put a 10 GB file in Google's Coldline class and delete it after 20 days. What are you billed for, and why?
<details><summary>Answer</summary>

Coldline has a 90-day minimum storage duration, so you're billed as if it was stored 90 days (20 actual + 70 early-deletion charge). Colder classes trade lower storage price for retrieval fees and minimums.
</details>

3. What's the practical difference between Google's Archive class and Azure's Archive tier?
<details><summary>Answer</summary>

Google Archive is online — reads return in milliseconds (with retrieval fees; 365-day minimum). Azure Archive is offline — a blob must be rehydrated first, which can take up to 15 hours (180-day minimum). S3 Glacier Flexible Retrieval and Deep Archive are also restore-then-read.
</details>

4. Versioning, soft delete, and a locked retention policy all "keep data." Which one protects against an attacker who holds full storage admin rights, and why?
<details><summary>Answer</summary>

Only the locked retention policy (Google Bucket Lock, S3 Object Lock compliance mode, Azure locked immutability policy). An admin can delete versions, disable versioning, or shorten/disable soft delete; a locked policy can't be removed or shortened by anyone until objects age out.
</details>

5. What does Google Cloud's soft delete do by default, and what does it cost?
<details><summary>Answer</summary>

It's on by default for buckets that support it, keeping deleted objects restorable for 7 days (configurable 7–90 days, or 0 to disable). Soft-deleted objects keep accruing storage charges until the window ends (plus early-deletion charges for non-Standard classes).
</details>

6. Name each cloud's main control to stop a bucket/container from being made public.
<details><summary>Answer</summary>

Google: public access prevention (with uniform bucket-level access to remove ACLs), enforceable via the `storage.publicAccessPrevention` org policy. AWS: S3 Block Public Access (on by default for new buckets since April 2023), plus ACLs disabled via Object Ownership. Azure: the storage account's `AllowBlobPublicAccess = false`, which overrides every container's setting.
</details>

7. Spot the misconfiguration: "Our Azure storage account blocks anonymous access, so it's safe. Our app uses a SAS URL with a two-year expiry that grants read/write/list on the whole account; it's in our config repo."
<details><summary>Answer</summary>

A SAS is a bearer credential — anyone with the URL has the access, regardless of anonymous-access settings. Two years and account-wide scope are far too broad (Microsoft recommends one hour or less), and it's stored in a repo. This is the pattern behind Microsoft's own 2023 exposure. Fix: short-lived, narrowly scoped user-delegation SAS (or Entra ID auth), keys out of code, consider disabling shared-key access.
</details>

8. An S3 bucket was enabled for Object Lock in compliance mode with a 10-year retention on each object. Can the account's root user delete an object next week?
<details><summary>Answer</summary>

No. In compliance mode no user, including root, can delete or overwrite a protected version or shorten its retention. (Governance mode would allow users with `s3:BypassGovernanceRetention` to override.) Object Lock also requires versioning.
</details>

9. Scenario: an agency must retain investigative case files for 7 years, unalterable, but investigators sometimes need a file the same day. Recommend a Google Cloud design.
<details><summary>Answer</summary>

A regional (or dual-region inside the authorized boundary) bucket with UBLA and PAP enforced; a retention policy of 7 years, tested unlocked and then locked with Bucket Lock; lifecycle rules moving objects to Coldline and then Archive — Archive stays online, so same-day retrieval works (with retrieval fees). Least-privilege IAM per group, Data Access audit logs on, and location restricted by org policy. Confirm the retention period with records officers before locking — it can't be shortened.
</details>

10. Which object-level reads are logged by default on Google Cloud and AWS?
<details><summary>Answer</summary>

None. Google Cloud Storage Data Access audit logs (object reads/writes) are off by default — and access via public `allUsers` grants isn't captured in audit logs at all. AWS CloudTrail data events for S3 are off by default and billed when enabled. Configuration changes are logged by default on both (Admin Activity / management events).
</details>

11. In the January 2025 S3 ransomware pattern AWS reported, how did attackers get in and what did they do?
<details><summary>Answer</summary>

They used valid, compromised long-term access keys, then rewrote objects with `CopyObject` using server-side encryption with customer-provided keys (SSE-C) that only they held. Mitigations: short-term credentials, versioning/backups/replication, monitoring (CloudTrail, GuardDuty S3 Protection), and blocking SSE-C where unneeded — which S3 now does by default on new buckets.
</details>

12. Why is "misconfiguration or stolen credential?" the first analytic question for a cloud storage leak, and what evidence distinguishes them?
<details><summary>Answer</summary>

They imply different root causes, scope, and remediation. A public bucket leaves anonymous access (on Google, possibly no audit record; you'd need usage/access logs) and an IAM/ACL change in admin logs. A stolen credential leaves a named principal, source IPs, and bursts of read/copy calls in data-access logs — and points to where the credential leaked.
</details>
