# 04 Lab — Make the bill readable, wire an alarm to code, and find your ceilings

**Cost:** $0 expected. Pub/Sub topics and a few small messages fall well inside Pub/Sub's free 10 GiB/month. Budgets, labels, quota views, anomaly settings, and billing reports are free. The optional BigQuery billing export stores a tiny amount of data inside BigQuery's free tier (10 GiB storage, 1 TiB queries per month). AWS: one SNS topic with no subscribers and console configuration only. Azure: one empty resource group. · **Time:** 75–90 min (plus a next-day check) · **Clouds:** GCP (required), AWS and Azure (parallels)

## Goal

1. See how a charge is labeled, grouped, and reported.
2. Send budget status to Pub/Sub — the hook any automated response would use — and read the message yourself.
3. Understand, without deploying it, why a billing kill switch is dangerous.
4. Find the quotas that cap what you (or an intruder) can launch.
5. Do the AWS and Azure equivalents: activate a cost-allocation tag, look at a budget action, create an anomaly monitor.

## Prerequisites

- Modules 00–03 complete; the $10 budgets from module 00 exist on all three clouds.
- Google Cloud: a lab project with billing linked, `gcloud config list` showing it. You need **Billing Account Administrator** (or Costs Manager) on the billing account — you have it if you created the trial.
- Azure: an active subscription (module 00's trial-cliff box: after day 30 you must have upgraded).

```bash
gcloud config list
PROJECT_ID=$(gcloud config get-value project)
BILLING_ID=$(gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)" | sed 's#billingAccounts/##')
echo $PROJECT_ID $BILLING_ID
```

---

## Part A — Google Cloud

### A1. Who pays for this project? (CLI)

```bash
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID
```

**Notice:** `billingEnabled: true` and the `billingAccountName`. That one link is what makes every resource in the project billable — and unlinking it is what the kill-switch pattern does.

### A2. Label a resource (console, then CLI)

You'll create a free Pub/Sub topic and use it twice: as a labeled resource, and as the budget's notification target.

Console: **Pub/Sub → Topics → Create topic** → ID `lab04-budget-alerts` → uncheck "Add a default subscription" → **Labels**: `lab=04`, `cost-center=training` → Create.

CLI (use either, not both):

```bash
gcloud services enable pubsub.googleapis.com billingbudgets.googleapis.com
gcloud pubsub topics create lab04-budget-alerts --labels=lab=04,cost-center=training
gcloud pubsub subscriptions create lab04-budget-sub \
  --topic=lab04-budget-alerts --labels=lab=04 --expiration-period=7d
gcloud pubsub topics describe lab04-budget-alerts --format="yaml(labels)"
```

Label rules to remember: lowercase keys starting with a letter; letters, numbers, `_`, `-`; up to 64 per resource. Try `--labels=Cost-Center=Training` and read the error.

`--expiration-period=7d` makes the subscription delete itself after a week of inactivity — a cleanup safety net.

### A3. A budget that talks to code (CLI)

This budget is scoped to just this project, tiny on purpose, and publishes status to your topic.

```bash
gcloud billing budgets create \
  --billing-account=$BILLING_ID \
  --display-name="lab04-project-1usd" \
  --budget-amount=1USD \
  --filter-projects=projects/$PROJECT_ID \
  --credit-types-treatment=exclude-all-credits \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=1.0 \
  --threshold-rule=percent=1.0,basis=forecasted-spend \
  --notifications-rule-pubsub-topic=projects/$PROJECT_ID/topics/lab04-budget-alerts

gcloud billing budgets list --billing-account=$BILLING_ID \
  --format="table(name.basename(),displayName,amount.specifiedAmount.units)"
```

Console equivalent: **Billing → Budgets & alerts → Create budget** → scope: this project → amount $1 → thresholds → **Manage notifications → Connect a Pub/Sub topic to this budget**.

Why exclude credits? Same reason as module 00: with the $300 credit counted, your net cost is $0 and nothing ever fires.

### A4. Read what the budget says (CLI — wait a few hours)

Google sends budget notifications "multiple times per day," and the first can take several hours. Come back later and pull:

```bash
gcloud pubsub subscriptions pull lab04-budget-sub --auto-ack --limit=3
```

The **DATA** column holds the message body. If it looks like base64 (a long run of letters with no spaces), decode it with `echo '<paste>' | base64 -d`.

**What you should see:** JSON with `budgetDisplayName`, `costAmount`, `budgetAmount`, `currencyCode`, and `costIntervalStart`. If a threshold has been crossed, `alertThresholdExceeded` appears (e.g., `0.5`). If nothing arrives after a day, check that the budget shows the topic under **Manage notifications**.

This message is the **input** to any automated response. Everything else is code you'd write.

### A5. Read — don't deploy — the kill switch

Open Google's [Disable billing usage with notifications](https://docs.cloud.google.com/billing/docs/how-to/disable-billing-with-notifications) page and answer in your notes:

1. What does the function actually do when cost exceeds budget? (It removes the billing account from the project.)
2. What does Google warn can happen to resources? (They might be irretrievably deleted.)
3. What role does the function's service account need? (Billing Account Administrator — a very powerful identity sitting in a function.)
4. Why does the sample start with `SIMULATE_DEACTIVATION = True`?

**Do not deploy it in this lab.** The point is to understand the trade: guaranteed stop vs. possible data loss and a highly privileged automation identity.

### A6. Find your ceilings: quotas (console, then CLI)

Console: **IAM & Admin → Quotas & system limits** → filter for `Compute Engine API` → look at **CPUs** and **GPUs (all regions)**.

CLI:

```bash
gcloud services enable compute.googleapis.com
gcloud compute project-info describe \
  --format="table(quotas.metric,quotas.limit,quotas.usage)" | grep -i -E "cpus|gpus|instances|addresses" | head -20

gcloud compute regions describe us-central1 \
  --format="table(quotas.metric,quotas.limit,quotas.usage)" | grep -i -E "^cpus|gpus" | head -10
```

**Notice:** quotas are per project and often per region. On a Free Trial billing account you **can't request increases**, and GPUs can't be attached at all. Ask yourself: if someone stole this project's credentials tonight, how many vCPUs could they mine with?

### A7. Reports and anomalies (console)

1. **Billing → Reports.** Group by **SKU**. Then filter **Labels → lab** to see per-lab cost (expect cents or $0 — modules 01–02 VMs were free-tier). Change the time range to "last 90 days."
2. **Billing → Anomalies** (may be labeled **Cost anomalies**). Note the notification settings: who gets emailed, and the cost-impact threshold. Leave defaults unless they email nobody.

### A8. (Optional) Billing export to BigQuery (console)

This is how FinOps teams do real analysis.

1. **BigQuery → your project → Create dataset** → ID `lab04_billing` → location `US`.
2. **Billing → Billing export → BigQuery export → Standard usage cost → Edit settings** → project = your lab project, dataset = `lab04_billing` → Save.
3. Data arrives over the following hours to a day. Tomorrow, in BigQuery, look at the new table's schema: find the `labels` and `sku` columns.

Cost: export storage and small queries sit inside BigQuery's free tier. If you're not going to keep it, do the cleanup step for A8.

---

## Part B — AWS

Sign in as `labadmin`. Region: `us-east-1`.

### B1. Make a tag show up in billing (CLI, then console)

In CloudShell:

```bash
aws sns create-topic --name lab04-tag-demo --tags Key=cost-center,Value=training Key=lab,Value=04
```

An SNS topic with no subscribers costs nothing to exist.

Console: **Billing and Cost Management → Cost allocation tags → User-defined cost allocation tags.** The `cost-center` key won't be there yet — AWS says it can take **up to 24 hours** to appear and **another 24** to activate. Come back tomorrow, select it, and choose **Activate**.

**The lesson:** a tag that isn't activated doesn't exist as far as billing reports are concerned.

### B2. Look inside a budget action (console, don't save)

**Budgets → lab budget from module 00 → Actions → Add action.** Walk through the options — **IAM policy**, **SCP**, **Automate instance to stop (EC2 or RDS)** — and note that each needs an IAM role AWS Budgets can assume, plus a choice between automatic and approval-required. **Cancel** without saving.

(SCP actions need AWS Organizations, which would end your free plan — module 00.)

### B3. Cost Anomaly Detection (console)

**Billing and Cost Management → Cost Anomaly Detection → Create monitor** → type **AWS services** → name `lab04-services` → alert subscription: **daily summary** to your lab email, threshold **$1 absolute**. ⚠️ AWS's getting-started page doesn't state a price; check the pricing note on the console page before creating.

### B4. Service quotas (CLI)

```bash
aws service-quotas list-service-quotas --service-code ec2 \
  --query "Quotas[?contains(QuotaName,'On-Demand')].[QuotaName,Value]" --output table
```

**Notice:** EC2 quotas are expressed in **vCPUs** per instance family group, per Region.

---

## Part C — Azure

Azure Cloud Shell (ephemeral, Bash), signed in as `labadmin`.

### C1. Tags on a resource group (CLI)

```bash
az group create --name rg-lab04 --location eastus --tags lab=04 cost-center=training
az group show --name rg-lab04 --query tags
```

### C2. A resource-group budget (console)

**Cost Management → Budgets → Add** → scope **rg-lab04** → $1/month → alerts: 50% actual, 100% forecasted → your lab email. Look at the **action group** option: this is where automation would hook in. Leave it empty.

### C3. Anomaly alert (console)

**Cost Management** (subscription scope) → **Cost alerts → Add** → **Alert type: Anomaly** → your lab email → Create. Microsoft notes anomaly alerts are subscription-scope only and up to five per subscription.

### C4. Tag inheritance (console — if your account offers it)

**Cost Management** (subscription scope) → **Settings → Manage subscription → Tag inheritance → Edit**. Microsoft documents this for EA, MCA, and MPA accounts; if your free account doesn't show it, note that and move on. It copies subscription/RG tags onto **usage records**, not onto resources.

### C5. Quotas (CLI)

```bash
az vm list-usage --location eastus -o table | head -20
```

**Notice:** "Total Regional vCPUs" and per-family vCPU limits.

---

## Verify it worked

| Check | Google Cloud | AWS | Azure |
|---|---|---|---|
| Labeled resource | `topics describe` shows `lab: '04'` | SNS topic has tags | `rg-lab04` shows tags |
| Budget → code path | Pulled a budget JSON message (A4) | Saw action types (B2) | Saw action group field (C2) |
| Anomaly detection | Notification settings reviewed | Monitor `lab04-services` exists | Anomaly alert rule exists |
| Quotas | Found CPU and GPU quota values | Listed On-Demand vCPU quotas | Listed regional vCPU usage |

## What to notice (reflection questions)

1. Your Google budget fired a Pub/Sub message. Write, in plain English, the three steps a function would take to *freeze* (not kill) spend in a project. What permission would it need, and why is that dangerous to hand to code?
2. Why does AWS make you activate tags before they appear in billing? What breaks if a team forgets?
3. An agency's appropriation for a program is $2M for the fiscal year. Name four controls from this lab you'd put in place, and say which ones *stop* spend versus *report* it.
4. An attacker steals a key for your project. Which of today's settings would detect them, and which would limit them? How long until you'd know?
5. In intel terms: what's the latency and reliability of billing data as a collection source?

## Cleanup

**Google Cloud**

```bash
gcloud billing budgets list --billing-account=$BILLING_ID --format="value(name,displayName)"
# copy the ID of lab04-project-1usd, then:
gcloud billing budgets delete BUDGET_ID --billing-account=$BILLING_ID

gcloud pubsub subscriptions delete lab04-budget-sub
gcloud pubsub topics delete lab04-budget-alerts
```

Keep the **module 00** `lab-monthly-10` budget — only delete `lab04-project-1usd`.

If you did **A8**: **Billing → Billing export → BigQuery export → Edit settings → Disable**, then delete the dataset:

```bash
bq rm -r -f -d $PROJECT_ID:lab04_billing
```

Confirm:

```bash
gcloud pubsub topics list --filter="name:lab04"          # expect nothing
gcloud pubsub subscriptions list --filter="name:lab04"   # expect nothing
bq ls                                                    # lab04_billing gone
gcloud billing budgets list --billing-account=$BILLING_ID --format="value(displayName)"  # only lab-monthly-10
```

**AWS**

```bash
TOPIC_ARN=$(aws sns list-topics --query "Topics[?contains(TopicArn,'lab04-tag-demo')].TopicArn" --output text)
aws sns delete-topic --topic-arn $TOPIC_ARN
aws sns list-topics --output text | grep lab04 || echo "lab04 topic gone"
```

Keep the anomaly monitor if you like it (it's a useful tripwire); otherwise **Cost Anomaly Detection → Cost monitors → lab04-services → Delete**. Leave the activated `cost-center` tag key — it's just a billing setting.

**Azure**

Delete the rg-lab04 budget in **Cost Management → Budgets**, then:

```bash
az group delete --name rg-lab04 --yes
az group list --query "[?name=='rg-lab04']" -o table   # expect empty
```

Keep or delete the anomaly alert rule (**Cost alerts → Alert rules**).

**Final check — nothing billable remains:** all three billing pages show $0.00 current-month charges for lab04 items (check Google's report filtered by `lab=04` tomorrow). Your module 00 budgets still exist.

## Write-up prompt

> On [date] I configured cost governance in personal Google Cloud, AWS, and Azure lab accounts. On Google Cloud I labeled resources for cost allocation, created a project-scoped budget that publishes programmatic notifications to Pub/Sub and read the budget JSON directly, reviewed the documented disable-billing pattern and its data-loss risk, and inspected Compute Engine quotas. On AWS I activated a user-defined cost allocation tag, reviewed Budgets action types (IAM/SCP deny, EC2/RDS stop), and created a Cost Anomaly Detection monitor. On Azure I tagged a resource group, created a resource-group budget, and set an anomaly alert. I cleaned up all lab resources.
