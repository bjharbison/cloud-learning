# 23 Lab — Run a credential-compromise incident on yourself: emulate, preserve, contain, scope, recover

**Cost:** $0 expected. Google Cloud: two small buckets (bytes) and a service account; Data Access logs for one bucket for an hour (KB against the 50 GiB free allotment). The optional VM step uses an **e2-micro** in `us-central1` (free-tier eligible if you have no other e2-micro running this month) with no external IP, plus one snapshot of its 10 GB boot disk for under an hour (fractions of a cent) ⚠️ snapshot pricing not re-verified this run — delete it promptly. AWS (optional): an IAM user and access key — no charge; CloudTrail Event history is free. Azure (optional): an Entra test user — no charge. · **Time:** 2–2.5 hours · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

Play both sides of a small incident in your own lab, then work it like a responder:

1. **Emulate** an attacker using a compromised service account: discovery, a data read, and a failed persistence attempt.
2. **Detect and scope** from audit logs — including *who* was behind the impersonation.
3. **Preserve** evidence with hashes in a separate evidence bucket.
4. **Contain** without deleting, and observe what disabling does and doesn't stop.
5. (Optional) **Snapshot** a VM for forensics before removal.
6. (AWS) See the classic trap: a deactivated access key whose **temporary credentials still work** — and the fix.
7. (Azure) Disable a user and **revoke sessions**.
8. Write a short **incident timeline**.

## Prerequisites

- Modules 00–22 done; budget alerts active. Re-read module 18's log anatomy.
- Cloud Shell, lab project selected.

```bash
PROJECT_ID=$(gcloud config get-value project)
ME=$(gcloud config get-value account)
SA=lab23-app@$PROJECT_ID.iam.gserviceaccount.com
B=lab23-data-$PROJECT_ID-$RANDOM
EV=lab23-evidence-$PROJECT_ID-$RANDOM
ZONE=us-central1-a
mkdir -p ~/lab23 && cd ~/lab23
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com storage.googleapis.com logging.googleapis.com compute.googleapis.com
```

**Rules of engagement:** everything here targets resources you create in your own project/account. You will impersonate your own service account — no keys are created, and nothing leaves your project.

---

## Part A — Google Cloud

### A1. Build the victim (CLI, then one console step)

```bash
gcloud storage buckets create gs://$B --location=us-central1 --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=23
printf "name,salary\nalice,100\nbob,90\n" > payroll.csv && gcloud storage cp payroll.csv gs://$B/
gcloud iam service-accounts create lab23-app --display-name="lab23 app (will be 'compromised')"
gcloud storage buckets add-iam-policy-binding gs://$B --member=serviceAccount:$SA --role=roles/storage.objectViewer
gcloud iam service-accounts add-iam-policy-binding $SA --member=user:$ME --role=roles/iam.serviceAccountTokenCreator
```

The last line lets *you* mint tokens for the SA — standing in for an attacker who stole its credentials.

**Console:** turn on Data Access logs for Cloud Storage (**IAM & Admin → Audit Logs → Google Cloud Storage → Data Read + Data Write → Save**), as in module 18. Without this, the most important question — *what did they read?* — has no answer.

### A2. Emulate the attacker (CLI)

Wait a minute for IAM to propagate, then act as the SA:

```bash
sleep 60
export CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT=$SA       # every gcloud call below runs as the SA
gcloud storage ls 2>&1 | tail -1                           # discovery: list buckets (T1619/T1580)
gcloud compute instances list 2>&1 | tail -1              # discovery: list VMs (T1580)
gcloud storage cat gs://$B/payroll.csv                     # collection: read data (T1530)
gcloud iam service-accounts keys create /dev/null --iam-account=$SA 2>&1 | tail -1   # persistence attempt (T1098.001)
unset CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee attack_end.txt
```

**What you should see:** permission errors on the two discovery calls and the key creation (the SA has no such rights, and your org may also block key creation by policy), and the payroll file contents on the read. Real attackers generate exactly this mix of denials and successes.

