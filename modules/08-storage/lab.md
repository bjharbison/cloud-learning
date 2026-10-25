# 08 Lab — A bucket that can't go public, can't lose data by accident, and tells you who touched it

**Cost:** $0 expected on Google Cloud. Two small **Standard**-class buckets in `us-central1` holding a few kilobytes — inside the free tier (5 GB-month regional Standard in us-central1/us-east1/us-west1, 5,000 Class A and 50,000 Class B operations per month). Soft-deleted and noncurrent bytes are billed, but at kilobyte scale that rounds to $0.00. Turning on Data Access logs for one bucket for an hour generates a handful of log entries — well inside Cloud Logging's free allotment (⚠️ current free allotment not re-verified this run). **Do not use Nearline/Coldline/Archive in this lab** — minimum-duration charges apply. AWS (optional): one S3 bucket with a few KB, covered by free-plan credits. Azure (optional): one Standard LRS storage account with a few KB in Hot — inside the 12-month free 5 GB. · **Time:** 75–90 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Create a bucket with **uniform bucket-level access** and **public access prevention** — then try to make it public and watch it fail.
2. Turn on **versioning**, overwrite and delete a file, and get it back.
3. Delete a version and recover it from **soft delete**.
4. Write a **lifecycle rule**.
5. Put an **unlocked**, 60-second **retention policy** on a second bucket and watch a delete get refused.
6. Turn on **Data Access logs** for storage and see a read show up.
7. (Optional) The same "can't go public" checks on S3 and Azure Blob.

## Prerequisites

- Modules 00–07 done; budget alerts active.
- `gcloud config list` shows your lab project.

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
B=lab08-$PROJECT_ID-$RANDOM          # bucket names are globally unique
R=lab08-ret-$PROJECT_ID-$RANDOM
echo $B $R                           # write these down in case Cloud Shell restarts
```

> ⚠️ **Never run `--lock-retention-period` in this lab.** Locking a retention policy is irreversible; you could not delete the bucket until the period ends.

---

## Part A — Google Cloud Storage

### A1. A private-by-design bucket (console, then CLI)

Console: **Cloud Storage → Buckets → Create** → name `$B` → **Region** `us-central1` → **Storage class: Standard** → **Access control: Uniform** and tick **Enforce public access prevention on this bucket** → **Data protection**: leave **Soft delete** at the default (7 days) → **Labels** `lab=08` → Create.

CLI (either, not both):

```bash
gcloud storage buckets create gs://$B --location=$REGION \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access --public-access-prevention

gcloud storage buckets update gs://$B --update-labels=lab=08

gcloud storage buckets describe gs://$B \
  --format="yaml(location,default_storage_class,uniform_bucket_level_access,public_access_prevention,soft_delete_policy,labels)"
```

**What you should see:** `uniform_bucket_level_access: true`, `public_access_prevention: enforced`, and a soft-delete policy with `retentionDurationSeconds: '604800'` (7 days) — Google turned that on without being asked.

### A2. Try to make it public (CLI)

```bash
gcloud storage buckets add-iam-policy-binding gs://$B \
  --member=allUsers --role=roles/storage.objectViewer
```

**What you should see:** an error, typically **412 Precondition Failed**, mentioning public access prevention. The guardrail refused the grant. With UBLA on, there are no object ACLs to sneak around it either.

Look at who *can* read:

```bash
gcloud storage buckets get-iam-policy gs://$B
```

Project-level roles (Owner, Editor, Viewer) show up as `projectOwner:`/`projectEditor:`/`projectViewer:` convenience bindings. In a real org you'd grant `roles/storage.objectViewer` on this one bucket to a specific group — never on the whole project.

### A3. Versioning: overwrite, delete, recover (CLI)

```bash
gcloud storage buckets update gs://$B --versioning

echo "v1 - original report" > report.txt
gcloud storage cp report.txt gs://$B/
echo "v2 - edited report"   > report.txt
gcloud storage cp report.txt gs://$B/

