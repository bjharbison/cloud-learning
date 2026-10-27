# 18 — Logging and audit trails: Cloud Audit Logs, CloudTrail, Azure Activity and Entra logs; centralizing logs

> **In one sentence:** you'll know which logs each cloud writes by default, which you must turn on, how to route them to one place and keep them long enough, and — most important for CTI and detection work — which log answers which investigative question.

**Prereqs:** modules 00–17 (module 09 for aggregated sinks and BigQuery; module 08 for storage data-access gaps; module 15 for Entra sign-ins) · **Time:** ~4 hours incl. lab · **Phase:** 5

## Learning objectives

- Name the **audit log types** on each cloud and which are on by default: Google **Admin Activity / Data Access / System Event / Policy Denied**; AWS CloudTrail **management / data / network activity / Insights** events; Azure **Activity Log**, **resource logs**, and **Entra sign-in and audit logs**.
- Read an audit log entry and pull out **who, what, where, when, from where, and how**.
- Turn on **Data Access** logging deliberately, with cost in mind.
- Design **centralized** logging: aggregated sinks, organization trails, diagnostic settings at scale; set **retention**.
- Map investigative questions to the right log, and log tampering to ATT&CK.

## Why this matters for the target roles

- **CTI / detection:** this is the module everything in Phase 6 depends on. In cloud intrusions, there's often no malware and no endpoint — the audit log *is* the evidence.
- **Cloud security:** "Data Access logs were off" is one of the most common post-incident findings.
- **Customer engineer:** every federal customer asks about logging to **M-21-31** and retention. You need to answer with specifics: what's on, what costs money, and where it lands.

---

## Concepts

### Four kinds of cloud log

| Kind | Question it answers | Examples |
|---|---|---|
| **Control-plane audit** | Who changed the configuration? | Create VM, change IAM, delete a sink |
| **Data-plane audit** | Who read or wrote the data? | Read an object, query a table, decrypt with a key, access a secret |
| **Sign-in / identity** | Who authenticated, how, from where? | Entra sign-in logs, AWS `ConsoleLogin`, Google login audit |
| **Platform / network / app** | What happened on the wire or in the workload? | VPC Flow Logs, firewall logs, load balancer logs, app stdout, guest OS logs |

**Bridge from Splunk:** think of each as a **sourcetype**. Control-plane audit is your Windows Security log for the cloud's management API; data-plane audit is file-access auditing (which, like object-access auditing on Windows, is off until you enable it and gets noisy fast); sign-in logs are your authentication sourcetype; flow logs are NetFlow.

### Google Cloud: Cloud Audit Logs

| Type | Default | Can disable? | Stored in | Charged? |
|---|---|---|---|---|
| **Admin Activity** — config changes (`SetIamPolicy`, `insert`, `delete`) | **On** | No | `_Required` (400 days) | No |
| **System Event** — Google-initiated changes (e.g., live migration) | **On** | No | `_Required` | No |
| **Data Access** — `ADMIN_READ` (read config), `DATA_READ`, `DATA_WRITE` | **Off** (except **BigQuery**, always on) | Yes | `_Default` (30 days) | Yes |
| **Policy Denied** — a request blocked by VPC Service Controls or similar | **On** | Can only exclude from storage | `_Default` | Yes |

The log names you'll filter on: `cloudaudit.googleapis.com%2Factivity`, `%2Fdata_access`, `%2Fsystem_event`, `%2Fpolicy`.

**Turning on Data Access logs:** console **IAM & Admin → Audit Logs**, per service and per sub-type, with **exempted principals** (e.g., a noisy pipeline service account). Or edit `auditConfigs` in the project/folder/org IAM policy. Settings **inherit and add up** down the hierarchy — a project can't turn off what the org turned on. Viewing them needs **Private Logs Viewer** (`roles/logging.privateLogViewer`); Editor isn't enough.

**What to turn on first** — Google's own security log analytics guidance: Data Access for the identity and secrets services (**IAM, IAP, Cloud KMS, Secret Manager, Resource Manager**), then sensitive storage and databases, then the rest as budget allows. Remember the module 08 gap: access through public (`allUsers`) grants isn't audit-logged at all.

