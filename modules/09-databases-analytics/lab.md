# 09 Lab — Hunt in BigQuery: the sandbox, cost controls, and a mini security data lake

**Cost:** $0 on Google Cloud. Part A runs in the **BigQuery sandbox** — a project with **no billing account attached** — so nothing can be charged: 10 GiB of storage over the project's lifetime, 1 TiB of query processing per month, tables expire after 60 days, and no streaming or DML. AWS (optional): one on-demand DynamoDB table with a single item for a few minutes — fractions of a cent, covered by free-plan credits. Azure (optional): an Azure SQL logical server (free) and one database on the **free offer** with auto-pause when the free limit is used — $0. · **Time:** 75–90 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Set up the **BigQuery sandbox** and query a public dataset.
2. See what a query costs **before** running it, and make an expensive query fail safely.
3. Load a small set of (synthetic) authentication logs and **hunt** in SQL — password spraying and a suspicious success.
4. Find out **who ran which query and how many bytes it scanned**.
5. (Optional) A DynamoDB table with deletion protection and PITR; an Azure SQL database with Entra-only auth and no network path.

## Prerequisites

- Modules 00–08 done.
- Google: you'll create a **new project and deliberately not link billing** — that's what makes it a sandbox.

---

## Part A — BigQuery sandbox

### A1. Create a sandbox project (console, then CLI)

Console: project picker → **New project** → name `lab09-sbx` → Create. When asked to link a billing account, **skip it**. Open **BigQuery** in that project — you should see a **SANDBOX** badge near the top.

CLI (either, not both):

```bash
SBX=lab09-sbx-$RANDOM
gcloud projects create $SBX --name="lab09-sbx" --labels=lab=09
gcloud services enable bigquery.googleapis.com --project=$SBX
gcloud billing projects describe $SBX --format="value(billingEnabled)"   # expect False (or empty)
gcloud config set project $SBX
```

**Notice:** no billing account, no credit card exposure. If you ever link billing to this project, it stops being a sandbox and the normal free tier and charges apply.

### A2. First query: read the bytes-processed number (console)

**BigQuery → SQL query** (BigQuery Studio editor). Paste:

```sql
SELECT word, SUM(word_count) AS uses
FROM `bigquery-public-data.samples.shakespeare`
GROUP BY word
ORDER BY uses DESC
LIMIT 10;
```

Before you click **Run**, look at the top right of the editor: "This query will process *N* MB when run." That's the dry-run estimate. Run it.

**Notice:** the public dataset lives in Google's `bigquery-public-data` project. Google pays to store it; you pay (here: nothing) to query it. Results tab → **Job information** shows bytes processed and bytes billed (minimum 10 MB per table referenced).

### A3. Cost control from the CLI: dry runs and a hard ceiling (CLI)

Compare two queries on a much bigger table — **without running them**:

```bash
bq query --location=US --use_legacy_sql=false --dry_run \
  'SELECT * FROM `bigquery-public-data.samples.natality`'

bq query --location=US --use_legacy_sql=false --dry_run \
  'SELECT year, AVG(weight_pounds) AS avg_lb FROM `bigquery-public-data.samples.natality` GROUP BY year'
```

**What you should see:** each prints the bytes it *would* process. `SELECT *` reads every column; the second reads two. That gap is columnar storage — and on a billed project, it's the gap in your invoice.

Now make BigQuery refuse to overspend:

```bash
bq query --location=US --use_legacy_sql=false --maximum_bytes_billed=10000000 \
  'SELECT year, AVG(weight_pounds) AS avg_lb FROM `bigquery-public-data.samples.natality` GROUP BY year'
```

**What you should see:** an error saying the query exceeded the bytes-billed limit (10 MB here), and **nothing is charged**. Raise the limit to the dry-run figure and it runs. On real projects, set this in tooling defaults and add project-level custom query quotas.

### A4. A mini security data lake: load and hunt (CLI)

