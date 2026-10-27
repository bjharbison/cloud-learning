# 18 Lab — Build your collection plan: audit logs on, routed, queried in SQL, and a tamper attempt caught

**Cost:** $0 expected on Google Cloud. Admin Activity logs and the `_Required` bucket are free; the Data Access logs and the routed copy you create here are a few MB against the **50 GiB per project per month** free allotment; upgrading a log bucket to Observability Analytics and querying it from the console are free; one tiny Cloud Storage bucket fits the always-free tier. AWS (optional): a CloudTrail trail's **first copy of management events is free**; you pay only S3 storage for a few KB of log files (fractions of a cent) — **don't** add data events, Insights, CloudWatch Logs delivery, or SSE-KMS for this lab. Azure (optional): a Log Analytics workspace receiving only the **AzureActivity** table, which has no ingestion charge. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Read an Admin Activity entry field by field: who, what, on what, from where, with what tool.
2. Turn on **Data Access** logs for Cloud Storage and see a `DATA_READ` record of your own object read.
3. Create a dedicated **log bucket** with **Observability Analytics** and a **sink** that routes all audit logs into it.
4. Answer investigative questions with **SQL**.
5. Attempt to tamper with logging — and find the evidence in `_Required`, which you can't touch.
6. (Optional) Do the same on AWS with Event history and a trail, and on Azure with the Activity Log and KQL.

## Prerequisites

- Modules 00–17 done; budget alerts active.
- Cloud Shell, lab project selected. `jq` is preinstalled in Cloud Shell.

```bash
PROJECT_ID=$(gcloud config get-value project)
ME=$(gcloud config get-value account)
B=lab18-$PROJECT_ID-$RANDOM
gcloud services enable logging.googleapis.com storage.googleapis.com
echo "$B"
```

---

## Part A — Google Cloud

### A1. Make some events, then read one like an analyst (CLI)

```bash
gcloud storage buckets create gs://$B --location=us-central1 --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=18
echo "case file 18" > evidence.txt && gcloud storage cp evidence.txt gs://$B/
sleep 30
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.methodName=\"storage.buckets.create\"" \
  --freshness=1h --limit=1 --format=json | jq '.[0] | {
    when: .timestamp,
    who: .protoPayload.authenticationInfo.principalEmail,
    what: .protoPayload.methodName,
    on: .protoPayload.resourceName,
    from_ip: .protoPayload.requestMetadata.callerIp,
    tool: .protoPayload.requestMetadata.callerSuppliedUserAgent,
    log: .logName }'
```

**What you should see:** your email, `storage.buckets.create`, `projects/_/buckets/lab18-...`, a Google Cloud Shell IP, and a user agent naming `gcloud`. That's the full **5 W's** of one action. Now look for the object upload:

```bash
gcloud logging read "protoPayload.serviceName=\"storage.googleapis.com\" AND protoPayload.methodName=\"storage.objects.create\"" --freshness=1h --limit=1 --format="value(logName)" || true
```

**What you should see:** nothing. Object writes and reads are **Data Access** logs, and they're off.

### A2. Turn on Data Access logs for Cloud Storage (console, then verify with CLI)

The console is the safer way to edit audit config — the CLI method rewrites your whole project IAM policy, and a mistake there can lock you out.

1. Console → **IAM & Admin → Audit Logs**.
2. Filter for **Google Cloud Storage**, check the row, then in the right panel check **Data Read** and **Data Write** → **Save**.
3. Verify from Cloud Shell:

```bash
gcloud projects get-iam-policy $PROJECT_ID --format=json | jq '.auditConfigs'
```