gcloud storage ls -a gs://$B/report.txt     # two entries: report.txt#<gen1> and #<gen2>
gcloud storage cat gs://$B/report.txt       # v2 (the live version)
```

Now "accidentally" delete it:

```bash
gcloud storage rm gs://$B/report.txt
gcloud storage ls gs://$B                    # nothing live
gcloud storage ls -a gs://$B                 # both versions still there, now noncurrent
```

Restore v1 by copying that generation back over the live name (paste the `#generation` from the listing):

```bash
gcloud storage cp gs://$B/report.txt#<GEN1> gs://$B/report.txt
gcloud storage cat gs://$B/report.txt        # v1 is back
```

**Notice:** versioning turned a delete into a reversible action. It also means every overwrite keeps a billed copy — which is why you pair it with a lifecycle rule (A5).

### A4. Soft delete: the net under the net (CLI)

Delete one **noncurrent** version permanently (paste a generation that is *not* the live one):

```bash
gcloud storage rm gs://$B/report.txt#<GEN2>
gcloud storage ls -a gs://$B/report.txt                 # GEN2 is gone from the normal listing
gcloud storage ls --soft-deleted -a gs://$B             # …but it's here, soft-deleted
gcloud storage restore gs://$B/report.txt#<GEN2>        # bring it back
gcloud storage ls -a gs://$B/report.txt                 # GEN2 reappears
```

**What you should see:** the "permanently" deleted version was recoverable for 7 days. An attacker with `storage.admin` could shorten or disable soft delete first — that's why locked retention (A6) exists for data that really matters.

### A5. A lifecycle rule (console, then CLI)

Console: **Bucket → Lifecycle → Add a rule** → action **Delete object** → condition **Number of newer versions: 2** → Create. Look at the other actions offered (Set storage class to Nearline/Coldline/Archive) but **don't** add them.

CLI (either, not both):

```bash
cat > lifecycle.json <<'EOF'
{
  "rule": [
    {"action": {"type": "Delete"},
     "condition": {"numNewerVersions": 2, "isLive": false}},
    {"action": {"type": "Delete"},
     "condition": {"daysSinceNoncurrentTime": 30}}
  ]
}
EOF
gcloud storage buckets update gs://$B --lifecycle-file=lifecycle.json
gcloud storage buckets describe gs://$B --format="json(lifecycle_config)"
```

**Notice:** "keep at most two old versions, and none older than 30 days." Lifecycle actions run asynchronously (Google says changes can take up to 24 hours to take effect), so you won't see it fire during the lab. In production this rule is what keeps versioning from silently doubling your bill.

### A6. Retention: a delete that's refused (CLI)

Use a **separate** bucket so retention doesn't mix with the versioning experiments.

```bash
gcloud storage buckets create gs://$R --location=$REGION \
  --uniform-bucket-level-access --public-access-prevention \
  --retention-period=60s
gcloud storage buckets update gs://$R --update-labels=lab=08

echo "evidence item 001" > evidence.txt
gcloud storage cp evidence.txt gs://$R/
gcloud storage rm gs://$R/evidence.txt        # refused
```

**What you should see:** a `403` / permission-denied error saying the object is under a retention policy (`retentionPolicyNotMet`). **You are project Owner** and still can't delete it. Wait 60 seconds:

```bash
sleep 65; gcloud storage rm gs://$R/evidence.txt     # now it works
gcloud storage buckets describe gs://$R --format="yaml(retention_policy)"
```

Note `isLocked` is false (or absent). If it were locked, you couldn't remove the policy, shorten it, or delete the bucket until every object aged out — and with a 7-year policy, that's 7 years. *Read, don't run:* `gcloud storage buckets update gs://$R --lock-retention-period`.

### A7. Who read the file? Turn on Data Access logs (console)

Data Access logs for Cloud Storage are **off by default**. Turn on just reads for this project:

Console: **IAM & Admin → Audit Logs** → filter `Google Cloud Storage` → tick it → in the side panel check **Data Read** → **Save**.

Wait a minute, then read the file and check the logs:

```bash
sleep 60
gcloud storage cat gs://$B/report.txt >/dev/null
sleep 60
gcloud logging read \
  "resource.type=\"gcs_bucket\" AND resource.labels.bucket_name=\"$B\" AND logName:\"data_access\"" \
  --limit=5 --freshness=30m \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail,protoPayload.requestMetadata.callerIp)"
```