### A3. Detect and scope from the logs (CLI)

Wait 1–2 minutes. Everything the SA did, across all audit log types:

```bash
gcloud logging read "protoPayload.authenticationInfo.principalEmail=\"$SA\"" --freshness=1h --limit=50 \
  --format="table(timestamp,logName.basename(),protoPayload.methodName,protoPayload.status.code,protoPayload.requestMetadata.callerIp)"
```

Now **attribution** — who was behind the SA? Impersonation leaves the chain in each entry:

```bash
gcloud logging read "protoPayload.authenticationInfo.principalEmail=\"$SA\"" --freshness=1h --limit=1 --format=json \
  | jq '.[0].protoPayload.authenticationInfo'
```

**What you should see:** `storage.objects.get` on `payroll.csv` (succeeded, in the `data_access` log), denied `storage.buckets.list` and compute list calls (status code 7 = permission denied), and the key-creation attempt if your setup logs denied admin calls ⚠️ (whether a denied `CreateServiceAccountKey` appears depends on where it was blocked — IAM vs org policy). The `serviceAccountDelegationInfo` block names **your user** as the principal who impersonated the SA. In a real case, that field is how you go from "the app account did it" to "this human or workload credential did it."

Write the timeline as you go (UTC, from the log timestamps) in `~/lab23/timeline.md`: first activity, each discovery attempt, the data read, the persistence attempt.

### A4. Preserve evidence (CLI)

```bash
gcloud storage buckets create gs://$EV --location=us-central1 --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$EV --versioning --update-labels=lab=23,purpose=evidence

gcloud logging read "protoPayload.authenticationInfo.principalEmail=\"$SA\"" \
  --freshness=2h --format=json > evidence_sa_activity.json
gcloud logging read "protoPayload.serviceName=\"iam.googleapis.com\" OR protoPayload.serviceName=\"iamcredentials.googleapis.com\"" \
  --freshness=2h --format=json > evidence_iam_activity.json
sha256sum evidence_*.json | tee evidence_hashes.txt
touch timeline.md
gcloud storage cp evidence_*.json evidence_hashes.txt timeline.md gs://$EV/case-lab23/
gcloud storage ls -L gs://$EV/case-lab23/ | grep -E "gs://|Hash \(crc32c\)|Creation time"
```

**What to notice:** your SHA-256 hashes are recorded *with* the evidence, Cloud Storage records its own checksums and creation times, and versioning means an overwrite won't destroy the original. In a real case you'd also add a **locked retention policy** (Bucket Lock, module 08) — skipped here so you can clean up. Your own export actions are in the audit log too: that's your custody trail.

### A5. Contain — disable, don't delete (CLI)

```bash
gcloud iam service-accounts disable $SA
gcloud iam service-accounts remove-iam-policy-binding $SA --member=user:$ME --role=roles/iam.serviceAccountTokenCreator
gcloud iam service-accounts describe $SA --format="value(email,disabled)"
sleep 60
gcloud storage cat gs://$B/payroll.csv --impersonate-service-account=$SA 2>&1 | tail -2
```

**What you should see:** `disabled: True`, then the impersonated read **fails**. Two independent controls now stop the "attacker": the SA can't get new tokens, and you can no longer mint them. ⚠️ If the read **succeeds**, gcloud reused a cached token — tokens already issued stay valid until they expire (up to an hour). That's exactly Google's warning: disabling stops *new* tokens; for immediate effect on existing ones, add an **IAM deny policy** on the principal (module 14) and wait out the token lifetime before re-enabling.

You did **not** delete the SA. Deleting it would make its ID harder to correlate, and a later investigator might need to re-enable it for testing in a controlled way.

### A6. (Optional) Forensic snapshot of an attacker-created VM (CLI)

Suppose the attacker had launched a VM. Simulate one (no external IP, no SSH needed), then preserve its disk before removal:

```bash
gcloud compute instances create lab23-suspect --zone=$ZONE --machine-type=e2-micro \
  --no-address --labels=lab=23 --image-family=debian-12 --image-project=debian-cloud
gcloud compute snapshots create lab23-suspect-snap --source-disk=lab23-suspect --source-disk-zone=$ZONE \
  --labels=lab=23,case=lab23 --description="Case lab23: boot disk of suspect VM, taken before deletion"
gcloud compute snapshots describe lab23-suspect-snap --format="yaml(name,status,diskSizeGb,storageBytes,creationTimestamp,labels)"
gcloud compute instances delete lab23-suspect --zone=$ZONE --quiet
```

**What to notice:** the VM had no external IP and nobody SSHed in — evidence was captured entirely through the API. The snapshot survives the VM's deletion. In a real case you'd create a disk from it in an isolated **forensics project** and examine it there (Google's Cloud Forensics Utils automates this). You'll delete the snapshot in Cleanup.

### A7. Eradicate, recover, improve (your notes)

Answer in `timeline.md`:

1. **Persistence check:** did the SA create keys, roles, or SAs? (`gcloud iam service-accounts keys list --iam-account=$SA --managed-by=user` should show none.)
2. **Recovery:** what would the app use instead of this SA's stolen credentials? (A new SA with **workload identity federation** or an attached identity, no keys — module 15.)
3. **Improve:** which detection from module 22 would have fired, and how fast? Which guardrail (module 20) blocked the persistence attempt?
4. **Data impact statement:** "payroll.csv was read once by $SA at <time> (confirmed by Data Access log)." Without step A1's console change, what could you have said?

### A8. The leaked-key path (read-along)

If the compromise were a **downloaded key** instead of impersonation, the same playbook adds key-specific steps. Read them; don't create a key for this lab (your organization likely blocks it anyway):

```bash
gcloud iam service-accounts keys list --iam-account=$SA --managed-by=user          # which keys exist, when created
gcloud iam service-accounts keys disable KEY_ID --iam-account=$SA                   # contain (reversible)
gcloud iam service-accounts keys delete KEY_ID --iam-account=$SA                    # after replacement is live
gcloud logging read "protoPayload.authenticationInfo.serviceAccountKeyName:\"KEY_ID\"" --freshness=30d   # what that key did ⚠️ field name per audit-log docs
```

And check whether Google already acted: keys found in public repositories are **auto-disabled** by default (`iam.serviceAccountKeyExposureResponse`), with a notice to project owners and Essential Contacts.

---

## Part B — AWS (optional): the access-key trap

AWS CloudShell, as `labadmin`. You'll create a deliberately "leaked" key for a throwaway user that can do almost nothing. **Keep the key only in shell variables — never write it to a file.**

```bash
aws iam create-user --user-name lab23-leaky --tags Key=lab,Value=23
aws iam put-user-policy --user-name lab23-leaky --policy-name lab23-list-buckets \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:ListAllMyBuckets","Resource":"*"}]}'
read AK SK < <(aws iam create-access-key --user-name lab23-leaky --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text)
echo "Key ID: $AK"     # the ID is fine to display; the secret is not
sleep 15
```

**B1. The attacker uses the key — and mints temporary credentials:**

```bash
AWS_ACCESS_KEY_ID=$AK AWS_SECRET_ACCESS_KEY=$SK aws sts get-caller-identity
AWS_ACCESS_KEY_ID=$AK AWS_SECRET_ACCESS_KEY=$SK aws s3 ls >/dev/null && echo "s3 ls OK"
AWS_ACCESS_KEY_ID=$AK AWS_SECRET_ACCESS_KEY=$SK aws iam list-users 2>&1 | tail -1      # denied (discovery)
read TAK TSK TST < <(AWS_ACCESS_KEY_ID=$AK AWS_SECRET_ACCESS_KEY=$SK aws sts get-session-token \
  --duration-seconds 900 --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text)
echo "Temp key: $TAK"
```

**B2. Respond: triage the key.**

```bash
aws iam list-access-keys --user-name lab23-leaky
aws iam get-access-key-last-used --access-key-id $AK
```

**B3. Contain step 1 — deactivate the key, and test both credentials:**

```bash
aws iam update-access-key --user-name lab23-leaky --access-key-id $AK --status Inactive
sleep 15
AWS_ACCESS_KEY_ID=$AK AWS_SECRET_ACCESS_KEY=$SK aws s3 ls 2>&1 | tail -1                              # fails
AWS_ACCESS_KEY_ID=$TAK AWS_SECRET_ACCESS_KEY=$TSK AWS_SESSION_TOKEN=$TST aws s3 ls >/dev/null && echo "TEMP CREDS STILL WORK"
```

**What you should see:** the long-term key fails — and the temporary credentials minted from it **still work** ⚠️ (AWS's docs frame this as "change permissions to stop temporary credentials"; observe the actual behavior in your account). This is why deactivating a key is step one, not the whole containment.

**B4. Contain step 2 — deny by permissions (checked on every request):**

```bash
aws iam put-user-policy --user-name lab23-leaky --policy-name lab23-deny-all \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*"}]}'
sleep 15
AWS_ACCESS_KEY_ID=$TAK AWS_SECRET_ACCESS_KEY=$TSK AWS_SESSION_TOKEN=$TST aws s3 ls 2>&1 | tail -1    # now denied
```

This is the same idea AWS applies with **`AWSCompromisedKeyQuarantineV3`** and the role **"Revoke active sessions"** button (an inline `AWSRevokeOlderSessions` deny on tokens issued before a time).

**B5. Scope in CloudTrail Event history** (wait ~5–15 minutes for events):

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=Username,AttributeValue=lab23-leaky \
  --max-results 20 --query 'Events[].[EventTime,EventName,EventSource]' --output table
```

**What you should see:** `GetCallerIdentity` ⚠️ (may not appear for all regions/STS endpoints), `ListBuckets`, the denied `ListUsers`, `GetSessionToken`, and the post-deactivation calls. Note the temp-credential calls are attributed to the same user — that's how you'd find activity from session credentials in a real case. Clear the variables: `unset AK SK TAK TSK TST`.

## Part C — Azure (optional): disable a user and revoke sessions

Creating and disabling users needs an Entra role such as **User Administrator** — `labadmin` has Owner on the *subscription*, which isn't a directory role (module 14). Use your sign-up identity, or skip this part. Azure Cloud Shell:

```bash
DOMAIN=$(az rest --method GET --url "https://graph.microsoft.com/v1.0/domains" --query "value[?isDefault].id" -o tsv)
PW="Lab23-$(openssl rand -hex 12)!"
UID23=$(az ad user create --display-name "lab23 test user" --user-principal-name lab23-user@$DOMAIN \
  --password "$PW" --query id -o tsv)
az ad user update --id $UID23 --account-enabled false
az rest --method POST --url "https://graph.microsoft.com/v1.0/users/$UID23/revokeSignInSessions"
az ad user show --id $UID23 --query "{upn:userPrincipalName, enabled:accountEnabled}"
unset PW
```

Then **Entra admin center → Monitoring & health → Audit logs**: find *Update user* and the session revocation for `lab23-user`. **What to notice:** disabling and revoking are separate actions with separate log entries; Microsoft's emergency-revocation guidance does both (plus device disablement), and **Continuous Access Evaluation** propagates them to supporting apps within about 15 minutes.

---

## Verify it worked

| Check | Expected |
|---|---|
| Emulation | Denied discovery, successful `payroll.csv` read, failed key creation |
| Scope | SA activity table; `serviceAccountDelegationInfo` names you |
| Preserve | Evidence JSON + SHA-256 file in a versioned evidence bucket |
| Contain | SA `disabled: True`; Token Creator removed; impersonated read fails (or cached-token lesson) |
| (A6) Snapshot | `lab23-suspect-snap` READY after VM deletion |
| (B) AWS | Deactivated key fails; temp creds work until the deny policy |
| (C) Azure | User disabled; revoke call returns `value: true`; audit entries present |
| Timeline | UTC timeline + data impact statement |

## What to notice (reflection questions)

1. Which single setting decided whether you could write a data impact statement? When must it be turned on?
2. Why disable rather than delete the SA in the first hour? When would you delete it?
3. In AWS, what would an attacker with temporary credentials do in the minutes between key deactivation and your deny policy? How does the AWS quarantine policy shorten that window?
4. Your evidence bucket lives in the same project as the incident. Why is that wrong in production, and where should it live?
5. Map this lab to NIST SP 800-61 Rev. 3's Functions: which steps were Detect, Respond, Recover — and what belongs in Govern/Identify/Protect before the next one?

## Cleanup

**Google Cloud**

```bash
cd ~/lab23
gcloud iam service-accounts delete $SA --quiet
gcloud storage rm --recursive gs://$B
gcloud storage rm --recursive --all-versions gs://$EV
gcloud compute instances delete lab23-suspect --zone=$ZONE --quiet 2>/dev/null || true
gcloud compute snapshots delete lab23-suspect-snap --quiet 2>/dev/null || echo "no snapshot (A6 skipped)"
```

Console → **IAM & Admin → Audit Logs → Google Cloud Storage** → uncheck **Data Read** and **Data Write** → Save. Verify and sweep:

```bash
gcloud projects get-iam-policy $PROJECT_ID --format=json | jq '.auditConfigs // "none"'
gcloud storage ls | grep lab23 || echo "no lab23 buckets"
gcloud compute snapshots list --filter="labels.lab=23" --format="value(name)"
gcloud compute instances list --filter="labels.lab=23" --format="value(name)"
gcloud iam service-accounts list --filter="email~lab23" --format="value(email)"
```

Download `timeline.md` and `evidence_hashes.txt` as lab evidence (Cloud Shell **⋮ → Download**), then `rm -rf ~/lab23`. The evidence JSON contains only your own lab activity, but it's still log data — don't commit it to this repo.

**AWS**

```bash
for k in $(aws iam list-access-keys --user-name lab23-leaky --query 'AccessKeyMetadata[].AccessKeyId' --output text); do
  aws iam delete-access-key --user-name lab23-leaky --access-key-id $k; done
aws iam delete-user-policy --user-name lab23-leaky --policy-name lab23-list-buckets
aws iam delete-user-policy --user-name lab23-leaky --policy-name lab23-deny-all
aws iam delete-user --user-name lab23-leaky
aws iam get-user --user-name lab23-leaky 2>&1 | tail -1     # NoSuchEntity
```

The temporary credentials expire on their own within 15 minutes, and they belonged to a user that no longer exists.

**Azure**

```bash
az ad user delete --id $UID23
```

Deleted users sit in Entra's recycle bin for a period before permanent deletion; no charge.

**Final check — nothing billable remains:** no `lab23` buckets, SA, VM, or snapshot; Data Access logs back to off; no `lab23-leaky` IAM user or keys; no `lab23-user` in Entra.

## Write-up prompt

> On [date] I ran a cloud incident-response exercise in a personal lab. On Google Cloud I emulated a compromised service account (discovery attempts, a data read, and a failed key-creation attempt), scoped its activity from Cloud Audit Logs including the impersonation chain, preserved the relevant logs with SHA-256 hashes in a versioned evidence bucket, contained the account by disabling it and removing token-creation rights, [took a forensic snapshot of a VM before deleting it,] and wrote a UTC timeline with a data-impact statement. [On AWS I showed that temporary credentials minted from an access key kept working after the key was deactivated and contained them with a deny policy; on Microsoft Entra ID I disabled a test user and revoked its sessions.] I removed all lab resources afterward.