**What you should see:** an entry for `storage.googleapis.com` with `DATA_READ` and `DATA_WRITE`. (If you enabled IAP Data Read in module 17 and didn't turn it off, that appears too.)

Now generate a read and find it:

```bash
gcloud storage cat gs://$B/evidence.txt
sleep 60
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Fdata_access\" AND protoPayload.methodName=\"storage.objects.get\"" \
  --freshness=30m --limit=3 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.resourceName.basename(),protoPayload.requestMetadata.callerIp)"
```

**What you should see:** a row with your email reading `evidence.txt`. That's the record you need for **T1530 Data from Cloud Storage** — and it only exists because you turned it on.

### A3. A dedicated log bucket with Observability Analytics, and a sink (CLI)

```bash
gcloud logging buckets create lab18-security --location=global --retention-days=30 \
  --enable-analytics --description="lab18 central audit bucket"
gcloud logging sinks create lab18-audit \
  logging.googleapis.com/projects/$PROJECT_ID/locations/global/buckets/lab18-security \
  --log-filter='logName:"cloudaudit.googleapis.com"' --description="lab18: all audit logs"
gcloud logging sinks describe lab18-audit --format="yaml(destination,filter,writerIdentity)"
gcloud logging buckets list --format="table(name.basename(),retentionDays,analyticsEnabled,lifecycleState)"
```

**What you should see:** the sink with no `writerIdentity` (same-project bucket — no extra identity needed; a sink to another project would print one you'd have to grant `roles/logging.bucketWriter`). Three buckets: `_Required` (400 days), `_Default` (30), `lab18-security` (30, analytics enabled).

Why 30 days here? Retention beyond 30 days costs $0.01/GiB-month — trivial, but this lab stays at $0. A real design would use 400+ days and **lock** the bucket (`gcloud logging buckets update ... --locked`, which can't be casually reversed — don't do it in a lab).

Now create activity that the sink will catch (sinks only route entries written **after** they exist):

```bash
for i in 1 2 3; do gcloud storage cat gs://$B/evidence.txt > /dev/null; done
gcloud storage buckets update gs://$B --update-labels=lab=18,case=alpha
gcloud iam service-accounts create lab18-sa --display-name="lab18 suspicious SA"
gcloud storage buckets add-iam-policy-binding gs://$B \
  --member=serviceAccount:lab18-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/storage.objectViewer
```

### A4. Investigate in SQL (console)

Console → **Logging → Observability Analytics** (it may still be labeled **Log Analytics** in some views ⚠️). Wait a few minutes after A3, then select the `lab18-security` bucket's `_AllLogs` view and run:

```sql
-- Who did what in this project in the last 2 hours?
SELECT
  timestamp,
  proto_payload.audit_log.authentication_info.principal_email AS who,
  proto_payload.audit_log.method_name AS what,
  proto_payload.audit_log.resource_name AS target,
  proto_payload.audit_log.request_metadata.caller_ip AS from_ip
FROM `PROJECT_ID.global.lab18-security._AllLogs`
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
ORDER BY timestamp DESC
LIMIT 50
```

Replace `PROJECT_ID`. ⚠️ If a column name differs, open the schema panel and adjust — the nested names follow the log entry's JSON fields in snake_case. Then answer these with your own `WHERE` clauses:

1. Which IAM changes happened? (`what LIKE '%SetIamPolicy%'`)
2. How many times was `evidence.txt` read, and by whom? (`what = 'storage.objects.get'`)
3. Which principals created service accounts? (`what LIKE '%CreateServiceAccount%'`)

**Splunk bridge:** this is `index=audit | stats count by who, what` — the view is your index, `WHERE` is your search, and the console query history is your saved searches.

### A5. Tamper with logging — and get caught (CLI)

Play the adversary (T1685.002): try to weaken and remove logging.

```bash
gcloud logging buckets update _Required --location=global --retention-days=1 2>&1 | tail -2
gcloud logging sinks delete lab18-audit --quiet
sleep 60
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.serviceName=\"logging.googleapis.com\"" \
  --freshness=30m --limit=5 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail,protoPayload.status.code)"
```

**What you should see:** the `_Required` update is refused (you can't shorten or delete it). The sink deletion succeeds — and then shows up as `DeleteSink` (plus your earlier `CreateSink` and `CreateBucket`) in **Admin Activity**, stored in `_Required` for 400 days, which no project user can delete. An attacker can stop *future* routing; they can't erase the record that they did it. Module 19 turns that into an alert.

---

## Part B — AWS (optional): Event history and a trail

CloudShell, as `labadmin`.

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 5 --query 'Events[].{time:EventTime,user:Username,event:EventName}' --output table
aws cloudtrail lookup-events --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false \
  --max-results 10 --query 'Events[].[EventTime,EventSource,EventName,Username]' --output table
```

**What you should see:** your recent console sign-ins and write actions — free, 90 days, this Region only.

Now a real trail (console is easiest — it creates the bucket and bucket policy for you):

1. **CloudTrail → Trails → Create trail.** Name `lab18-trail`; **Create new S3 bucket**.
2. **Log file SSE-KMS encryption: uncheck it** for this lab ⚠️ (if left on, the console creates a customer managed KMS key at $1/month — module 16). **Log file validation: enabled.** **CloudWatch Logs: off.**
3. Event types: **Management events** only (Read and Write). No data, network activity, or Insights events.
4. Create. Then in CloudShell:

```bash
aws cloudtrail describe-trails --query 'trailList[].{name:Name,multiRegion:IsMultiRegionTrail,validation:LogFileValidationEnabled,bucket:S3BucketName}'
aws cloudtrail get-trail-status --name lab18-trail --query IsLogging
TB=$(aws cloudtrail describe-trails --trail-name-list lab18-trail --query 'trailList[0].S3BucketName' --output text)
sleep 900; aws s3 ls s3://$TB --recursive | head    # log files arrive within ~15 minutes
```

**What you should see:** `multiRegion: true`, `validation: true`, `IsLogging: true`, then `.json.gz` files under `AWSLogs/ACCOUNT/CloudTrail/REGION/...`. After an hour, a digest file appears under `CloudTrail-Digest/` and you can run `aws cloudtrail validate-logs --trail-arn ARN --start-time <ISO time>` ⚠️ (optional; requires waiting for the first digest).

## Part C — Azure (optional): Activity Log and KQL

Azure Cloud Shell (Bash), as `labadmin`.

```bash
az monitor activity-log list --offset 7d --max-events 10 \
  --query "[].{time:eventTimestamp, who:caller, op:operationName.localizedValue, status:status.value}" -o table
```

Then route it somewhere queryable:

```bash
az group create -n lab18-rg -l eastus --tags lab=18
az monitor log-analytics workspace create -g lab18-rg -n lab18-law -l eastus
```

Portal → **Monitor → Activity log → Export Activity Logs → Add diagnostic setting**: name `lab18-diag`, categories **Administrative** and **Security**, destination **Send to Log Analytics workspace** → `lab18-law` → Save. Create something (`az group create -n lab18-temp -l eastus && az group delete -n lab18-temp --yes`), wait ~10 minutes, then in the workspace's **Logs** blade run:

```kusto
AzureActivity
| where TimeGenerated > ago(1h)
| project TimeGenerated, Caller, OperationNameValue, ActivityStatusValue, CallerIpAddress
| order by TimeGenerated desc
```

Finally, **Entra admin center → Monitoring & health → Sign-in logs**: note the retention you're working with (7 days on Entra ID Free) and that exporting these to Log Analytics would need P1/P2.

---

## Verify it worked

| Check | Expected |
|---|---|
| Admin Activity entry | Who/what/on/from/tool all populated |
| Before Data Access enabled | No `storage.objects.*` audit entries |
| After enabling | `storage.objects.get` by you in `data_access` log |
| Log bucket | `lab18-security`, analytics enabled |
| SQL | IAM changes, reads of `evidence.txt`, SA creation all answerable |
| Tamper | `_Required` change refused; `DeleteSink` recorded in Admin Activity |
| (B) AWS | Multi-Region trail with validation; log files in S3 |
| (C) Azure | `AzureActivity` rows in KQL |

## What to notice (reflection questions)

1. Write one intelligence requirement this lab's logs can answer and one they *can't* (yet). What would you turn on to close the gap, and what would it cost?
2. Why can't an attacker with Owner on the project erase `DeleteSink` from `_Required`? What *could* they do, and how would you see it?
3. AWS logged your KMS calls by default (module 16); Google needed Data Access logs. Which default would you rather explain in an incident review?
4. Your Entra sign-in logs keep 7 days on the free tier. An intrusion is discovered on day 45. What's lost, and what licensing and export would have prevented it?
5. Map your sink, the org-level aggregated sink from module 09, and an AWS organization trail to the same design goal. What's the equivalent of the "log archive account" on Google Cloud?

## Cleanup

**Google Cloud**

1. Console → **IAM & Admin → Audit Logs → Google Cloud Storage** → uncheck **Data Read** and **Data Write** → **Save**. (Also IAP, if still on from module 17.) Verify:

```bash
gcloud projects get-iam-policy $PROJECT_ID --format=json | jq '.auditConfigs // "none"'
```

2. Then:

```bash
gcloud logging sinks delete lab18-audit --quiet 2>/dev/null || echo "sink already deleted in A5"
gcloud logging buckets delete lab18-security --location=global --quiet
gcloud iam service-accounts delete lab18-sa@$PROJECT_ID.iam.gserviceaccount.com --quiet
gcloud storage rm --recursive gs://$B
rm -f evidence.txt
gcloud logging sinks list --format="value(name)" | grep lab18 || echo "no lab18 sinks"
gcloud logging buckets list --format="table(name.basename(),lifecycleState)"
gcloud storage ls | grep lab18 || echo "no lab18 buckets"
```

**What you should see:** `lab18-security` in `DELETE_REQUESTED` — Google keeps a deleted log bucket recoverable for a short period (`gcloud logging buckets undelete`) before removing it ⚠️ (exact period not re-verified this run). Stored logs are within the free allotment either way.

**AWS**

```bash
aws cloudtrail delete-trail --name lab18-trail
aws s3 rm s3://$TB --recursive && aws s3 rb s3://$TB
aws cloudtrail describe-trails --query 'trailList[].Name'      # lab18-trail gone
```

`delete-trail` does **not** delete the S3 bucket or its log files — the last two commands do.

**Azure**

```bash
az monitor diagnostic-settings subscription delete --name lab18-diag --yes 2>/dev/null \
  || echo "Delete it in the portal: Monitor → Activity log → Export Activity Logs → lab18-diag → Delete"
az group delete -n lab18-rg --yes --no-wait
```

The diagnostic setting lives on the **subscription**, not in `lab18-rg`, so deleting the resource group doesn't remove it — confirm it's gone in the portal. ⚠️ The `subscription delete` command's exact parameters weren't verified; use the portal path if it errors.

**Final check — nothing billable remains:** Data Access logs back to off; no `lab18` sink, bucket, service account, or Cloud Storage bucket; no `lab18-trail` or its S3 bucket; no `lab18-diag` subscription diagnostic setting and no `lab18-rg`.

## Write-up prompt

> On [date] I worked with Google Cloud Audit Logs in a personal lab: I parsed Admin Activity entries for principal, method, resource, source IP, and user agent; enabled Data Access audit logs for Cloud Storage and confirmed object reads were recorded only after enabling them; created a dedicated log bucket upgraded to Observability Analytics with a sink routing all audit logs to it; and answered investigative questions (IAM changes, object reads, service-account creation) with SQL. I simulated log tampering by attempting to shorten the `_Required` bucket's retention (refused) and deleting the sink, then located the `DeleteSink` event in the undeletable Admin Activity log. [Optional: I queried AWS CloudTrail Event history, created a multi-Region trail with log file validation, and queried the Azure Activity Log in a Log Analytics workspace with KQL.] I deleted all resources and restored default audit settings afterward.
