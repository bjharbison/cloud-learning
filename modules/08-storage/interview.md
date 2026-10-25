# 08 Interview Prep — Storage

## Likely questions

### Q1. "A customer is worried about accidentally exposing a bucket. How do you prevent it?"

**Answer outline:**
- Remove the legacy path: uniform bucket-level access (IAM only, no object ACLs).
- Block the outcome: public access prevention on every bucket, enforced org-wide with the `storage.publicAccessPrevention` org policy (plus `storage.uniformBucketLevelAccess`).
- Least-privilege IAM per bucket, granted to groups; short-lived signed URLs when outsiders need a file.
- Detect: Admin Activity logs for IAM changes on buckets; posture tooling for public findings (module 21).
- Same idea elsewhere: S3 Block Public Access at the account level; Azure `AllowBlobPublicAccess=false` via Azure Policy.

**Strong signal:** "prevent by policy at the org level, not by reviewing each bucket."
**Avoid:** "we'll just be careful."

### Q2. "How would you protect cloud data from ransomware?"

**Answer outline:**
- The attacker usually arrives with valid credentials — so start with identity: short-lived credentials, no long-term keys, MFA, least privilege (module 14).
- Recovery layers: versioning + soft delete for mistakes; a **locked** retention policy (Bucket Lock / Object Lock compliance / Azure locked immutability) for data that must survive an admin-level attacker.
- Copies in a separate project/account with separate admins.
- Detection: data-access logs, alerts on mass deletes/rewrites, on soft-delete or retention changes.
- Cite the January 2025 S3 SSE-C campaign as a real example.

**Strong signal:** knowing versioning alone isn't enough, and why.

### Q3. "Walk me through storage classes. How do you keep costs down?"

**Answer outline:**
- Standard → Nearline (30 d) → Coldline (90 d) → Archive (365 d); cheaper to keep, costlier to read, minimum-duration charges.
- Lifecycle rules for predictable patterns; Autoclass when access is unpredictable.
- Differentiator: Google Archive is online (millisecond reads); AWS Glacier Flexible/Deep Archive and Azure Archive require a restore.
- Watch the hidden costs: noncurrent versions, soft-deleted bytes, early deletion, egress.

### Q4. "Compare object storage on Google Cloud, AWS, and Azure."

**Answer outline:**
- Cloud Storage buckets / S3 buckets / Azure storage account → containers (the account carries keys and network settings).
- Public-access controls: PAP + UBLA / Block Public Access + ACLs disabled (defaults since 2023) / `AllowBlobPublicAccess`.
- WORM: Bucket Lock / Object Lock (needs versioning) / immutable storage.
- Soft delete on by default only on Google.
- Azure's distinctive risk: account keys and SAS tokens as bearer credentials.

### Q5. "An agency has records-retention requirements. How does that shape the design?"

**Answer outline:**
- Map the records schedule to retention periods; test unlocked, then lock — and confirm with records officers first, because it can't be shortened.
- Location inside the authorized boundary; org policy restricting locations.
- Retrieval-time requirements decide the coldest usable class.
- Data Access logging for chain-of-custody questions.

## 60-second executive explanation

"Cloud storage is where most of our data will live — documents, logs, backups. Three things keep it safe. First, we make it impossible to publish anything to the internet by accident: a setting enforced across the whole organization, so one person's mistake can't expose a dataset. Second, we keep deleted or changed files recoverable for a period, so a bad script or an error isn't a disaster. Third, for records we're legally required to keep, we put them under a lock that even our own administrators can't undo until the retention period ends — which also means ransomware can't destroy them. And we log who reads sensitive data, so if something goes wrong we can answer 'what was taken' with evidence, not guesses."

## Whiteboard prompt

Draw a bucket for an agency's case files: who writes (an ingest service account), who reads (an analyst group), and the settings on the bucket — UBLA, PAP, versioning, soft delete, a locked 7-year retention policy, and a lifecycle rule to Coldline then Archive. Add the org policies above it that enforce UBLA and PAP. Then draw two attack paths — a public grant attempt and a stolen service-account key — and mark which control or log addresses each.

## What you can honestly claim

- **After reading + quiz:** "I've studied object, block, and file storage across Google Cloud, AWS, and Azure, including storage classes, lifecycle management, versioning, retention locks, and public-access prevention controls, and how storage shows up in threat reporting."
- **After completing the lab:** "In a personal lab I configured Cloud Storage buckets with uniform bucket-level access and public access prevention, verified public grants were refused, recovered data using versioning and soft delete, demonstrated a retention policy blocking deletion, and enabled Data Access audit logs to record object reads." Add the S3 and Azure sentences only if you did those parts.
- **Still requires (cert / production experience / clearance):** designing and operating storage for production data, records-management programs, or backup/DR at scale; locking real retention policies; storage inside an authorized government boundary. Don't claim "data protection engineering experience." The Associate Cloud Engineer exam covers Cloud Storage administration and is a claimable milestone.
