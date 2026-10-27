# 18 Interview Prep — Logging and audit trails

## Likely questions

### Q1. "What gets logged by default in Google Cloud, and what doesn't?"

**Answer outline:**
- On and free: Admin Activity and System Event audit logs, 400 days in `_Required`, can't be disabled or deleted.
- On, stored 30 days in `_Default`: Policy Denied.
- Off: Data Access logs for most services (BigQuery is the exception, always on) — who read data, decrypted, accessed secrets.
- Not audit-logged: access via public `allUsers` grants.
- Then: what to enable first (IAM, IAP, KMS, Secret Manager, Resource Manager; then sensitive data stores) and the cost trade-off.

**Strong signal:** naming the specific gap and a prioritized enablement plan. **Avoid:** "everything is logged."

### Q2. "How would you design centralized logging for an agency with hundreds of projects?"

**Answer outline:**
- Org-level aggregated sink with `include-children` into a dedicated, separately administered logging project.
- Log bucket with Observability Analytics for SQL; locked retention to M-21-31 (12 months active, 18 cold via Cloud Storage with Bucket Lock).
- Pub/Sub sink to the SIEM (Google SecOps, Splunk, Sentinel).
- Data Access config set at org level so new projects inherit it.
- Alerts on sink/audit-config changes; least-privilege log viewing (Private Logs Viewer only where needed).
- AWS parallel: organization trail to a log archive account; Azure: diagnostic settings deployed by policy.

### Q3. "Walk me through investigating a suspected compromised service account."

**Answer outline:**
- Scope: all Admin Activity and Data Access entries where `principalEmail` = the SA or appears in `serviceAccountDelegationInfo`, across projects (aggregated sink).
- Look for: new keys (`CreateServiceAccountKey`, T1098.001), IAM changes, discovery bursts (`List*`, `AccessDenied`, T1580), data reads (T1530), cross-project copies (T1537), logging changes (T1685.002).
- Pivot on `callerIp` and user agent; compare with the SA's normal workload.
- Contain (disable keys/SA), preserve logs, extend retention for the case.

**Strong signal:** knowing that data reads are visible only if Data Access logs were on, and saying so up front.

### Q4. "How do AWS CloudTrail and Azure logging compare with Google's?"

**Answer outline:**
- AWS: management events on by default (Event history 90 days); trails for retention; data, network activity, and Insights events cost extra; integrity validation via signed digests; CloudTrail Lake closed to new customers since May 2026.
- Azure: Activity Log 90 days; resource logs need diagnostic settings; Entra sign-in/audit logs 7 or 30 days, export needs P1/P2; KQL in Log Analytics.
- All three: data-plane audit is opt-in.

### Q5. "What's an example where logging made the difference?"

**Answer outline:**
- Storm-0558 (2023): a federal agency caught it via MailItemsAccessed anomalies in premium M365 audit logs (CISA AA23-193A); Microsoft then expanded standard logging.
- Lesson: decide collection from the threat model; logging tiers are a security decision, not just a cost line.

## 60-second executive explanation

"In the cloud, most attacks don't leave malware behind — they leave log entries: who signed in, who changed permissions, who read which files. Every cloud records configuration changes for free, but records of who *read* our data are off until we turn them on, and they cost money in proportion to how busy the data is. Our plan is to turn on that detailed logging for the systems that hold our most sensitive data and credentials, send every log from every project to one protected place that administrators of those projects can't erase, keep it for the 30 months federal policy calls for, and alert the moment anyone tries to turn logging off. That way, when something happens, we can say exactly what happened — and prove it."

## Whiteboard prompt

Draw a federal tenant spanning Google Cloud (org → folders → projects; aggregated sink → locked log bucket + Cloud Storage cold tier + Pub/Sub to SIEM), AWS (organization trail → log archive account with S3 Object Lock), and Azure (Policy-deployed diagnostic settings → central Log Analytics; Entra logs exported with P1). Mark: which logs are on by default, which you enabled, retention on each tier, and the three tamper alerts. Then trace one intrusion — stolen SA key → discovery → bucket reads → sink deletion — through the logs.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud audit logging on Google Cloud, AWS, and Azure — Cloud Audit Logs types and routing, CloudTrail event types and trails, Azure Activity Log, resource logs, and Entra sign-in logs — including centralization, retention requirements such as OMB M-21-31, and which logs support which investigative questions."
- **After completing the lab:** "In a personal lab I enabled Google Cloud Data Access audit logs, routed audit logs to a dedicated log bucket, queried them with SQL in Observability Analytics to answer investigative questions, and confirmed that log-tampering actions were recorded in the undeletable Admin Activity log." Add CloudTrail trail and KQL sentences only if you did them.
- **Still requires (cert / production experience / clearance):** designing or operating enterprise logging pipelines, SIEM ingestion at scale, or incident investigations in production cloud environments. Your Splunk experience and analytic work with logs are real and transferable — describe them as they were (on-prem/enterprise sources), not as cloud logging experience, and only at a publicly discussable level. Splunk Core User is earned; Google Professional Cloud Security Engineer or Microsoft SC-200 would make the cloud side claimable.
