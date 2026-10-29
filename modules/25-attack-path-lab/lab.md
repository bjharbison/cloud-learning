# 25 Lab — Purple team in a throwaway project: emulate five cloud techniques, then find and detect them

**Cost:** about $0. A new Google Cloud project linked to your lab billing account (free trial credit or Free Tier). Five Stratus techniques that touch only IAM, Cloud Logging, a tiny Cloud Storage bucket, and a few Secret Manager secrets (the free tier covers 6 active secret versions; Stratus may create a few more for under an hour — fractions of a cent ⚠️ exact count not verified). Data Access audit logs for two services for an hour (KB against the 50 GiB free logging allotment). Log-based alerting policies aren't charged before September 2027 (module 19). **No VMs, GPUs, or notebooks.** The optional AWS part uses CloudTrail Event history (free) plus one trail and IAM user created and removed by the tool. · **Time:** 2.5–3 hours · **Clouds:** GCP (required), AWS (optional, separate sandbox account only), Azure (read-only comparison)

## Goal

1. Stand up a **dedicated, disposable project** and turn on the logs that matter.
2. Deploy **five detections** (two from module 22, three new).
3. Use **Stratus Red Team** to emulate five techniques.
4. **Hunt** each one in the audit logs and record whether a detection fired.
5. Produce a **coverage scorecard** and a short purple-team report.
6. **Delete the whole project.**

## Prerequisites

- Modules 00–24 done; budget alerts active on your billing account.
- Your billing account ID: `gcloud billing accounts list`.
- Read the README's **rules of engagement**. Summary: this project only; your own identity; **no technique that grants access to an outside account**; no org-level actions; no compute.

## Rules of engagement (copy into your notes and "sign" it)

```
System owner: <you>        Date: <today>        Scope: project lab25-purple-<suffix> only
Allowed techniques: the five listed in Part A, nothing else
Forbidden: any share-*, invite-*, backdoor-* technique; remove-project-from-organization;
           any technique creating compute; any target outside this project
Stop condition: anything unexpected outside the project → stop, run cleanup, delete project
```

---

## Part A — Google Cloud

### A1. Create the throwaway project (CLI)

Open Cloud Shell. Note your normal project so you can return to it, then create the sandbox:

```bash
ORIG_PROJECT=$(gcloud config get-value project)
BILLING=XXXXXX-XXXXXX-XXXXXX          # from: gcloud billing accounts list
LABP=lab25-purple-$(date +%m%d)-$RANDOM
gcloud projects create $LABP --labels=lab=25 --name="lab25 purple team"
gcloud billing projects link $LABP --billing-account=$BILLING
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com logging.googleapis.com \
  monitoring.googleapis.com secretmanager.googleapis.com storage.googleapis.com \
  cloudresourcemanager.googleapis.com --project=$LABP
mkdir -p ~/lab25 && cd ~/lab25 && echo "LABP=$LABP" > env.txt
```

Project IDs must be 6–30 characters, lowercase letters, digits, and hyphens — the generated name fits. Every command below passes `--project=$LABP`, so your normal project is never touched. (If Cloud Shell restarts, run `source ~/lab25/env.txt`.)

> **If project creation fails with a quota error:** personal accounts have a project limit. Delete an old lab project or request a quota increase — don't run this lab in your normal project.

### A2. Turn on Data Access logs for the techniques that need them (CLI)

Two of the five techniques are invisible without **Data Access** logs (module 18). Enable them for IAM (which covers the IAM Credentials impersonation calls) and Secret Manager — in this project only:

```bash
gcloud projects get-iam-policy $LABP --format=json > policy.json
python3 - <<'EOF'
import json
p = json.load(open("policy.json"))
p["auditConfigs"] = [
  {"service": "iam.googleapis.com", "auditLogConfigs": [{"logType": "DATA_READ"}, {"logType": "DATA_WRITE"}]},
  {"service": "secretmanager.googleapis.com", "auditLogConfigs": [{"logType": "DATA_READ"}]},
]
json.dump(p, open("policy.json", "w"), indent=1)
EOF
gcloud projects set-iam-policy $LABP policy.json --format="yaml(auditConfigs)"
```

The file keeps the existing `bindings` and `etag`, so you don't lock yourself out. **What you should see:** the two `auditConfigs` echoed back.

