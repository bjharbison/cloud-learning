# 22 Quiz — Cloud detection engineering and SIEM

1. List the stages of the detection engineering lifecycle and the intelligence-cycle step each resembles.
<details><summary>Answer</summary>

Requirement (intel requirement) → research (collection planning: technique, log, fields, is it collected?) → develop (processing/analysis) → test with emulated true positives and historical false positives (validation) → deploy with runbook (dissemination) → tune (feedback) → retire.
</details>

2. Name the four platforms in ATT&CK's cloud matrix today, and what they replaced.
<details><summary>Answer</summary>

IaaS, SaaS, Office Suite, Identity Provider. Since v16 (October 2024) they replaced the Azure AD, Office 365, and Google Workspace platforms.
</details>

3. What did ATT&CK v18 and v19 change that a detection engineer should know?
<details><summary>Answer</summary>

v18 (Oct 2025) replaced free-text detection sections with Detection Strategies and Analytics (per-platform logic, log sources, tunable elements). v19 (Apr 2026) split Defense Evasion into Stealth and Defense Impairment and revoked T1562 in favor of T1685, so cloud log tampering is T1685.002.
</details>

4. Match the language to the platform: YARA-L 2.0, KQL, CloudWatch Logs Insights, Sigma.
<details><summary>Answer</summary>

YARA-L 2.0: Google Security Operations. KQL: Microsoft Sentinel / Log Analytics. Logs Insights: AWS CloudWatch Logs. Sigma: vendor-neutral format converted to others (and used natively by OpenSearch Security Analytics).
</details>

5. Name the five main sections of a YARA-L 2.0 rule and what `match: $user over 15m` does.
<details><summary>Answer</summary>

`meta`, `events`, `match`, `outcome`, `condition` (plus optional `options`). The match line groups matching events by the `$user` placeholder within a 15-minute window — like SPL's `stats … by user` over a time bucket.
</details>

6. Translate to KQL: `index=azure sourcetype=activity | stats count by Caller | where count > 5`.
<details><summary>Answer</summary>

```kusto
AzureActivity
| summarize count_ = count() by Caller
| where count_ > 5
```
`stats` → `summarize`; the table name replaces index/sourcetype.
</details>

7. A customer's AWS-only shop asks, "What's AWS's SIEM?" What do you say?
<details><summary>Answer</summary>

AWS doesn't sell a single SIEM. It offers building blocks — GuardDuty (managed threat detection), Security Hub (correlated findings), Security Lake (OCSF data lake), OpenSearch Security Analytics (Sigma rules), CloudWatch Logs Insights and EventBridge — and many customers run Splunk, Google SecOps, or Sentinel on top.
</details>

8. Spot the problem: a detection for SA key creation excludes every principal ending in `gserviceaccount.com` "to cut noise from automation."
<details><summary>Answer</summary>

It blinds you to compromised service accounts — the most common cloud attacker identity (T1078.004) — creating keys for persistence (T1098.001). Exclude only the specific pipeline identity, ideally combined with expected user agent and source.
</details>

9. Why might a console sign-in show `MFAUsed = "No"` in CloudTrail even though MFA was used?
<details><summary>Answer</summary>

Federated sign-ins always show "No" because MFA happened at the external identity provider. Filter detections to `Root` and `IAMUser` identity types.
</details>

10. What changes for Sentinel customers by March 31, 2027?
<details><summary>Answer</summary>

After that date Sentinel is supported only in the Microsoft Defender portal, not the Azure portal. Some rule types (Fusion, "Microsoft security") aren't available there because Defender XDR handles that correlation.
</details>

11. Your Sentinel GCP connector stopped ingesting three days ago and no rule fired. What failed, and what control catches it?
<details><summary>Answer</summary>

Data-source health — a silent connector looks like a quiet environment. Monitor ingestion (Sentinel health data, metric-absence/volume alerts) and treat missing data as an alert; also check the Pub/Sub subscription and federation credentials on the Google side.
</details>

12. Why is Sigma useful for an agency planning a SIEM migration?
<details><summary>Answer</summary>

Detections written in Sigma are vendor-neutral and can be converted to SPL, KQL, and other backends (a community backend exists for Google SecOps), so detection content, ATT&CK tags, and tests survive the platform change.
</details>
