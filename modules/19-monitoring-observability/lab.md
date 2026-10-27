# 19 Lab — Watch a service like SRE and SOC at once: uptime check, alerts, a dashboard, and an SLO on paper

**Cost:** $0 expected on Google Cloud. Uptime checks get **1 million executions free per project per month** (this lab uses a few thousand); **alerting policies aren't charged** before September 2027; email notifications are free; dashboards are free; one log-based metric produces a few KB against the 150 MiB/month free chargeable-metric allotment; the Cloud Run sample service stays inside Cloud Run's free tier. AWS (optional): one custom metric, one alarm, and one SNS email subscription — all inside CloudWatch's free tier (10 custom metrics, 10 alarm metrics). Azure (optional): one action group and one activity log alert ⚠️ (Azure lists activity log alerts as billable; expect $0 or cents for an hour — current price not confirmed). · **Time:** 90 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Deploy a small public web service and put an **uptime check** on it.
2. Create an **email notification channel** and two **alerting policies**: an ops alert (uptime failure) and a security alert (IAM change, log-based).
3. Create a **log-based metric** and a **dashboard from JSON**.
4. Make one change that trips **both** alerts — and see where ops and security monitoring meet.
5. Compute an **SLI, SLO, and error budget** from the service's real request metrics.
6. (Optional) Build a missing-heartbeat alarm in CloudWatch and a role-assignment alert in Azure.

## Prerequisites

- Modules 00–18 done; budget alerts active.
- Cloud Shell, lab project selected; an email address you can check during the lab.

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
SVC=lab19-web
EMAIL=you@example.com          # <-- edit
gcloud services enable run.googleapis.com monitoring.googleapis.com logging.googleapis.com
```

---

## Part A — Google Cloud

### A1. A public sample service (CLI)

```bash
gcloud run deploy $SVC --image=us-docker.pkg.dev/cloudrun/container/hello \
  --region=$REGION --allow-unauthenticated --max-instances=2 --labels=lab=19
