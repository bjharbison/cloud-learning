# 18 Quiz — Logging and audit trails

1. Name Google Cloud's four audit log types, which are on by default, and which bucket each lands in.
<details><summary>Answer</summary>

Admin Activity (on, can't disable, `_Required`), System Event (on, can't disable, `_Required`), Data Access (off except BigQuery, `_Default`), Policy Denied (on; can only be excluded from storage, `_Default`).
</details>

2. An analyst asks, "Who downloaded `payroll.csv` from our bucket last month?" On Google Cloud, what has to have been true for you to answer?
<details><summary>Answer</summary>

Data Access audit logs (`DATA_READ`) must have been enabled for Cloud Storage before the access, retained long enough (`_Default` is 30 days unless changed or routed elsewhere), and the access must have been through an authenticated principal — access via public `allUsers` grants isn't audit-logged.
</details>

3. Match the AWS CloudTrail event type to the example: `GetObject`, `AttachRolePolicy`, an API call through a VPC endpoint, an unusual spike in `RunInstances` calls.
<details><summary>Answer</summary>

`GetObject` = data event; `AttachRolePolicy` = management event; VPC endpoint call = network activity event; spike = Insights event.
</details>

4. What's the difference between CloudTrail Event history and a trail?
<details><summary>Answer</summary>

Event history: free, 90 days, management events only, per Region, view/lookup with one filter at a time. A trail: delivers events (optionally data, network activity, Insights) to S3 (and optionally CloudWatch Logs/EventBridge) for as long as you retain them; multi-Region and organization-wide options; integrity validation.
</details>

5. On Azure, which logs exist without any setup, and which need a diagnostic setting?
<details><summary>Answer</summary>

The Activity Log (subscription control plane, 90 days) exists automatically, as do Entra sign-in/audit logs (7 or 30 days depending on license). Resource logs (data plane) need diagnostic settings; exporting Activity or Entra logs to a workspace for longer retention also needs a diagnostic setting (Entra export needs P1/P2).
</details>

6. Spot the problem: an agency's security team has Owner on every workload project and also administers the org-level log sink and logging project.
<details><summary>Answer</summary>

No separation of duties: the people (or a stolen credential) that could compromise workloads can also disable or alter the logs. Put logging in a separate project/account with separately held admin rights, lock retention, and alert on logging changes.
</details>

7. What is ATT&CK T1685.002, and what was it called before April 2026?
<details><summary>Answer</summary>

Disable or Modify Tools: Disable or Modify Cloud Log, under the new Defense Impairment tactic (TA0112). It replaced T1562.008 Impair Defenses: Disable or Modify Cloud Logs when ATT&CK v19 revoked T1562 and split Defense Evasion into Stealth and Defense Impairment.
</details>

8. Give one log event per cloud you'd alert on for T1685.002.
<details><summary>Answer</summary>

Google: `DeleteSink`/`UpdateSink` or removal of audit configs (Admin Activity). AWS: `StopLogging`, `DeleteTrail`, or `PutEventSelectors` excluding sources. Azure: deletion of a diagnostic setting (Activity Log).
</details>

9. What retention does OMB M-21-31 call for on key logs, and how does it compare with the defaults?
<details><summary>Answer</summary>

12 months active plus 18 months cold storage. Defaults: Google `_Default` 30 days (`_Required` 400 days), AWS Event history 90 days, Azure Activity Log 90 days, Entra sign-ins 7 or 30 days — all short of the requirement without routing and retention settings.
</details>

10. Scenario: how was the 2023 Storm-0558 intrusion first detected by a federal agency, and what's the lesson?
<details><summary>Answer</summary>

The agency spotted MailItemsAccessed events from an unexpected application ID in its Microsoft 365 (Purview) audit logs, which at the time required a premium license. Lesson: detection depends on which logs you collect and baseline; Microsoft later expanded standard logging (CISA AA23-193A).
</details>

11. A sink routes logs to a BigQuery dataset in a different project, but nothing arrives. What's the most likely cause?
<details><summary>Answer</summary>

The sink's writer identity (`service-NUMBER@gcp-sa-logging.iam.gserviceaccount.com`) wasn't granted a role on the destination (e.g., `roles/bigquery.dataEditor` on the dataset). Also check the filter and that only new entries are routed.
</details>

12. Splunk bridge: what are the Google Cloud equivalents of a forwarder fleet, an index, and SPL?
<details><summary>Answer</summary>

Aggregated sinks / Log Router (forwarders), a log bucket or BigQuery dataset (index), and the Logging query language or SQL in Observability Analytics (SPL). On Azure, KQL in Log Analytics plays the SPL role.
</details>