Create a dataset with a short default table expiration (good hygiene even outside the sandbox):

```bash
bq --location=US mk --dataset --default_table_expiration=604800 \
  --description="lab09 synthetic auth logs" $SBX:lab09_sec
```

Generate **synthetic** sign-in logs (fake users, documentation-range IPs) in Cloud Shell:

```bash
python3 - <<'EOF'
import csv, random, datetime
random.seed(9)
users = [f"user{i:02d}" for i in range(1, 41)]
normal_ips = [f"198.51.100.{i}" for i in range(10, 40)]       # RFC 5737 documentation range
spray_ip, odd_ip = "203.0.113.66", "192.0.2.200"
t0 = datetime.datetime(2026, 10, 1, 8, 0, 0)
rows = []
for n in range(600):                                             # normal activity
    rows.append([t0 + datetime.timedelta(minutes=random.randint(0, 7*24*60)),
                 random.choice(users), random.choice(normal_ips), "US",
                 "SUCCESS" if random.random() > 0.05 else "FAILURE"])
for i, u in enumerate(users):                                    # password spray: one IP, many users
    rows.append([t0 + datetime.timedelta(days=3, minutes=i), u, spray_ip, "NL", "FAILURE"])
for k in range(6):                                               # failures, then success, unusual IP
    rows.append([t0 + datetime.timedelta(days=5, minutes=k), "user17", odd_ip, "RO",
                 "FAILURE" if k < 5 else "SUCCESS"])
rows.sort(key=lambda r: r[0])
with open("signins.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ts", "user", "src_ip", "country", "result"])
    for r in rows: w.writerow([r[0].strftime("%Y-%m-%d %H:%M:%S")] + r[1:])
print(len(rows), "rows written")
EOF

bq --location=US load --source_format=CSV --skip_leading_rows=1 \
  --schema=ts:TIMESTAMP,user:STRING,src_ip:STRING,country:STRING,result:STRING \
  lab09_sec.signins signins.csv
bq show --format=prettyjson lab09_sec.signins | grep -E '"numRows"|"expirationTime"'
```

**Hunt 1 — password spraying (one source, many accounts, all failures):**

```bash
bq query --location=US --use_legacy_sql=false '
SELECT src_ip, country,
       COUNT(DISTINCT user) AS users_tried,
       COUNTIF(result = "FAILURE") AS failures,
       MIN(ts) AS first_seen, MAX(ts) AS last_seen
FROM lab09_sec.signins
GROUP BY src_ip, country
HAVING users_tried >= 10 AND failures = COUNT(*)
ORDER BY users_tried DESC'
```

**Hunt 2 — a success right after a burst of failures, from an IP the user has never used:**

```bash
bq query --location=US --use_legacy_sql=false '
WITH scored AS (
  SELECT ts, user, src_ip, country, result,
         MIN(ts) OVER (PARTITION BY user, src_ip) AS first_use_of_ip,
         COUNTIF(result = "FAILURE") OVER (
           PARTITION BY user, src_ip ORDER BY UNIX_SECONDS(ts)
           RANGE BETWEEN 1800 PRECEDING AND CURRENT ROW) AS failures_last_30m
  FROM lab09_sec.signins
)
SELECT ts, user, src_ip, country, failures_last_30m
FROM scored
WHERE result = "SUCCESS"
  AND failures_last_30m >= 3
  AND first_use_of_ip >= TIMESTAMP_SUB(ts, INTERVAL 1 HOUR)
ORDER BY ts'
```

**What you should see:** Hunt 1 surfaces `203.0.113.66` trying all 40 users. Hunt 2 surfaces `user17` succeeding from `192.0.2.200` after five failures. That's T1110.003 (password spraying) and T1110.001 (guessing) leading to T1078 (valid accounts) — expressed in SQL instead of SPL.