**What you should see:** a `storage.objects.get` entry with your identity and IP. Now look at the **Admin Activity** side, which was always on:

```bash
gcloud logging read \
  "resource.type=\"gcs_bucket\" AND resource.labels.bucket_name=\"$B\" AND logName:\"activity\"" \
  --limit=10 --freshness=2h \
  --format="table(timestamp,protoPayload.methodName,protoPayload.status.code)"
```

Look for bucket creation, the versioning/lifecycle updates, and — possibly — your refused `SetIamPolicy` from A2 with a non-zero status code (⚠️ whether rejected PAP grants appear in Admin Activity wasn't verified this run; note what you see).

**Turn Data Access logging back off** when done (same screen, untick **Data Read**, Save) — at scale it can cost money.

---

## Part B — AWS S3 (optional): defaults that already block public

CloudShell, `us-east-1`, as `labadmin`.

```bash
SB=lab08-$(aws sts get-caller-identity --query Account --output text)-$RANDOM
aws s3api create-bucket --bucket $SB --region us-east-1
aws s3api put-bucket-tagging --bucket $SB --tagging 'TagSet=[{Key=lab,Value=08}]'

aws s3api get-public-access-block --bucket $SB          # all four settings true
aws s3api get-bucket-ownership-controls --bucket $SB    # BucketOwnerEnforced (ACLs disabled)
aws s3api get-bucket-encryption --bucket $SB            # SSE-S3 (AES256) by default

aws s3api put-bucket-versioning --bucket $SB --versioning-configuration Status=Enabled
echo v1 > r.txt; aws s3 cp r.txt s3://$SB/; echo v2 > r.txt; aws s3 cp r.txt s3://$SB/
aws s3api list-object-versions --bucket $SB --query "Versions[].{Key:Key,Id:VersionId,Latest:IsLatest}"
```

**What you should see:** you did nothing special, yet Block Public Access is on, ACLs are disabled, and encryption is set — the April 2023 and January 2023 defaults. *Read, don't run:* making it public would require first deleting the public access block, then attaching a bucket policy with `"Principal": "*"`. Two deliberate steps — and CloudTrail would record both.

## Part C — Azure Blob (optional): anonymous access off, RBAC for data

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab08 --location eastus --tags lab=08
SA=lab08$RANDOM$RANDOM                               # 3–24 lowercase letters/digits, globally unique
az storage account create --name $SA --resource-group rg-lab08 --location eastus \
  --sku Standard_LRS --kind StorageV2 --access-tier Hot \
  --allow-blob-public-access false --min-tls-version TLS1_2 --tags lab=08
az storage account show -n $SA -g rg-lab08 --query "{public:allowBlobPublicAccess,sharedKey:allowSharedKeyAccess,tls:minimumTlsVersion}"

az storage account blob-service-properties update -n $SA -g rg-lab08 \
  --enable-versioning true --enable-delete-retention true --delete-retention-days 7
```

Now the **control plane vs data plane** lesson. You're subscription Owner — but Owner doesn't include reading blob data. Give yourself a data role on just this account:

```bash
ME=$(az ad signed-in-user show --query id -o tsv)
SCOPE=$(az storage account show -n $SA -g rg-lab08 --query id -o tsv)
az role assignment create --assignee $ME --role "Storage Blob Data Contributor" --scope $SCOPE
sleep 90    # role assignments take a minute or two to apply
az storage container create --account-name $SA --name lab08 --auth-mode login
echo hello > h.txt
az storage blob upload --account-name $SA --container-name lab08 --name h.txt --file h.txt --auth-mode login
```

**What you should see:** `allowBlobPublicAccess: false`. If the container command fails with an authorization error, wait another minute and retry — that's role propagation. Note you used `--auth-mode login` (your Entra identity) rather than the account key. In production, consider setting `--allow-shared-key-access false` so keys and key-signed SAS tokens can't be used at all (⚠️ check app compatibility first).

---

## Verify it worked

| Check | Expected |
|---|---|
| `buckets describe gs://$B` | UBLA true, PAP enforced, soft delete 7 d, versioning on, lifecycle rules |
| `allUsers` grant attempt | Refused (412) |
| Delete live object, then restore a generation | File content recovered |
| Delete noncurrent version, then `restore` | Version reappears |
| Delete inside 60 s on `gs://$R` | Refused; succeeds after 60 s |
| Data Access log | `storage.objects.get` with your principal |
| (B) S3 defaults | Block Public Access all true; `BucketOwnerEnforced`; SSE-S3 |
| (C) Azure | `allowBlobPublicAccess: false`; upload works only after a data-plane role |

## What to notice (reflection questions)

1. Owner couldn't delete the retained object in A6. What does that tell you about using a *locked* policy against ransomware — and about the risk of setting one wrong?
2. Versioning, soft delete, and retention all "keep data." Which one stops (a) a buggy script, (b) a careless admin, (c) an attacker holding `storage.admin`?
3. Data Access logs were off until you turned them on. If a bucket had been exfiltrated last month with them off, what could you still say from Admin Activity logs — and what couldn't you?
4. On Azure, subscription Owner couldn't read blobs until you added a data role. Map that to Google's split between project roles and `roles/storage.objectViewer`.
5. Write a plain-English detection for T1530 against this bucket.

## Cleanup

**Google Cloud**

```bash
# Optional: objects deleted FROM NOW ON won't be retained. Anything already soft-deleted keeps its 7-day
# window (kilobytes; ~$0). Deleting a bucket also soft-deletes the bucket itself for a restorable window.
gcloud storage buckets update gs://$B --clear-soft-delete
gcloud storage buckets update gs://$R --clear-soft-delete

gcloud storage rm --recursive gs://$B         # deletes ALL versions, then the bucket
gcloud storage rm --recursive gs://$R         # works because the 60 s retention has passed and was never locked
rm -f report.txt evidence.txt lifecycle.json
```

If Cloud Shell restarted and `$B`/`$R` are empty: `gcloud storage ls | grep lab08` and delete each.

Confirm Data Access logging is **off**: **IAM & Admin → Audit Logs → Google Cloud Storage** — Data Read unticked.

```bash
gcloud storage ls | grep lab08 || echo "no lab08 buckets"
```

**AWS** — a versioned bucket must have every version removed before it can be deleted:

```bash
aws s3api delete-objects --bucket $SB --delete "$(aws s3api list-object-versions --bucket $SB \
  --query '{Objects: [Versions, DeleteMarkers][][].{Key:Key,VersionId:VersionId}}' --output json)"
aws s3api delete-bucket --bucket $SB
aws s3api list-buckets --query "Buckets[?starts_with(Name,'lab08')].Name" --output text   # expect empty
rm -f r.txt
```

If `delete-objects` reports nothing to delete, run `delete-bucket` directly.

**Azure**

```bash
az group delete --name rg-lab08 --yes
az group list --query "[?name=='rg-lab08']" -o table      # expect empty
rm -f h.txt
```

Deleting the resource group removes the storage account and everything in it; the role assignment scoped to it goes too.

**Final check — nothing billable remains:** no `lab08` buckets on Google, Data Access logging off; no `lab08` bucket on AWS; no `rg-lab08` on Azure. Tomorrow, check Google **Billing → Reports** filtered to Cloud Storage: expect $0.00.

## Write-up prompt

> On [date] I configured Google Cloud Storage buckets with uniform bucket-level access and enforced public access prevention, and verified that a grant to `allUsers` was refused. I enabled Object Versioning and recovered an overwritten and deleted object from a noncurrent generation, restored a permanently deleted version from soft delete, wrote lifecycle rules to cap noncurrent versions, and demonstrated an (unlocked) retention policy blocking deletion by a project Owner. I enabled Cloud Storage Data Access audit logs and confirmed an object read was recorded with the caller's identity and IP. [Optional: I confirmed S3's default Block Public Access, disabled ACLs, and default encryption on a new bucket, and created an Azure storage account with anonymous access disallowed and data access via Entra ID RBAC.] I deleted all resources afterward.