**Console check:** **IAM & Admin → Audit Logs** (with `$LABP` selected) — *Identity and Access Management (IAM) API* and *Secret Manager API* show Data Read enabled.

### A3. Deploy the detections (CLI)

Five log-based alerting policies, built with `jq` exactly as in module 22. Two are module 22's rules; three are new.

```bash
AA="logName=\"projects/$LABP/logs/cloudaudit.googleapis.com%2Factivity\""
DA="logName=\"projects/$LABP/logs/cloudaudit.googleapis.com%2Fdata_access\""
declare -A RULES=(
 ["lab25 IAM-001 human project IAM change (T1098.003)"]="$AA AND protoPayload.methodName=\"SetIamPolicy\" AND protoPayload.serviceName=\"cloudresourcemanager.googleapis.com\" AND NOT protoPayload.authenticationInfo.principalEmail:\"gserviceaccount.com\""
 ["lab25 LOG-001 sink deleted or updated (T1685.002)"]="$AA AND protoPayload.serviceName=\"logging.googleapis.com\" AND (protoPayload.methodName:\"DeleteSink\" OR protoPayload.methodName:\"UpdateSink\")"
 ["lab25 IAM-002 SA key created (T1098.001)"]="$AA AND protoPayload.methodName=\"google.iam.admin.v1.CreateServiceAccountKey\""
 ["lab25 IAM-003 SA impersonation token minted (T1548.005)"]="$DA AND protoPayload.serviceName=\"iamcredentials.googleapis.com\" AND protoPayload.methodName:\"GenerateAccessToken\""
 ["lab25 SEC-001 secret version accessed (T1555.006)"]="$DA AND protoPayload.methodName:\"AccessSecretVersion\""
)
for N in "${!RULES[@]}"; do
  jq -n --arg n "$N" --arg f "${RULES[$N]}" '{
    displayName: $n, combiner: "OR",
    conditions: [{displayName: $n, conditionMatchedLog: {filter: $f}}],
    alertStrategy: {notificationRateLimit: {period: "300s"}, autoClose: "1800s"},
    documentation: {content: "lab25 purple team. Runbook: module 23.", mimeType: "text/markdown"}}' > p.json
  gcloud monitoring policies create --policy-from-file=p.json --project=$LABP --format="value(displayName)"
done
```

**What you should see:** five policy names printed. Note that **IAM-001 excludes service accounts** — module 22's lab told you that's too broad. Keep it as is today and watch what it misses.

### A4. Install and authenticate Stratus Red Team (CLI)

Cloud Shell includes Go. Stratus needs Go 1.23 or later:

```bash
go version
go install -v github.com/datadog/stratus-red-team/v2/cmd/stratus@latest
export PATH=$PATH:$(go env GOPATH)/bin
stratus --help | head -5
```