**Bridge:** in Splunk you'd write `stats dc(user) by src_ip | where ...`. Same logic, different language. The difference at scale: BigQuery charges per byte scanned, so real tables get partitioned by day and every hunt gets a time filter.

### A5. A view that hides a column (CLI)

```bash
bq mk --use_legacy_sql=false \
  --view='SELECT ts, result, country FROM `'$SBX'.lab09_sec.signins`' \
  lab09_sec.signins_no_identity
bq query --location=US --use_legacy_sql=false \
  'SELECT result, COUNT(*) AS n FROM lab09_sec.signins_no_identity GROUP BY result'
```

This view drops `user` and `src_ip`. Made an **authorized view** (granted read access to the source dataset, with consumers given access only to the view's dataset), it would let a dashboard team see trends without seeing identities. You can't fully demonstrate that with one identity — just know the pattern.

### A6. Who queried what, and what did it cost? (CLI, then console)

```bash
bq query --location=US --use_legacy_sql=false '
SELECT creation_time, statement_type, total_bytes_processed, total_bytes_billed,
       error_result.reason AS error, LEFT(query, 60) AS query_start
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_USER
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY creation_time DESC
LIMIT 20'
```

**What you should see:** every query you ran today — including the one that failed on `bytesBilledLimitExceeded` (or similar) — with bytes processed. Admins use `JOBS_BY_PROJECT` / `JOBS_BY_ORGANIZATION` for everyone's jobs (⚠️ those views need extra permissions and weren't tested in the sandbox this run).

Console: **Logging → Logs Explorer** in this project:

```
protoPayload.serviceName="bigquery.googleapis.com"
```

These are BigQuery **Data Access audit logs** — on by default and impossible to disable. Contrast with module 08, where you had to turn on Cloud Storage data-access logging yourself.

---

## Part B — AWS DynamoDB (optional): protection you must turn on

CloudShell, `us-east-1`, as `labadmin`.

```bash
aws dynamodb create-table --table-name lab09-cases \
  --attribute-definitions AttributeName=case_id,AttributeType=S \
  --key-schema AttributeName=case_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --deletion-protection-enabled \
  --tags Key=lab,Value=09
aws dynamodb wait table-exists --table-name lab09-cases

aws dynamodb put-item --table-name lab09-cases \
  --item '{"case_id":{"S":"C-001"},"status":{"S":"open"}}'
aws dynamodb get-item --table-name lab09-cases --key '{"case_id":{"S":"C-001"}}'

aws dynamodb describe-continuous-backups --table-name lab09-cases \
  --query "ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus"   # DISABLED
aws dynamodb update-continuous-backups --table-name lab09-cases \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true,RecoveryPeriodInDays=7

aws dynamodb delete-table --table-name lab09-cases     # refused: deletion protection
```

**What you should see:** a serverless table (no instance to size), encrypted at rest by default — but **PITR was disabled until you turned it on**, and the delete was refused because you enabled deletion protection. Both are customer decisions.

## Part C — Azure SQL Database (optional): Entra-only auth, no network path

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab09 --location eastus --tags lab=09
ME_UPN=$(az ad signed-in-user show --query userPrincipalName -o tsv)
ME_ID=$(az ad signed-in-user show --query id -o tsv)
SQLSRV=lab09-sql-$RANDOM

az sql server create --name $SQLSRV --resource-group rg-lab09 --location eastus \
  --enable-ad-only-auth --external-admin-principal-type User \
  --external-admin-name "$ME_UPN" --external-admin-sid $ME_ID

az sql db create --resource-group rg-lab09 --server $SQLSRV --name lab09db \
  --edition GeneralPurpose --family Gen5 --capacity 2 --compute-model Serverless \
  --use-free-limit true --free-limit-exhaustion-behavior AutoPause