**Anatomy of an entry** (`protoPayload` is an `AuditLog`):

| Field | Tells you |
|---|---|
| `protoPayload.authenticationInfo.principalEmail` | **Who** (user, service account, or federated principal) |
| `protoPayload.authenticationInfo.serviceAccountDelegationInfo` | **Through whom** — impersonation chain |
| `protoPayload.methodName` | **What** (`SetIamPolicy`, `storage.objects.get`) |
| `protoPayload.resourceName` / `resource.labels` | **On what** |
| `protoPayload.requestMetadata.callerIp`, `callerSuppliedUserAgent` | **From where, with what tool** |
| `protoPayload.status` | Succeeded or failed (failures are intent) |
| `timestamp` | **When** |

### Google Cloud: storing and routing logs

- Every project has two **log buckets**: **`_Required`** (Admin Activity, System Event, Access Transparency and similar; **400 days, fixed, free, can't be deleted**) and **`_Default`** (everything else; **30 days** default, adjustable from 1 to 3,650 days for project buckets). You can create your own buckets, optionally **locked** so retention can't be shortened.
- The **Log Router** sends each entry through **sinks**: one inclusion filter, up to 50 exclusions, destination = log bucket, **BigQuery**, **Cloud Storage**, **Pub/Sub** (the usual path to Splunk or another SIEM), or another project.
- **Aggregated sinks** at the **organization or folder** (`--include-children`) collect every project's logs — module 09 built one into BigQuery. An **intercepting** sink (`--intercept-children`) also stops matching logs from flowing to the children's own sinks (except `_Required`).
- A sink in another project writes as a **writer identity** (`service-NUMBER@gcp-sa-logging.iam.gserviceaccount.com`) that needs a role on the destination.
- **Observability Analytics** (formerly **Log Analytics**) upgrades a log bucket so you can query it in **SQL** — free to upgrade and query from the console; optionally link a read-only BigQuery dataset (BigQuery charges for queries). The upgrade is permanent.

**Pricing to know:** **$0.50/GiB** to store logs (covers 30 days), **first 50 GiB per project per month free**, **$0.01/GiB-month** beyond 30 days; `_Required` is free; each extra copy you route is charged again; VPC Flow/firewall/NAT logs are **$0.25/GiB**. Data Access logs on a busy storage bucket can dwarf everything else — enable them where they answer a question you'll actually ask.

### Google Cloud: logs about Google

- **Access Transparency** records actions **Google personnel** take on your content — who, why (justification), when.
- **Access Approval** lets you approve or deny those requests in advance (requires Access Transparency).
- Eligibility depends on organization and support tier ⚠️ (Google's pages differ; confirm for your case). Pairs with Key Access Justifications (module 16).

### AWS: CloudTrail

| Event type | Default | Cost |
|---|---|---|
| **Management events** (control plane, incl. `ConsoleLogin`, KMS crypto ops) | **On** in **Event history** (90 days, per Region, free) | First copy to a trail's S3 bucket free |
| **Data events** (S3 `GetObject`/`PutObject`, Lambda `Invoke`, DynamoDB items…) | **Off** | $0.10 per 100,000 |
| **Network activity events** (API calls through VPC endpoints) | **Off** | $0.10 per 100,000 |
| **Insights events** (unusual API call or error rates) | **Off** | $0.35 per 100,000 events analyzed |

- **Event history** is a 90-day convenience view of management events with one filter at a time. For anything real, create a **trail**: **multi-Region** (AWS's recommendation; console trails are always multi-Region), delivered to **S3**, optionally to **CloudWatch Logs** and EventBridge.
- **Organization trails** from the management account cover every member account; members can see but not change them. The standard pattern sends them to a dedicated **log archive account**.
- **Log file integrity validation**: hourly digest files with SHA-256 hashes, signed and chained. Turning it on doesn't validate anything — run `aws cloudtrail validate-logs` during an investigation.
- **CloudTrail Lake** (managed SQL event store) **stopped accepting new customers on May 31, 2026**; AWS points new users to CloudWatch. **Amazon Security Lake** (OCSF, module 09) is the security-data-lake option.

**Entry anatomy:** `userIdentity` (type, ARN, `accessKeyId`, `sessionContext` for assumed roles), `eventSource`, `eventName`, `awsRegion`, `sourceIPAddress`, `userAgent`, `requestParameters`, `errorCode`. `AccessDenied` errors are early warning of discovery.

### Azure and Microsoft Entra

- **Activity Log** — subscription-level **control-plane** writes, kept **90 days**, collected automatically, free. Reads generally aren't recorded.
- **Resource logs** (data plane — Key Vault access, Storage reads, NSG flow) — **not collected until you create a diagnostic setting** for each resource. At scale, organizations assign **Azure Policy** to deploy diagnostic settings everywhere ⚠️ (policy-driven deployment noted from general guidance; detail in module 20).
- **Diagnostic settings** send logs to a **Log Analytics workspace** (query with **KQL**), a storage account (archive), or **Event Hubs** (stream to a SIEM).
- **Entra sign-in logs** (interactive, non-interactive, service principal, managed identity) and **audit logs** (directory changes). Retained **7 days on Entra ID Free, 30 days on P1/P2** — upgrading doesn't bring back expired data. **Exporting them to Log Analytics requires P1 or P2.**
- **Log Analytics**: first **5 GB per month per billing account free**; the **AzureActivity** table has no ingestion charge; 31 days of retention included (90 for Sentinel-enabled workspaces), up to 12 years. Table plans: **Analytics**, **Basic**, **Auxiliary** (cheaper ingestion, pay to query).
- **Microsoft Purview Audit** covers Microsoft 365 (Exchange, SharePoint, Teams). After the 2023 Storm-0558 intrusion, Microsoft expanded logging in **Audit (Standard)** for government and other customers — including **MailItemsAccessed** — and CISA published an implementation playbook. Standard retention is now 180 days.

### Centralize, then retain

| Goal | Google Cloud | AWS | Azure |
|---|---|---|---|
| Every account/project, one place | **Org-level aggregated sink** → dedicated logging project | **Organization trail** → log archive account | Diagnostic settings (via Azure Policy) → central workspace |
| Tamper-resistant retention | **Locked** log bucket; Bucket Lock on Cloud Storage (module 08) | S3 **Object Lock** + integrity validation | Immutable storage; workspace retention + access control |
| SIEM feed | Pub/Sub sink | S3 + SQS, or CloudWatch/EventBridge | Event Hubs |

**Retention policy:** OMB **M-21-31** (August 2021) defines event-logging maturity tiers **EL0–EL3** and calls for **12 months of active storage plus 18 months of cold storage** for key logs — cloud audit logs among them. CISA's July 2023 Storm-0558 advisory (AA23-193A) repeated that recommendation. Default retention on every cloud is far shorter.

**Bridge to your intel background:** retention is your collection window. An intrusion discovered 200 days after initial access (not unusual) is unexplainable if your logs roll off at 90. Set retention from the threat's dwell time, not the default.

### Which log answers which question?

| Investigative question | Google Cloud | AWS | Azure / Entra |
|---|---|---|---|
| Who signed in, from where, with what MFA? | Cloud Identity/Workspace login audit; IdP logs | CloudTrail `ConsoleLogin`; Identity Center events | **Entra sign-in logs** |
| Who changed IAM or created credentials? | Admin Activity: `SetIamPolicy`, `CreateServiceAccountKey` | Management: `AttachRolePolicy`, `CreateAccessKey` | Activity Log `roleAssignments/write`; Entra audit logs |
| Who read this file / table / secret? | **Data Access** logs (enable first); BigQuery always | **Data events** (enable first) | Resource logs via diagnostic settings |
| Who decrypted with this key? | Data Access (Cloud KMS) | Management events (KMS) | Key Vault resource logs |
| Did anyone tamper with logging? | Admin Activity: `UpdateSink`, `DeleteSink`, audit-config changes in `SetIamPolicy` | `StopLogging`, `DeleteTrail`, `PutEventSelectors` | Diagnostic setting delete; Activity Log |
| Did a VM talk to a strange IP? | VPC Flow Logs, firewall logs | VPC Flow Logs | VNet flow logs |
| Did Google/Microsoft staff touch our data? | **Access Transparency** | ⚠️ no direct equivalent found | **Customer Lockbox** records ⚠️ |
| What was blocked by a perimeter? | Policy Denied logs | `AccessDenied` errors | Policy/deny events ⚠️ |

> **Shared responsibility — say it plainly:** providers generate the audit logs and protect `_Required` / Event history. **Turning on data-access logging, creating trails and diagnostic settings, centralizing, retention length, protecting logs from your own admins, and actually reviewing them are always the customer's.**

---

## Text diagram — centralized audit logging on Google Cloud

```
 Org agency.gov ── Audit config: Data Access ON for IAM, IAP, KMS, Secret Manager, Resource Manager
   ├─ Folder Prod ── projects …┐
   ├─ Folder Dev  ── projects …├─► Org Log Router: aggregated sinks (include-children)
   └─ Folder Sec               │     filter: logName:"cloudaudit.googleapis.com" OR VPC/firewall logs
                               ├─ sink 1 ─► Project sec-logging: log bucket "audit-central"
                               │             (locked, 400+ days, Observability Analytics → SQL)
                               ├─ sink 2 ─► Pub/Sub topic ──► SIEM (Google SecOps / Splunk / Sentinel) [module 22]
                               └─ sink 3 ─► Cloud Storage (Bucket Lock, Archive class) — 18-month cold tier
   Every project still keeps its own _Required (400 d, free, undeletable) — the tamper backstop
   Alerts: DeleteSink / UpdateSink / audit-config change → log-based alert (module 19)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Control-plane audit, default on | Admin Activity (400 d, free) | Management events — Event history 90 d | Activity Log 90 d | Google keeps longest by default |
| Data-plane audit | Data Access logs (off; BigQuery on) | Data events (off, $0.10/100k) | Resource logs (off until diagnostic setting) | All three make you opt in |
| Identity sign-ins | Cloud Identity / Workspace login audit | `ConsoleLogin` in CloudTrail | **Entra sign-in logs** (7 d Free / 30 d P1+) | Entra export needs P1/P2 |
| Central collection | Aggregated sinks (org/folder) | Organization trail | Diagnostic settings + Azure Policy | |
| Native query | Logging query language; **Observability Analytics** SQL | CloudWatch Logs Insights; Athena; (CloudTrail Lake closed to new customers) | **KQL** in Log Analytics | Splunk SPL users find KQL most familiar |
| Integrity / immutability | Locked buckets; `_Required` undeletable | Digest-file validation; S3 Object Lock | Immutable storage | Only AWS signs log digests |
| Provider-access logs | Access Transparency + Access Approval | — ⚠️ | Customer Lockbox | |
| Free tier | 50 GiB/project/month; `_Required` free | Event history + first trail copy free | 5 GB/billing account/month; AzureActivity free | |

## Administer and monitor it

- **Audit the auditing:** `gcloud projects get-iam-policy PROJECT --format=json | jq .auditConfigs`; `aws cloudtrail describe-trails` + `get-event-selectors`; check diagnostic settings coverage with Azure Policy compliance.
- **Watch volume and cost:** Cloud Logging usage by log name; CloudTrail data-event counts; Log Analytics `Usage` table.
- **Alert on logging changes** (module 19): sink/trail/diagnostic-setting deletion, `StopLogging`, audit-config edits, retention reductions.
- **Test your logs** — every lab from here on ends by finding its own actions in the logs.

## Security angle

1. **Data Access / data events off** for the services that hold secrets and sensitive data.
2. **No organization-wide collection** — new projects/accounts/subscriptions land unlogged.
3. **Retention at defaults** (30/90 days) vs a 12+18-month requirement.
4. **Logging admins = workload admins** — whoever can disable logs can hide their tracks. Separate the logging project/account.
5. **No Entra log export** — sign-in history evaporates after 7 or 30 days.
6. **Over-exempting principals** in Data Access configs (a compromised exempted SA is invisible).
7. **Logs collected, never reviewed** — no alerts on tampering.

## Threat intel angle

**ATT&CK changed in April 2026.** Version 19 (still current in substance after v20, October 2026) split **Defense Evasion** into **Stealth** (TA0005) and **Defense Impairment** (TA0112), and revoked **T1562 Impair Defenses**. Cloud log tampering is now **T1685.002 Disable or Modify Tools: Disable or Modify Cloud Log**, which MITRE says revoked the old "Disable or Modify Cloud Logs" sub-technique (T1562.008 — the ID mapping is by name ⚠️); firewall tampering moved to **T1686** (modules 10–11 cite the older T1562.007 — read them with that in mind). Older vendor reports will use the old IDs.

| Technique | ATT&CK | What it looks like in logs |
|---|---|---|
| Disable or modify cloud logs | **T1685.002** | `DeleteSink`/`UpdateSink`, audit-config removed; `StopLogging`, `DeleteTrail`, `PutEventSelectors` excluding sources; diagnostic setting deleted |
| Valid cloud accounts | **T1078.004** | Sign-ins from new ASNs/countries; service-account use from outside expected workloads |
| Add credentials for persistence | **T1098.001 Additional Cloud Credentials** | `CreateServiceAccountKey`, `CreateAccessKey`, new app secrets in Entra audit logs |
| Cloud infrastructure discovery | **T1580** | Bursts of `List*`/`Describe*`/`Get*`, often with `AccessDenied` |
| Data from cloud storage | **T1530** | Data Access / data events — only if enabled |
| Transfer to attacker's cloud account | **T1537** | Snapshot/image sharing, cross-account copy, VPC-SC Policy Denied entries |

**The case to know:** in June 2023, a U.S. federal civilian agency detected the Storm-0558 intrusion by noticing **MailItemsAccessed** events from an unexpected application ID in its Microsoft 365 audit logs — logging that, at the time, required the premium license tier. CISA/FBI advisory **AA23-193A** describes it; the episode drove Microsoft's expansion of standard logging. It's the clearest public example of "the log you didn't pay for is the intrusion you didn't see."

**Also read:** *Best Practices for Event Logging and Threat Detection* (ASD's ACSC with CISA, FBI, NSA and partners, August 2024).

**Bridge to your CTI work:** treat audit logs as your collection plan. Write the intelligence requirement first ("would we see a new credential created for a service account?"), then confirm the log exists, is on, is centralized, and is retained. Gaps in collection are findings in their own right.

## Public sector notes

- **M-21-31** logging maturity (EL0–EL3) and 12+18-month retention are the federal yardstick; DoD and IC environments add their own requirements.
- **Access Transparency / Access Approval** (Google) and **Customer Lockbox** (Microsoft) answer "can the provider's staff see our data, and would we know?"
- Microsoft's expanded Purview Audit (Standard) logging came directly out of a federal agency's detection — a useful talking point.
- For Assured Workloads and GovCloud logging specifics, see module 27.

## Key takeaways

- Control-plane audit is on by default everywhere; **data-plane audit is off everywhere** until you turn it on (BigQuery excepted).
- Google: Admin Activity + System Event in **`_Required` (400 days, free)**; Data Access and Policy Denied in `_Default` (30 days).
- AWS: Event history is 90 days; create a **multi-Region organization trail**; data events cost extra; CloudTrail Lake is closed to new customers.
- Azure: Activity Log 90 days; resource logs need **diagnostic settings**; Entra logs 7/30 days and export needs P1/P2.
- Centralize (aggregated sink / org trail / policy-driven diagnostic settings), separate logging admins, and retain to **M-21-31** (12 + 18 months).
- Cloud log tampering is **T1685.002** in ATT&CK v19 — alert on it.
- Enabling, centralizing, retaining, and reviewing logs are **always the customer's**.

## Sources

- [Google Cloud — Cloud Audit Logs overview](https://docs.cloud.google.com/logging/docs/audit), [Enable Data Access audit logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access), [Routing overview](https://docs.cloud.google.com/logging/docs/routing/overview), [Configure sinks](https://docs.cloud.google.com/logging/docs/export/configure_export_v2), [Aggregated sinks](https://docs.cloud.google.com/logging/docs/export/aggregated_sinks), [Log storage](https://docs.cloud.google.com/logging/docs/store-log-entries), [Quotas and retention](https://docs.cloud.google.com/logging/quotas), [Observability Analytics](https://docs.cloud.google.com/logging/docs/log-analytics), [Logging release notes](https://docs.cloud.google.com/logging/docs/release-notes), [Observability pricing](https://cloud.google.com/products/observability/pricing)
- [Google Cloud — Security log analytics](https://docs.cloud.google.com/architecture/security-log-analytics), [Access Transparency](https://docs.cloud.google.com/assured-workloads/access-transparency/docs/overview), [enable Access Transparency](https://docs.cloud.google.com/assured-workloads/access-transparency/docs/enable), [Access Approval](https://docs.cloud.google.com/assured-workloads/access-approval/docs/overview), [gcloud logging read](https://docs.cloud.google.com/sdk/gcloud/reference/logging/read), [gcloud logging buckets create](https://docs.cloud.google.com/sdk/gcloud/reference/logging/buckets/create)
- [AWS — CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html), [Event history](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html), [log file validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html), [create a trail with the CLI](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail-by-using-the-aws-cli-create-trail.html), [CloudTrail Lake availability change](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-lake-service-availability-change.html), [CloudTrail pricing](https://aws.amazon.com/cloudtrail/pricing/), [Logging KMS calls with CloudTrail](https://docs.aws.amazon.com/kms/latest/developerguide/logging-using-cloudtrail.html), [lookup-events](https://docs.aws.amazon.com/cli/latest/reference/cloudtrail/lookup-events.html), [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [Microsoft — Activity log](https://learn.microsoft.com/en-us/azure/azure-monitor/platform/activity-log), [data retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure), [Log Analytics costs and table plans](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs), [Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/), [Entra data retention](https://learn.microsoft.com/en-us/entra/identity/monitoring-health/reference-reports-data-retention), [Entra logs in Log Analytics](https://learn.microsoft.com/en-us/entra/identity/monitoring-health/howto-integrate-activity-logs-with-azure-monitor-logs), [Purview Audit solutions](https://learn.microsoft.com/en-us/purview/audit-solutions-overview), [Customer Lockbox for Azure](https://learn.microsoft.com/en-us/azure/security/fundamentals/customer-lockbox-overview), [Sentinel billing](https://learn.microsoft.com/en-us/azure/sentinel/billing), [az monitor activity-log](https://learn.microsoft.com/en-us/cli/azure/monitor/activity-log?view=azure-cli-latest)
- [CISA/FBI AA23-193A — Enhanced monitoring to detect APT activity targeting Outlook Online (PDF)](https://www.cisa.gov/sites/default/files/2023-07/aa23-193a_joint_csa_enhanced_monitoring_to_detect_apt_activity_targeting_outlook_online.pdf), [CISA Microsoft expanded cloud logs playbook](https://www.cisa.gov/news-events/alerts/2025/01/15/cisa-releases-microsoft-expanded-cloud-logs-implementation-playbook), [Best Practices for Event Logging and Threat Detection](https://www.cisa.gov/resources-tools/resources/best-practices-event-logging-and-threat-detection)
- [OMB M-21-31](https://www.whitehouse.gov/wp-content/uploads/2021/08/M-21-31-Improving-the-Federal-Governments-Investigative-and-Remediation-Capabilities-Related-to-Cybersecurity-Incidents.pdf)
- [MITRE ATT&CK — April 2026 (v19) updates](https://attack.mitre.org/resources/updates/updates-april-2026/), [T1685.002](https://attack.mitre.org/techniques/T1685/002/), [T1078.004](https://attack.mitre.org/techniques/T1078/004/), [T1098.001](https://attack.mitre.org/techniques/T1098/001/), [T1580](https://attack.mitre.org/techniques/T1580/), [T1530](https://attack.mitre.org/techniques/T1530/), [T1537](https://attack.mitre.org/techniques/T1537/)

Verified: 2026-10-27