URL=$(gcloud run services describe $SVC --region=$REGION --format="value(status.url)")
HOST=${URL#https://}; echo $HOST
for i in $(seq 1 50); do curl -s -o /dev/null $URL; done
```

**Why public here?** An uptime check is a **black-box** probe from the internet, so the target must be reachable. This is Google's static sample page with no data and a two-instance ceiling, and you'll delete it at the end. (For private services, Google offers **private uptime checks** — and for Assured Workloads/IL4 boundaries, Google says not to use public uptime checks at all.)

### A2. Uptime check (console tour, then CLI)

Console tour: **Monitoring → Uptime checks → Create uptime check**. Note protocol, resource type (URL, Cloud Run, load balancer…), check frequency, **regions** (minimum 3), response validation, and the option to create an alert. Cancel; use the CLI:

```bash
gcloud monitoring uptime create lab19-uptime \
  --resource-type=uptime-url --resource-labels=host=$HOST,project_id=$PROJECT_ID \
  --protocol=https --path=/ --period=5 --timeout=10
gcloud monitoring uptime list-configs --format="table(displayName,name.basename(),period,selectedRegions)"
UPTIME_ID=$(gcloud monitoring uptime list-configs --filter="displayName=lab19-uptime" --format="value(name.basename())"); echo $UPTIME_ID
```

After ~5 minutes, **Monitoring → Uptime checks → lab19-uptime** shows green results per region.

### A3. Email notification channel (console)

**Monitoring → Alerting → Edit notification channels → Email → Add new**: your email, display name `lab19-email` → Save. Then get its ID:

```bash
gcloud beta monitoring channels list --format="table(displayName,name)"
CHANNEL=$(gcloud beta monitoring channels list --filter="displayName=lab19-email" --format="value(name)"); echo $CHANNEL
```

(Notification-channel commands are in `gcloud beta`; Cloud Shell includes it.)

### A4. Two alerting policies: one ops, one security (CLI)

**Ops — uptime failure.** The uptime check writes the metric `monitoring.googleapis.com/uptime_check/check_passed`; alert when it fails from more than one region:

```bash
cat > uptime-policy.json <<EOF
{
  "displayName": "lab19 OPS: site down",
  "combiner": "OR",
  "conditions": [{
    "displayName": "Uptime check failing",
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"$UPTIME_ID\" AND resource.type=\"uptime_url\"",
      "aggregations": [{"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_NEXT_OLDER", "crossSeriesReducer": "REDUCE_COUNT_FALSE", "groupByFields": ["resource.label.host"]}],
      "comparison": "COMPARISON_GT", "thresholdValue": 1, "duration": "0s",
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["$CHANNEL"],
  "documentation": {"content": "lab19: the public site failed uptime checks from 2+ regions. Check recent IAM and deploy changes first.", "mimeType": "text/markdown"}
}
EOF
gcloud monitoring policies create --policy-from-file=uptime-policy.json
```

This mirrors the policy the console builds when you click **Create alert** on an uptime check ⚠️ (if the CLI rejects a field, create it from the console instead: **Uptime checks → lab19-uptime → Create alert** and attach `lab19-email`).

**Security — IAM change on the service (log-based alert).**

```bash
cat > iam-policy.json <<EOF
{
  "displayName": "lab19 SEC: Cloud Run IAM changed",
  "combiner": "OR",
  "conditions": [{
    "displayName": "SetIamPolicy on Cloud Run",
    "conditionMatchedLog": {
      "filter": "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.serviceName=\"run.googleapis.com\" AND protoPayload.methodName:\"SetIamPolicy\""
    }
  }],
  "alertStrategy": {"notificationRateLimit": {"period": "300s"}, "autoClose": "1800s"},
  "notificationChannels": ["$CHANNEL"],
  "documentation": {"content": "lab19: someone changed who can invoke a Cloud Run service. Verify the principal and change ticket.", "mimeType": "text/markdown"}
}
EOF
gcloud monitoring policies create --policy-from-file=iam-policy.json
gcloud monitoring policies list --format="table(displayName,enabled,name.basename())"
```

**What you should see:** both policies listed and enabled. The second one is a **security detection built in the ops tool** — the same pattern as AWS's CIS CloudWatch.4 control (IAM policy changes) and Google's documented secret-access alerts.

### A5. A log-based metric and a dashboard from JSON (CLI)

```bash
gcloud logging metrics create lab19_iam_changes \
  --description="Count of IAM policy changes in this project" \
  --log-filter="logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.methodName:\"SetIamPolicy\""

cat > dash.json <<'EOF'
{
  "displayName": "lab19 golden signals + security",
  "gridLayout": { "columns": "2", "widgets": [
    { "title": "Requests/s by response class (traffic + errors)",
      "xyChart": { "dataSets": [{ "plotType": "STACKED_BAR", "timeSeriesQuery": { "timeSeriesFilter": {
        "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"lab19-web\"",
        "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_RATE", "crossSeriesReducer": "REDUCE_SUM", "groupByFields": ["metric.label.response_code_class"] } } } }] } },
    { "title": "Request latency p95 (latency)",
      "xyChart": { "dataSets": [{ "plotType": "LINE", "timeSeriesQuery": { "timeSeriesFilter": {
        "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"lab19-web\"",
        "aggregation": { "alignmentPeriod": "60s", "perSeriesAligner": "ALIGN_PERCENTILE_95" } } } }] } },
    { "title": "IAM policy changes (security)",
      "xyChart": { "dataSets": [{ "plotType": "STACKED_BAR", "timeSeriesQuery": { "timeSeriesFilter": {
        "filter": "metric.type=\"logging.googleapis.com/user/lab19_iam_changes\"",
        "aggregation": { "alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_SUM", "crossSeriesReducer": "REDUCE_SUM" } } } }] } },
    { "title": "Uptime check pass ratio (black-box)",
      "xyChart": { "dataSets": [{ "plotType": "LINE", "timeSeriesQuery": { "timeSeriesFilter": {
        "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" resource.type=\"uptime_url\"",
        "aggregation": { "alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_FRACTION_TRUE", "crossSeriesReducer": "REDUCE_MEAN" } } } }] } }
  ] }
}
EOF
gcloud monitoring dashboards create --config-from-file=dash.json --validate-only && \
gcloud monitoring dashboards create --config-from-file=dash.json
```

Open **Monitoring → Dashboards → lab19 golden signals + security**. Three golden signals (traffic, errors, latency) plus a security counter on one screen. (Saturation — instance count or CPU — is the fourth; add it from the console as a stretch.) ⚠️ If `--validate-only` reports a field error, fix that widget or build it in the console; the JSON shape follows the Dashboards API reference.

### A6. One change, two alerts (CLI)

Simulate a well-meaning admin "locking down" the service — or an attacker cutting off public access:

```bash
gcloud run services remove-iam-policy-binding $SVC --region=$REGION \
  --member=allUsers --role=roles/run.invoker
curl -s -o /dev/null -w "%{http_code}\n" $URL     # 403
```

Within a few minutes you should get **two emails**: the **SEC** alert (log-based, usually within a few minutes) and, after the next uptime runs, the **OPS** alert (site down from 2+ regions; can take 5–10 minutes). Open **Monitoring → Alerting** to see both incidents. The dashboard's IAM counter ticks up and the uptime ratio drops.

**The point:** one action, two teams' alerts. The SOC sees *who* changed access; SRE sees *impact*. Neither alone tells the whole story.

Restore it:

```bash
gcloud run services add-iam-policy-binding $SVC --region=$REGION \
  --member=allUsers --role=roles/run.invoker
```

(That's another `SetIamPolicy` — expect another SEC email after the 5-minute rate limit.)

### A7. SLI, SLO, and error budget — with real numbers (console + arithmetic)

Generate some mixed traffic, including errors:

```bash
for i in $(seq 1 300); do curl -s -o /dev/null $URL; done
for i in $(seq 1 6); do curl -s -o /dev/null "$URL/does-not-exist-$i"; done   # 404s (4xx)
```

**Metrics Explorer** → metric **Cloud Run Revision → Request Count**, filter `service_name = lab19-web`, group by `response_code_class`, aggregation **sum**, last hour. Read the totals.

Now, on paper:

1. **SLI definition:** "proportion of requests that did *not* return 5xx." (Why exclude 4xx? Those are usually the client's fault — decide deliberately.)
2. **Your SLI value** = non-5xx ÷ total for the hour.
3. **SLO:** 99.5% over 28 days. If the service handled 2,000,000 requests in 28 days, the **error budget** is `0.005 × 2,000,000 = 10,000` bad requests.
4. **Burn rate:** if A6 had caused 5xx (it caused 403s — client errors, which this SLI ignores) at 50% of 1,000 requests/hour for 2 hours, how much budget is gone? (1,000 bad requests = 10% of the month's budget in 2 hours ≈ a **fast burn** worth paging on.)
5. Notice: A6 made users fail with **403**, which your 5xx-based SLI **didn't count**. The uptime check caught it. That's why black-box checks complement request-based SLIs — and why SLI definitions are a design decision.

(Cloud Monitoring's **Services → Define service** builds SLOs and burn-rate alerts on custom or supported services ⚠️ automatic Cloud Run support wasn't confirmed this run; the arithmetic is the skill.)

---

## Part B — AWS (optional): alert on a missing heartbeat

CloudShell, as `labadmin`. You'll confirm an SNS email subscription.

```bash
TOPIC=$(aws sns create-topic --name lab19-alerts --tags Key=lab,Value=19 --query TopicArn --output text)
aws sns subscribe --topic-arn $TOPIC --protocol email --notification-endpoint you@example.com   # <-- edit; click the link in the email
for i in 1 2 3; do aws cloudwatch put-metric-data --namespace Lab19 --metric-name Heartbeat --value 1; sleep 20; done
aws cloudwatch put-metric-alarm --alarm-name lab19-heartbeat-missing \
  --namespace Lab19 --metric-name Heartbeat --statistic Sum --period 300 \
  --evaluation-periods 1 --threshold 1 --comparison-operator LessThanThreshold \
  --treat-missing-data breaching --alarm-actions $TOPIC
aws cloudwatch describe-alarms --alarm-names lab19-heartbeat-missing --query 'MetricAlarms[].StateValue'
```

Stop sending heartbeats. Within ~10 minutes the alarm goes to **ALARM** and you get an email. That's a **metric-absence** alert — the pattern that catches a disabled agent, pipeline, or log source (T1685.002). Compare with the Security Hub **CloudWatch.1–14** controls, which expect CIS metric filters + alarms on CloudTrail events (this needs a trail delivering to CloudWatch Logs — not built here to keep it free).

## Part C — Azure (optional): alert on privileged role assignments

Azure Cloud Shell (Bash), as `labadmin`.

```bash
RG=lab19-rg; az group create -n $RG -l eastus --tags lab=19
SUB=$(az account show --query id -o tsv)
AG=$(az monitor action-group create -n lab19-ag -g $RG --short-name lab19 \
  --action email me you@example.com --query id -o tsv)          # <-- edit email
az monitor activity-log alert create -n lab19-role-assign -g $RG --scope /subscriptions/$SUB \
  --condition category=Administrative and operationName=Microsoft.Authorization/roleAssignments/write \
  -a $AG --description "lab19: role assignment created"
# Trigger it: give yourself Reader on the lab resource group (harmless)
az role assignment create --assignee $(az ad signed-in-user show --query id -o tsv) --role Reader \
  --scope $(az group show -n $RG --query id -o tsv)
```

**What you should see:** an email from Azure Monitor within several minutes naming the role-assignment write. This is the alert Microsoft documents for privileged role assignments — a security detection built from Activity Log and an action group.

---

## Verify it worked

| Check | Expected |
|---|---|
| Uptime check | Passing from 3+ regions before A6 |
| Policies | `lab19 OPS: site down` and `lab19 SEC: Cloud Run IAM changed` enabled |
| Dashboard | Traffic/errors, latency, IAM changes, uptime ratio widgets |
| A6 | 403 to curl; SEC email, then OPS email; IAM counter up |
| SLI arithmetic | Non-5xx ratio computed; budget = 0.5% of requests |
| (B) AWS | Alarm `ALARM` after heartbeats stop; email received |
| (C) Azure | Activity log alert email on role assignment |

## What to notice (reflection questions)

1. Which alert told you *what changed and who did it*, and which told you *users were affected*? Who should receive each?
2. Your 5xx-based SLI didn't notice the 403 outage. Rewrite the SLI so it would, and explain the trade-off.
3. If an attacker deleted your alerting policies, where would that show up? (Hint: module 18.) What would catch it if nobody looked at that log?
4. Cryptomining would show up on which of today's signals, and on which billing signal from module 04?
5. Google warns against public uptime checks for Assured Workloads/IL4 boundaries. How would you monitor availability for a service inside one?

## Cleanup

**Google Cloud**

```bash
for p in $(gcloud monitoring policies list --filter="displayName~^lab19" --format="value(name)"); do gcloud monitoring policies delete $p --quiet; done
gcloud monitoring uptime delete $UPTIME_ID --quiet
for d in $(gcloud monitoring dashboards list --filter="displayName~^lab19" --format="value(name)"); do gcloud monitoring dashboards delete $d --quiet; done
gcloud logging metrics delete lab19_iam_changes --quiet
gcloud beta monitoring channels delete $CHANNEL --force --quiet
gcloud run services delete $SVC --region=$REGION --quiet
rm -f uptime-policy.json iam-policy.json dash.json
gcloud monitoring policies list --format="value(displayName)" | grep lab19 || echo "no lab19 policies"
gcloud monitoring uptime list-configs --format="value(displayName)" | grep lab19 || echo "no lab19 uptime checks"
gcloud run services list --region=$REGION --format="value(metadata.name)" | grep lab19 || echo "no lab19 services"
```

⚠️ If `channels delete` rejects `--force`, delete the channel in **Alerting → Edit notification channels**. Deleting the uptime check matters most: it would otherwise keep running (free within the allowance, but it would probe a deleted URL and generate failing checks).

**AWS**

```bash
aws cloudwatch delete-alarms --alarm-names lab19-heartbeat-missing
aws sns delete-topic --topic-arn $TOPIC
aws cloudwatch describe-alarms --alarm-name-prefix lab19 --query 'MetricAlarms[].AlarmName'   # expect []
```

The `Lab19/Heartbeat` custom metric expires on its own once no new data arrives ⚠️ (CloudWatch doesn't offer metric deletion; custom metrics bill only in months they receive data — confirm on the pricing page).

**Azure**

```bash
az role assignment delete --assignee $(az ad signed-in-user show --query id -o tsv) --role Reader \
  --scope $(az group show -n $RG --query id -o tsv)
az group delete -n $RG --yes --no-wait     # removes the action group and the activity log alert (both live in lab19-rg)
```

**Final check — nothing billable remains:** no `lab19` alerting policies, uptime check, dashboard, log-based metric, notification channel, or Cloud Run service; no `lab19` CloudWatch alarm or SNS topic; `lab19-rg` deleted.

## Write-up prompt

> On [date] I configured Google Cloud Monitoring for a Cloud Run service in a personal lab: a multi-region HTTPS uptime check, an email notification channel, an uptime-failure alerting policy, and a log-based alerting policy on Cloud Run IAM changes from Admin Activity audit logs. I created a log-based metric and a JSON-defined dashboard showing traffic, errors, latency, uptime, and IAM-change counts. I removed public access to the service and observed both the security alert (who changed access) and the operational alert (site unavailable) fire, then defined an SLI and SLO and calculated an error budget and burn rate from the service's request metrics. [Optional: I built a CloudWatch missing-heartbeat alarm with SNS email notification and an Azure Monitor activity log alert on role assignments.] I deleted all resources afterward.