az sql server firewall-rule list -g rg-lab09 -s $SQLSRV -o table          # expect empty
az sql server show -g rg-lab09 -n $SQLSRV --query "{public:publicNetworkAccess,entraOnly:administrators.azureAdOnlyAuthentication}"
```

**What you should see:** a database with **no SQL passwords** (Entra-only authentication) and **no firewall rules**, so nothing on the internet can reach it even though a public endpoint exists. If the region rejects the free offer, try `eastus2` or `centralus`. You won't connect in this lab — opening a firewall rule for your IP is exactly the kind of exposure decision module 11 covers.

---

## Verify it worked

| Check | Expected |
|---|---|
| Sandbox project billing | Not enabled; SANDBOX badge in BigQuery |
| Dry runs | `SELECT *` estimate much larger than the two-column query |
| `--maximum_bytes_billed=10000000` | Query refused, nothing billed |
| Hunt 1 / Hunt 2 | `203.0.113.66` (40 users); `user17` from `192.0.2.200` |
| `INFORMATION_SCHEMA.JOBS_BY_USER` | Your jobs with bytes processed, including the failed one |
| BigQuery audit logs | Entries present without enabling anything |
| (B) DynamoDB | PITR initially DISABLED; delete refused by deletion protection |
| (C) Azure SQL | Entra-only true; no firewall rules |

## What to notice (reflection questions)

1. On a billed project, what three controls would you set before handing analysts BigQuery access?
2. Your hunts read every row. On a two-year, 50 TB log table, what would you change so a hunt costs cents instead of dollars?
3. BigQuery logs every query by default; Cloud Storage doesn't log object reads by default. Why might Google make that choice differently for the two services?
4. The Snowflake-customer campaign needed no exploit. Which of today's controls (Entra-only auth, no firewall rules, IAM-only access) would have broken that kill chain, and at which step?
5. Write a plain-English detection for a compromised analyst account exfiltrating a dataset.

## Cleanup

**Google Cloud** — the cleanest reset is deleting the sandbox project:

```bash
bq rm -r -f -d $SBX:lab09_sec          # optional; project deletion removes it anyway
gcloud config set project <your-main-lab-project>
gcloud projects delete $SBX --quiet
rm -f signins.csv
gcloud projects list --filter="projectId:lab09-sbx*" --format="value(projectId,lifecycleState)"   # DELETE_REQUESTED
```

If Cloud Shell restarted, find the project with `gcloud projects list --filter="name:lab09-sbx"`. A deleted project stays recoverable for about 30 days, then is purged; it has no billing account, so it can't cost anything in the meantime.

**AWS**

```bash
aws dynamodb update-table --table-name lab09-cases --no-deletion-protection-enabled
aws dynamodb wait table-exists --table-name lab09-cases
aws dynamodb delete-table --table-name lab09-cases
aws dynamodb list-tables --query "TableNames[?starts_with(@,'lab09')]" --output text     # expect empty
```

**Azure**

```bash
az group delete --name rg-lab09 --yes
az group list --query "[?name=='rg-lab09']" -o table      # expect empty
```

**Final check — nothing billable remains:** the sandbox project is pending deletion (and never had billing); no `lab09-cases` table on AWS; no `rg-lab09` on Azure. Check Google **Billing → Reports** for your main billing account tomorrow: no BigQuery charges.

## Write-up prompt

> On [date] I used the BigQuery sandbox (no billing account) to query Google public datasets, compared dry-run byte estimates for full-table versus column-selective queries, and enforced a maximum-bytes-billed limit that safely blocked an over-budget query. I loaded a synthetic authentication log table and wrote SQL hunts that identified a password-spraying source and a successful sign-in following repeated failures from a new IP, created a view that removed identity columns, and audited my own query history and bytes scanned through INFORMATION_SCHEMA and BigQuery's always-on Data Access audit logs. [Optional: I created a DynamoDB table with deletion protection and enabled point-in-time recovery, and an Azure SQL free-offer database with Microsoft Entra-only authentication and no firewall rules.] I deleted all resources afterward.
