# 22 Lab — Detection engineering end to end: requirement → query → emulate → deploy → translate

**Cost:** $0 expected. Google Cloud: Admin Activity audit logs are free; log-based alerting policies aren't charged before September 2027 (module 19); one service account and one sink pointed at the existing `_Default` bucket don't bill. Azure (optional): a Log Analytics workspace that receives only the **AzureActivity** table (no ingestion charge) — you'll run queries but **not** create a scheduled log search alert (those are billed) or start a Sentinel trial. AWS (optional): CloudTrail **Event history** (free) and `aws events test-event-pattern` (a free API call); no trail, no CloudWatch Logs. Google SecOps has no self-serve trial, so YARA-L is written and reviewed, not run. · **Time:** 2 hours · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Write two **detection requirements** as code (YAML specs with ATT&CK mapping, data source, logic, tests, runbook).
2. **Hunt** for them in the audit history your earlier labs created.
3. **Emulate** each behavior to generate a true positive.
4. **Deploy** both as log-based alerting policies and watch them fire.
5. **Translate** the logic to YARA-L and KQL (and run KQL for real on Azure).
6. (Optional) Build and **unit-test** an AWS EventBridge detection pattern, and hunt in CloudTrail Event history.

## Prerequisites

- Modules 00–21 done (module 18's log anatomy is assumed); budget alerts active.
- Cloud Shell, lab project selected.

```bash
PROJECT_ID=$(gcloud config get-value project)
ME=$(gcloud config get-value account)
mkdir -p ~/lab22/detections && cd ~/lab22
gcloud services enable logging.googleapis.com monitoring.googleapis.com iam.googleapis.com
```

---

## Part A — Google Cloud

### A1. Requirement and research → detection specs (CLI)

Two requirements, written the way a detection-as-code repo stores them:

```bash
cat > detections/gcp_iam_change_by_human.yaml <<'EOF'
id: GCP-IAM-001
title: Project IAM policy changed by a human principal
requirement: Detect privilege changes made outside the IaC pipeline (persistence / escalation)
attack: [T1098.003]          # Account Manipulation: Additional Cloud Roles
data_source: Cloud Audit Logs - Admin Activity (always on, _Required, 400 days)
logic: methodName=SetIamPolicy on a project AND principal is not a service account
known_false_positives: break-glass admins during approved changes; lab exercises
test: grant roles/viewer to a test service account with gcloud as a user
severity: medium
runbook: Confirm a change ticket; diff the policy (protoPayload.serviceData.policyDelta); if unapproved, revert and open an incident (module 23)
owner: you
EOF

cat > detections/gcp_log_sink_tamper.yaml <<'EOF'
id: GCP-LOG-001
title: Cloud Logging sink deleted or updated
requirement: Detect attempts to stop or redirect log routing
attack: [T1685.002]          # Disable or Modify Tools: Disable or Modify Cloud Log
data_source: Cloud Audit Logs - Admin Activity
logic: serviceName=logging.googleapis.com AND methodName ends with DeleteSink or UpdateSink
known_false_positives: approved logging changes via the IaC pipeline
test: create, update, and delete a throwaway sink
severity: high
runbook: Identify principal and source IP; restore sink from code; check for other T1685 activity in the same window
owner: you
EOF
ls detections
```

Research step: open [ATT&CK DET0289](https://attack.mitre.org/detectionstrategies/DET0289/) (the Detection Strategy for disabling cloud logs) and compare its IaaS analytic with your spec. What log sources does it list that you haven't covered?

### A2. Hunt first: does history already contain hits? (CLI)

Your earlier labs created exactly these events. Write the logic as Logging query language and run it over the last 30 days:

```bash
IAM_FILTER="logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.methodName=\"SetIamPolicy\" AND protoPayload.serviceName=\"cloudresourcemanager.googleapis.com\" AND NOT protoPayload.authenticationInfo.principalEmail:\"gserviceaccount.com\""
SINK_FILTER="logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.serviceName=\"logging.googleapis.com\" AND (protoPayload.methodName:\"DeleteSink\" OR protoPayload.methodName:\"UpdateSink\")"

gcloud logging read "$IAM_FILTER" --freshness=30d --limit=10 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.requestMetadata.callerSuppliedUserAgent.slice(0:40))"
gcloud logging read "$SINK_FILTER" --freshness=30d --limit=10 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

**What you should see:** `SetIamPolicy` rows from labs 14, 18, 21 (and `DeleteSink` from lab 18, if it was within 30 days). Every one is a "true positive" for the logic and a "benign" in context — your own lab work. That's the tuning problem in miniature: the logic is right, and context (change tickets, the pipeline identity) decides. Note the **full `methodName`** string for `DeleteSink` — you'll need it for YARA-L in A6.

### A3. Deploy as log-based alerting policies (CLI)

Deploy before you emulate, so the emulation proves the deployed rule works. No notification channel is needed for the lab — incidents appear in the console.

```bash
for D in iam sink; do
  if [ $D = iam ]; then F="$IAM_FILTER"; N="lab22 GCP-IAM-001 human IAM change"; else F="$SINK_FILTER"; N="lab22 GCP-LOG-001 sink tamper"; fi
  jq -n --arg n "$N" --arg f "$F" '{
    displayName: $n, combiner: "OR",
    conditions: [{displayName: $n, conditionMatchedLog: {filter: $f}}],
    alertStrategy: {notificationRateLimit: {period: "300s"}, autoClose: "1800s"},
    documentation: {content: "Runbook: see ~/lab22/detections. Confirm change ticket; if unapproved, open incident (module 23).", mimeType: "text/markdown"}
  }' > policy-$D.json
  gcloud monitoring policies create --policy-from-file=policy-$D.json
done
gcloud monitoring policies list --filter="displayName~^lab22" --format="table(displayName,enabled)"
```

Using `jq` to build the JSON avoids quoting mistakes in the filters — the same reason detection-as-code repos generate SIEM payloads from specs instead of hand-editing them.

### A4. Emulate: generate true positives (CLI)

```bash
gcloud iam service-accounts create lab22-sa --display-name="lab22 test principal"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:lab22-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/viewer --condition=None

gcloud logging sinks create lab22-sink \
  logging.googleapis.com/projects/$PROJECT_ID/locations/global/buckets/_Default \
  --log-filter='logName:"lab22-nothing-matches-this"'
gcloud logging sinks update lab22-sink --log-filter='logName:"lab22-still-nothing"'
gcloud logging sinks delete lab22-sink --quiet
```

The sink routes nothing (its filter matches no logs) — it exists only so you can update and delete it.

Wait 2–5 minutes, then check: Console → **Monitoring → Alerting → Incidents**. You should see one incident for each policy.

```bash
gcloud logging read "$SINK_FILTER" --freshness=15m --limit=5 --format="table(timestamp,protoPayload.methodName)"
```

**What you should see:** `UpdateSink` and `DeleteSink` (both match), and incidents opened by both alerting policies. You've closed the loop: requirement → logic → deployed rule → emulated behavior → alert. Record the incident timestamps against the event timestamps — that gap is your **detection latency**.

### A5. Tune: add a documented exclusion (your notes)

Suppose the IaC pipeline runs as `terraform-ci@PROJECT_ID.iam.gserviceaccount.com`. GCP-IAM-001 already excludes all service accounts — too broad, because stolen service-account credentials are the most common cloud attacker identity (T1078.004). Rewrite the spec's `logic` so it excludes only the named pipeline service account *and* requires the Terraform user agent, and write one sentence in `known_false_positives` justifying it. (You don't need to redeploy.)

### A6. Translate (your notes, then compare)

In `~/lab22/translations.md`, write:

1. **YARA-L** for GCP-LOG-001 using `metadata.vendor_name`, `metadata.product_event_type` (holds the `methodName` you noted in A2), `principal.user.email_addresses`, a `match` window, and `condition: $e`.
2. **KQL** for GCP-IAM-001 against Sentinel's `GCPAuditLogs` table (`MethodName`, `PrincipalEmail`, `ServiceName`, `ProjectId`).
3. **SPL** for either one, the way you'd write it in Splunk.

Then compare yours with the README's example detections. Differences in field names are the whole lesson: the *logic* ports; the *schema* doesn't.

---

## Part B — Azure (optional): run KQL for real

Azure Cloud Shell (Bash), as `labadmin`. This mirrors module 18's Part C.

```bash
az group create -n lab22-rg -l eastus --tags lab=22
az monitor log-analytics workspace create -g lab22-rg -n lab22-law -l eastus
```

Portal → **Monitor → Activity log → Export Activity Logs → Add diagnostic setting**: name `lab22-diag`, categories **Administrative** and **Security**, destination the `lab22-law` workspace → Save.

Emulate a privilege change (T1098.003) — give yourself an extra, harmless role on the lab resource group:

```bash
UPN=$(az ad signed-in-user show --query userPrincipalName -o tsv)
RG_ID=$(az group show -n lab22-rg --query id -o tsv)
az role assignment create --assignee "$UPN" --role Reader --scope "$RG_ID"
```

Wait ~10–15 minutes for ingestion, then in the workspace's **Logs** blade run the README's KQL example 3:

```kusto
AzureActivity
| where TimeGenerated > ago(2h)
| where OperationNameValue =~ "MICROSOFT.AUTHORIZATION/ROLEASSIGNMENTS/WRITE"
| where ActivityStatusValue =~ "Success"
| project TimeGenerated, Caller, CallerIpAddress, _ResourceId
```

Then make it behavioral — who changed roles more than once in an hour?

```kusto
AzureActivity
| where TimeGenerated > ago(1d)
| where OperationNameValue has "ROLEASSIGNMENTS"
| summarize Changes = count(), Ops = make_set(OperationNameValue) by Caller, bin(TimeGenerated, 1h)
| where Changes > 1
```

**What you should see:** your role assignment, with your UPN as `Caller`. **SPL bridge:** `summarize … by` is `stats … by`; `make_set` is `values()`; `bin()` is `bin _time span=1h`. Don't save it as a scheduled alert rule (billed) and don't enable Sentinel's trial for this lab — the query is the skill.

## Part C — AWS (optional): hunt in Event history, unit-test a detection

AWS CloudShell, as `labadmin`.

**C1. Hunt: console sign-ins and their MFA status (free, 90 days).**

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 20 --output json \
  | jq -r '.Events[].CloudTrailEvent | fromjson
      | [.eventTime, .userIdentity.type, (.userIdentity.arn // "-"), .responseElements.ConsoleLogin, .additionalEventData.MFAUsed, .sourceIPAddress] | @tsv'
```

**What you should see:** your `labadmin` sign-ins with `MFAUsed` = `Yes` (module 00 put MFA on it). A `No` on an `IAMUser` or `Root` row is exactly what README AWS example 1 alerts on.

**C2. Emulate and find an IAM change.**

```bash
aws iam create-user --user-name lab22-canary --tags Key=lab,Value=22
aws iam delete-user --user-name lab22-canary
sleep 300   # Event history can take several minutes
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=iam.amazonaws.com \
  --max-results 10 --query 'Events[].[EventTime,EventName,Username]' --output table
```

**C3. Unit-test a detection pattern without deploying anything.** `test-event-pattern` checks whether an EventBridge pattern matches a sample event — a free API call, and exactly the kind of test a detection-as-code pipeline runs on every change:

```bash
cat > pattern.json <<'EOF'
{"source":["aws.cloudtrail"],"detail-type":["AWS API Call via CloudTrail"],
 "detail":{"eventSource":["cloudtrail.amazonaws.com"],"eventName":["StopLogging","DeleteTrail","UpdateTrail","PutEventSelectors"]}}
EOF
for EV in StopLogging DescribeTrails; do
cat > event.json <<EOF
{"id":"11111111-2222-3333-4444-555555555555","detail-type":"AWS API Call via CloudTrail","source":"aws.cloudtrail",
 "account":"123456789012","time":"2026-10-28T12:00:00Z","region":"us-east-1","resources":[],
 "detail":{"eventSource":"cloudtrail.amazonaws.com","eventName":"$EV"}}
EOF
echo -n "$EV -> "; aws events test-event-pattern --event-pattern file://pattern.json --event file://event.json --query Result
done
```

**What you should see:** `StopLogging -> true`, `DescribeTrails -> false`. One positive and one negative test case — the minimum any rule should ship with.

---

## Verify it worked

| Check | Expected |
|---|---|
| Specs | Two YAML detection specs with ATT&CK, data source, tests, runbook |
| Hunt | Historical `SetIamPolicy` (and possibly `DeleteSink`) from earlier labs |
| Deploy | Two `lab22` alerting policies enabled |
| Emulate | Incidents for both policies; you measured detection latency |
| Translate | YARA-L, KQL, SPL versions written |
| (B) Azure | KQL returns your role assignment |
| (C) AWS | MFA status per sign-in; `true`/`false` pattern tests |

## What to notice (reflection questions)

1. Your hunt found "true positives" that were benign. What data would let a rule tell an approved change from an unapproved one automatically?
2. What was your detection latency, and what parts of the path (log write, alert evaluation) contribute to it? Is it acceptable for T1685.002?
3. Excluding all service accounts made GCP-IAM-001 quiet but blind. Write the narrowest exclusion that still lets the pipeline work.
4. Which of today's detections would survive an attacker who uses a different tool (console vs gcloud vs Terraform)? Which field made it brittle or robust?
5. If this agency moved from Splunk to Google SecOps, which artifacts from today would carry over unchanged (specs, tests, ATT&CK tags) and which would be rewritten?

## Cleanup

**Google Cloud**

```bash
for p in $(gcloud monitoring policies list --filter="displayName~^lab22" --format="value(name)"); do gcloud monitoring policies delete $p --quiet; done
gcloud projects remove-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:lab22-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/viewer --condition=None
gcloud iam service-accounts delete lab22-sa@$PROJECT_ID.iam.gserviceaccount.com --quiet
gcloud logging sinks list --format="value(name)" | grep lab22 || echo "no lab22 sinks"
gcloud monitoring policies list --filter="displayName~^lab22" --format="value(displayName)" || true
```

Keep `~/lab22/detections` and `translations.md` — download them (Cloud Shell **⋮ → Download**) as lab evidence; they contain no secrets. Then `rm -rf ~/lab22`.

**Azure**

```bash
az role assignment delete --assignee "$UPN" --role Reader --scope "$RG_ID"
az group delete -n lab22-rg --yes --no-wait
```

Then delete the subscription diagnostic setting in the portal: **Monitor → Activity log → Export Activity Logs → lab22-diag → Delete** (it isn't inside the resource group).

**AWS:** `rm -f pattern.json event.json`; confirm `aws iam get-user --user-name lab22-canary` returns `NoSuchEntity`.

**Final check — nothing billable remains:** no `lab22` alerting policies, SA, or sink; no `lab22-rg`, `lab22-diag`, or extra role assignment; no `lab22-canary` IAM user.

## Write-up prompt

> On [date] I practiced cloud detection engineering in a personal lab. I wrote two detection specifications as code (human IAM policy changes, mapped to ATT&CK T1098.003, and log-sink tampering, T1685.002), hunted for matching events in 30 days of Google Cloud Admin Activity audit logs, deployed both as Cloud Monitoring log-based alerting policies, emulated each behavior to confirm the alerts fired, and measured detection latency. I tuned one rule's exclusions and translated the logic into YARA-L (Google SecOps), KQL (Microsoft Sentinel), and SPL. [Optional: I ran KQL detections against the Azure Activity log in a Log Analytics workspace, hunted CloudTrail Event history for console sign-ins without MFA, and unit-tested an EventBridge detection pattern with positive and negative cases.] I removed all lab resources afterward.