If `go version` is older than 1.23, download the Linux x86_64 archive from the [GitHub releases page](https://github.com/DataDog/stratus-red-team/releases) instead, extract `stratus`, and run it as `./stratus`.

Stratus uses **Application Default Credentials** and the `GOOGLE_PROJECT` variable:

```bash
gcloud auth application-default login            # follow the link; sign in as your lab admin
gcloud auth application-default set-quota-project $LABP
export GOOGLE_PROJECT=$LABP
stratus list --platform gcp
```

**What you should see:** about 25 GCP techniques. Find the five you're allowed to run, and the ones you're forbidden to run.

**Safety check, before anything else:**

```bash
stratus show gcp.exfiltration.share-compute-disk | head -20
```

Read it: this technique grants access to an outside "attacker" Google account. That's why it's on the forbidden list. **Don't detonate it.**

### A5. Emulate, then hunt — one technique at a time (CLI)

For each technique: **read** (`show`), **detonate**, **hunt**, then **score**. Record the UTC time of each detonation:

```bash
T=gcp.persistence.create-admin-service-account
stratus show $T
date -u +%FT%TZ | tee -a times.txt; stratus detonate $T
```

Hunt for it (wait 1–2 minutes for logs):

```bash
gcloud logging read "$AA AND (protoPayload.methodName:\"CreateServiceAccount\" OR protoPayload.methodName=\"SetIamPolicy\")" \
  --project=$LABP --freshness=15m --limit=10 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

Repeat the pattern with these technique IDs and hunt filters:

| # | Technique ID | Hunt filter (append to `$AA` or `$DA`) |
|---|---|---|
| 2 | `gcp.persistence.create-service-account-key` | `$AA AND protoPayload.methodName="google.iam.admin.v1.CreateServiceAccountKey"` |
| 3 | `gcp.privilege-escalation.impersonate-service-accounts` | `$DA AND protoPayload.serviceName="iamcredentials.googleapis.com"` |
| 4 | `gcp.defense-evasion.delete-logging-sink` | `$AA AND protoPayload.methodName:"DeleteSink"` |
| 5 | `gcp.credential-access.secretmanager-retrieve-secrets` | `$DA AND protoPayload.methodName:"AccessSecretVersion"` |

For technique 3, look at the `status` field — Stratus tries 10 service accounts and only one succeeds, so you should see **failed** attempts (permission denied) followed by **one success**:

```bash
gcloud logging read "$DA AND protoPayload.serviceName=\"iamcredentials.googleapis.com\"" \
  --project=$LABP --freshness=15m --limit=20 \
  --format="table(timestamp,protoPayload.resourceName.basename(),protoPayload.status.code,protoPayload.authenticationInfo.principalEmail)"
```

**What you should see:** a burst of `GenerateAccessToken` calls against different service accounts, most with status code 7 (permission denied) and one with no error. That **burst of denials then a success** is a better behavioral signal than any single event — the same pattern as module 22's discovery-with-denials rule.

### A6. Check what fired (console)

**Monitoring → Alerting → Incidents** (project `$LABP`). Within about 5 minutes of each detonation you should see incidents for:

| Rule | Expected to fire on |
|---|---|
| IAM-001 | Technique 1 (you, a human, granted Owner to a new SA) |
| IAM-002 | Technique 2 |
| IAM-003 | Technique 3 |
| LOG-001 | Technique 4 |
| SEC-001 | Technique 5 |

Also check whether **IAM-001** fired for the warm-up of technique 3 (Stratus grants Token Creator on one service account). It shouldn't: that grant is a `SetIAMPolicy` on a **service account** resource via `iam.googleapis.com`, not on the project — a gap.

### A7. Build the scorecard (your notes)

```bash
cat > scorecard.md <<'EOF'
| # | Technique | ATT&CK | Log event seen? (AA/DA) | Rule fired? | Latency | Outcome | Backlog item |
|---|---|---|---|---|---|---|---|
| 1 | create-admin-service-account | T1136.003, T1098.003 | | | | | |
| 2 | create-service-account-key | T1098.001 | | | | | |
| 3 | impersonate-service-accounts | T1548.005 | | | | | |
| 4 | delete-logging-sink | T1685.002 | | | | | |
| 5 | secretmanager-retrieve-secrets | T1555.006 | | | | | |
| 6 | (warm-up) Token Creator granted on an SA | T1098.003 | | | | | |
EOF
```

Fill in each row. **Outcome** is one of Detected / Logged only / Not logged / Prevented (README). Then answer: *if Data Access had been off (the default), which rows would become "Not logged"?*

### A8. Revert and clean up the tool's resources (CLI)

```bash
stratus status
stratus cleanup --all
stratus status          # everything should be COLD
```

You'll delete the whole project next anyway — `cleanup` is the habit you'd need in a shared sandbox.

---

## Part B — AWS (optional; separate sandbox account only)

**Only do this in an AWS account that holds nothing else** — not your main lab account if you use it for other modules' resources. If you don't have one, skip Part B; creating a second account needs AWS Organizations, which ends the AWS free plan (module 00).

In that account's CloudShell:

```bash
go install -v github.com/datadog/stratus-red-team/v2/cmd/stratus@latest 2>/dev/null || echo "use the release binary"
export PATH=$PATH:$(go env GOPATH 2>/dev/null)/bin
stratus show aws.defense-evasion.cloudtrail-stop
stratus detonate aws.defense-evasion.cloudtrail-stop
stratus detonate aws.persistence.iam-create-admin-user
sleep 300
for EV in StopLogging CreateUser AttachUserPolicy CreateAccessKey; do
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=$EV \
    --max-results 3 --query 'Events[].[EventTime,EventName,Username]' --output text
done
stratus cleanup --all
```

**What you should see:** each event in Event history, and — if GuardDuty is on in that account — a `Stealth:IAMUser/CloudTrailLoggingDisabled` finding. Run module 22's `aws events test-event-pattern` check against a copy of the real `StopLogging` event to prove your EventBridge pattern would have matched it.

**Do not run** AWS techniques that share snapshots, volumes, AMIs, or buckets with another account ID (`ec2-share-*`, `rds-share-snapshot`, `s3-backdoor-bucket-policy`).

## Part C — Azure (read-only comparison)

No detonation on Azure in this lab. Several Entra ID techniques invite guest users or create federation, which can reach outside your tenant. Just compare coverage:

```bash
stratus list --platform azure
stratus list --platform entra-id
```

Pick two techniques and write down which Azure log (Activity Log, Entra audit) and which module 22 KQL query would detect each.

---

## Verify it worked

| Check | Expected |
|---|---|
| Sandbox | `$LABP` existed with Data Access on for IAM and Secret Manager |
| Detections | Five `lab25` alerting policies |
| Emulation | Five techniques detonated; all others untouched |
| Hunt | Each technique found in Admin Activity or Data Access logs |
| Alerts | Incidents for the rules that matched; at least one gap found |
| Scorecard | Six rows filled with outcome and backlog item |

## What to notice (reflection questions)

1. Which techniques would have been **invisible** with default logging? What would it cost to turn Data Access on organization-wide, and how would you scope it?
2. IAM-001 excluded service accounts. Re-run technique 1 in your head as a compromised service account doing the same thing. Would anything fire?
3. Technique 3 produced a burst of denied impersonation attempts. Write a behavioral rule (in YARA-L or KQL, module 22) for "≥ 5 denied `GenerateAccessToken` calls followed by a success, same principal, 10 minutes."
4. Which of your detections would survive an attacker using the console instead of an API client? Which field made it robust?
5. If you ran this monthly for an agency, what would you report to the CISO — and which module 24 actor's TTPs would you add next?

## Cleanup

**Google Cloud — delete the whole sandbox**

```bash
source ~/lab25/env.txt 2>/dev/null
export GOOGLE_PROJECT=$LABP
stratus cleanup --all
gcloud billing projects unlink $LABP          # stop billing first
gcloud projects delete $LABP --quiet
gcloud projects describe $LABP --format="value(lifecycleState)"   # expect DELETE_REQUESTED
gcloud auth application-default revoke --quiet
gcloud config set project $ORIG_PROJECT
rm -rf ~/.stratus-red-team
rm -f "$(go env GOPATH)/bin/stratus"
```

Unlinking billing before deletion avoids charges that could otherwise run to the end of the billing cycle. The project stays recoverable for 30 days (`gcloud projects undelete`) and still counts toward your project quota until it's purged. The alerting policies and audit-log settings were inside the project, so they go with it.

Download `scorecard.md` and `times.txt` first (Cloud Shell **⋮ → Download**) — they're your evidence. Then `rm -rf ~/lab25`.

**AWS (if you did Part B):** `stratus cleanup --all` again, then confirm: `aws cloudtrail describe-trails` shows no Stratus trail, and `aws iam list-users` shows no Stratus-created user. Remove `~/.stratus-red-team`.

**Final check — nothing billable remains:** `$LABP` is `DELETE_REQUESTED` with no billing account linked (`gcloud billing projects describe $LABP` shows `billingEnabled: false`); no Stratus resources in the AWS sandbox; your normal project is the active `gcloud` project again.

## Write-up prompt

> On [date] I ran a purple-team exercise in a personal, dedicated Google Cloud project with written rules of engagement. I enabled Data Access audit logs for IAM and Secret Manager, deployed five log-based detections mapped to MITRE ATT&CK, and used the open-source Stratus Red Team tool to emulate five techniques: creating an Owner-level service account, creating a service-account key, impersonating service accounts, deleting a log sink, and reading Secret Manager secrets. I hunted each in the audit logs, measured alert latency, scored coverage (Detected / Logged only / Not logged), identified gaps such as service-account-level IAM grants and default-off Data Access logs, and deleted the project afterward. [Optional: I emulated CloudTrail tampering and admin-user creation in a separate AWS sandbox account and found them in CloudTrail.]
