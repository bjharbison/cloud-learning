# 16 Lab — Hold the key: envelope encryption by hand, a CMEK bucket you can switch off, and a secret instead of a password

**Cost:** about **$0.01** on Google Cloud if you clean up the same day. One software key version bills ~$0.06/month while enabled, disabled, **or scheduled for destruction**, so a second version and a 1-day destroy schedule add fractions of a cent; crypto operations are $0.03 per 10,000 (you'll make a few dozen). The bucket fits the always-free 5 GB-month in `us-central1`; Secret Manager stays inside its free 6 versions / 10,000 accesses. AWS (optional): one customer managed key at **$1/month** (⚠️ hourly proration not confirmed — you'll schedule deletion within the hour, and AWS doesn't bill keys pending deletion); a few requests inside the 20,000/month free tier. Azure (optional): a Key Vault Standard with a handful of secret operations — fractions of a cent ⚠️ (current per-operation price not confirmed). · **Time:** 75–90 min, plus a 2-minute follow-up the next day · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Create a Cloud KMS **key ring** and **key** with a short destroy schedule.
2. Do **envelope encryption by hand**: a local DEK encrypts a file, KMS wraps the DEK.
3. Protect a bucket with **CMEK**, then **disable** the key version and watch reads fail — then restore them.
4. **Rotate** the key and see that old objects still read.
5. Store a credential in **Secret Manager** and read it with IAM, not a file.
6. (Optional) Do the AWS data-key equivalent and an Azure Key Vault secret — and clean both up correctly given their deletion windows.

## Prerequisites

- Modules 00–15 done; budget alerts active.
- Cloud Shell, lab project selected.

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
LOC=us-central1
KR=lab16-kr
KEY=lab16-key
B=lab16-$PROJECT_ID-$RANDOM
gcloud services enable cloudkms.googleapis.com secretmanager.googleapis.com storage.googleapis.com
echo "$B"
```

---

## Part A — Google Cloud

### A1. Key ring and key (console, then CLI)

Console tour: **Security → Key Management → Create key ring**. Note the fields: location (fixed forever), then key **protection level** (Software / HSM / External…), **purpose**, **rotation period**, and **"Duration of 'scheduled for destruction' state"**. Cancel, then use the CLI:

```bash
gcloud kms keyrings create $KR --location=$LOC
gcloud kms keys create $KEY --keyring=$KR --location=$LOC \
  --purpose=encryption --protection-level=software \
  --destroy-scheduled-duration=1d --labels=lab=16
gcloud kms keys describe $KEY --keyring=$KR --location=$LOC \
  --format="yaml(primary.name,primary.state,versionTemplate,destroyScheduledDuration)"
```

**What you should see:** `primary.state: ENABLED`, algorithm `GOOGLE_SYMMETRIC_ENCRYPTION`, protection level `SOFTWARE`, `destroyScheduledDuration: 86400s`. The 1-day schedule (Google's minimum) is for the lab only — production keys usually keep the 30-day default so a mistaken destroy can be reversed.

### A2. Encrypt directly with KMS (CLI)

```bash
echo "mission data: lab16" > secret.txt
gcloud kms encrypt --key=$KEY --keyring=$KR --location=$LOC \
  --plaintext-file=secret.txt --ciphertext-file=secret.txt.enc
xxd secret.txt.enc | head -3        # unreadable
gcloud kms decrypt --key=$KEY --keyring=$KR --location=$LOC \
  --ciphertext-file=secret.txt.enc --plaintext-file=-
```

Direct KMS encryption is limited to small payloads (⚠️ 64 KiB plaintext limit not re-verified this run) — which is exactly why envelope encryption exists.

### A3. Envelope encryption by hand (CLI)

```bash
# 1. A fresh 256-bit data encryption key (DEK), generated locally (hex so openssl reads it cleanly)
openssl rand -hex 32 > dek.bin
# 2. Encrypt a "large" file locally with the DEK
head -c 2000000 /dev/urandom > bigfile.bin
openssl enc -aes-256-cbc -pbkdf2 -salt -in bigfile.bin -out bigfile.bin.enc -pass file:./dek.bin
# 3. Wrap the DEK with the KMS key (KEK) — only the tiny key file goes to KMS
gcloud kms encrypt --key=$KEY --keyring=$KR --location=$LOC \
  --plaintext-file=dek.bin --ciphertext-file=dek.wrapped
# 4. Throw away the plaintext DEK; keep only ciphertext + wrapped DEK
shred -u dek.bin
ls -l bigfile.bin.enc dek.wrapped
```

Now decrypt the way a service would:

```bash
gcloud kms decrypt --key=$KEY --keyring=$KR --location=$LOC \
  --ciphertext-file=dek.wrapped --plaintext-file=dek.unwrapped
openssl enc -d -aes-256-cbc -pbkdf2 -in bigfile.bin.enc -out bigfile.out -pass file:./dek.unwrapped
cmp bigfile.bin bigfile.out && echo "round trip OK"
shred -u dek.unwrapped
```

**What you just proved:** 2 MB never touched KMS — only the 65-byte DEK file did. Anyone holding `bigfile.bin.enc` and `dek.wrapped` still needs **KMS permission** to read it. (This lab uses `openssl` for clarity; real applications use Google's **Tink** library or the cloud SDKs, which use authenticated modes such as AES-GCM ⚠️ Tink details not re-verified this run.)

### A4. A CMEK bucket — and the kill switch (CLI)

```bash
KEY_PATH=projects/$PROJECT_ID/locations/$LOC/keyRings/$KR/cryptoKeys/$KEY
# Let the Cloud Storage service agent use this one key
gcloud storage service-agent --project=$PROJECT_ID --authorize-cmek=$KEY_PATH
gcloud kms keys get-iam-policy $KEY --keyring=$KR --location=$LOC

gcloud storage buckets create gs://$B --location=$LOC --uniform-bucket-level-access \
  --public-access-prevention --default-encryption-key=$KEY_PATH
gcloud storage buckets update gs://$B --update-labels=lab=16
echo "protected by my key" > cmek.txt && gcloud storage cp cmek.txt gs://$B/
gcloud storage objects describe gs://$B/cmek.txt --format="value(kms_key)"
```

**What you should see:** the IAM policy shows `service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com` with `roles/cloudkms.cryptoKeyEncrypterDecrypter`; the object's key is `.../cryptoKeys/lab16-key/cryptoKeyVersions/1`.

Now pull the switch:

```bash
gcloud kms keys versions disable 1 --key=$KEY --keyring=$KR --location=$LOC
sleep 60
gcloud storage cat gs://$B/cmek.txt || echo ">>> read refused: key version disabled"
gcloud storage ls gs://$B/          # listing still works — metadata isn't under your key
```

**What you should see:** after a short delay (⚠️ propagation time varies; retry after another minute if the read still succeeds) the `cat` fails with a key-related error, while `ls` still lists the object. You — not Google — just made your data unreadable. Turn it back on:

```bash
gcloud kms keys versions enable 1 --key=$KEY --keyring=$KR --location=$LOC
sleep 60
gcloud storage cat gs://$B/cmek.txt
```

### A5. Rotate — and see what rotation does *not* do (CLI)

```bash
gcloud kms keys versions create --key=$KEY --keyring=$KR --location=$LOC --primary
echo "written after rotation" > after.txt && gcloud storage cp after.txt gs://$B/
for o in cmek.txt after.txt; do echo -n "$o -> "; gcloud storage objects describe gs://$B/$o --format="value(kms_key)" | grep -o 'cryptoKeyVersions/[0-9]*'; done
gcloud storage cat gs://$B/cmek.txt     # still readable via version 1
```

**What you should see:** `cmek.txt -> cryptoKeyVersions/1`, `after.txt -> cryptoKeyVersions/2`. Rotation changed the key for **new** data only. Destroying v1 would still crypto-shred `cmek.txt`.

### A6. A secret instead of a password (console, then CLI)

Console tour: **Security → Secret Manager → Create secret**. Note **replication policy** (automatic vs user-managed locations), **rotation** (notifications only), **expiration**, and CMEK. Cancel; use the CLI:

```bash
printf 'db-password-%s' "$RANDOM" | gcloud secrets create lab16-db-pass \
  --data-file=- --replication-policy=user-managed --locations=$LOC --labels=lab=16
gcloud secrets versions access latest --secret=lab16-db-pass; echo
gcloud secrets get-iam-policy lab16-db-pass
```

The secret is readable by you because you're Owner on the project — inherited, not granted on the secret. In real use you'd grant **one** service account `roles/secretmanager.secretAccessor` on **this** secret only, and the workload would read it at startup (Cloud Run can mount it directly).

### A7. What the logs show (CLI)

```bash
gcloud logging read 'protoPayload.serviceName="cloudkms.googleapis.com"' --freshness=2h --limit=10 \
  --format="table(timestamp,protoPayload.methodName,logName.basename())"
```

**What you should see:** `CreateKeyRing`, `CreateCryptoKey`, `UpdateCryptoKeyVersion` (your disable/enable), `CreateCryptoKeyVersion`, `SetIamPolicy` — all **Admin Activity** (`cloudaudit.googleapis.com%2Factivity`). You will **not** see your `Encrypt`/`Decrypt` calls: those are **Data Access** logs, off by default. Module 18's lab turns them on.

---

## Part B — AWS (optional): a data key from KMS

CloudShell, as `labadmin`.

```bash
KID=$(aws kms create-key --description "lab16" --tags TagKey=lab,TagValue=16 \
  --query KeyMetadata.KeyId --output text); echo $KID
aws kms generate-data-key --key-id $KID --key-spec AES_256 \
  --query '{Plaintext:Plaintext,Wrapped:CiphertextBlob}' --output json > dk.json
python3 -c 'import json;d=json.load(open("dk.json"));print("plaintext DEK bytes:",len(d["Plaintext"])," wrapped bytes:",len(d["Wrapped"]))'
```

`GenerateDataKey` returns the **same pair you built by hand in A3**: a plaintext DEK to use and discard, and the wrapped copy to store. Then:

```bash
aws ec2 get-ebs-encryption-by-default --query EbsEncryptionByDefault   # false unless you turned it on — per Region
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com \
  --max-results 5 --query 'Events[].EventName'
```

Note the difference from Google: AWS records `GenerateDataKey` in CloudTrail **by default** — KMS cryptographic calls are logged as management events.

## Part C — Azure (optional): a Key Vault secret

Azure Cloud Shell (Bash), as `labadmin`. **Do not enable purge protection** — it can't be turned off and would block cleanup for up to 90 days.

```bash
RG=lab16-rg; KV=lab16kv$RANDOM; az group create -n $RG -l eastus --tags lab=16
az keyvault create -n $KV -g $RG -l eastus --retention-days 7 --tags lab=16
ME=$(az ad signed-in-user show --query id -o tsv)
az role assignment create --assignee $ME --role "Key Vault Secrets Officer" \
  --scope $(az keyvault show -n $KV --query id -o tsv)
sleep 30
az keyvault secret set --vault-name $KV --name db-pass --value "db-password-$RANDOM" --query id -o tsv
az keyvault secret show --vault-name $KV --name db-pass --query value -o tsv
az keyvault show -n $KV --query "properties.{rbac:enableRbacAuthorization,softDelete:enableSoftDelete,retention:softDeleteRetentionInDays,purgeProtection:enablePurgeProtection}"
```

**What you should see:** `rbac: true` (Azure RBAC is the default permission model for new vaults), soft delete on with 7-day retention, purge protection `null`/false. Note that even as subscription Owner you needed a **data-plane** role to read the secret — Azure separates managing the vault from reading its contents.

---

## Verify it worked

| Check | Expected |
|---|---|
| Key | `lab16-key`, SOFTWARE, destroy schedule 1 day |
| Envelope round trip | `round trip OK`; plaintext DEK shredded |
| CMEK object | `kms_key` ends in `cryptoKeyVersions/1` |
| Disabled version | `cat` refused; `ls` works |
| After rotation | new object on version 2; old object still readable |
| Secret | read with `versions access latest` |
| Audit log | Admin Activity KMS events present; no Encrypt/Decrypt entries |
| (B) AWS | DEK pair returned; KMS events in CloudTrail |
| (C) Azure | RBAC vault; secret readable only after data-plane role |

## What to notice (reflection questions)

1. In A4 you disabled one key version. Name two ways that same action could be an **incident** rather than a control.
2. Why did listing objects still work when reading them failed? What does that tell you about what CMEK protects?
3. After A5, what would you need to do to make *all* data use version 2? (Hint: rotation doesn't re-encrypt.)
4. Compare where encrypt/decrypt calls are logged by default on Google vs AWS. Which default would you rather defend in an incident review?
5. The 2025 S3 SSE-C ransomware used a legitimate encryption feature with stolen credentials. Which control from this module stops it, and which from module 14?

## Cleanup

**Google Cloud**

```bash
gcloud storage rm --recursive gs://$B
gcloud secrets delete lab16-db-pass --quiet
for v in 1 2; do gcloud kms keys versions destroy $v --key=$KEY --keyring=$KR --location=$LOC --quiet; done
gcloud kms keys versions list --key=$KEY --keyring=$KR --location=$LOC --format="table(name.basename(),state,destroyTime)"
rm -f secret.txt* bigfile.* dek.wrapped cmek.txt after.txt
gcloud storage ls | grep lab16 || echo "no lab16 buckets"
gcloud secrets list --filter="labels.lab=16" --format="value(name)" | grep . || echo "no lab16 secrets"
```

**What you should see:** both versions in `DESTROY_SCHEDULED` with a `destroyTime` about 24 hours out. They bill (a fraction of a cent) until then.

**Next day (2 minutes):** confirm both versions show `DESTROYED` — destroyed versions are free. Then, optionally, remove the empty resources:

```bash
gcloud kms keys versions delete 1 --key=$KEY --keyring=$KR --location=$LOC --quiet
gcloud kms keys versions delete 2 --key=$KEY --keyring=$KR --location=$LOC --quiet
gcloud kms keys delete $KEY --keyring=$KR --location=$LOC --quiet
gcloud kms keyrings delete $KR --location=$LOC --quiet || echo "keyrings delete not in this gcloud — use the console (Key Management → key ring → Delete) or leave it; an empty key ring costs nothing"
```

(Re-set `PROJECT_ID`, `LOC`, `KR`, `KEY` from Prerequisites in the new Cloud Shell session first.) Deleted names can't be reused.

**AWS**

```bash
aws kms schedule-key-deletion --key-id $KID --pending-window-in-days 7
aws kms describe-key --key-id $KID --query KeyMetadata.KeyState    # PendingDeletion — not billed
rm -f dk.json
```

**Azure**

```bash
az keyvault delete -n $KV -g $RG
az keyvault purge -n $KV -l eastus          # removes the soft-deleted vault immediately
az group delete -n $RG --yes --no-wait
az keyvault list-deleted --query "[?name=='$KV']" -o tsv   # expect empty
```

**Final check — nothing billable remains:** no `lab16` bucket or secret; both Google key versions `DESTROY_SCHEDULED` today and `DESTROYED` tomorrow; the AWS key `PendingDeletion`; no `lab16kv*` vault active or soft-deleted; `lab16-rg` gone.

## Write-up prompt

> On [date] I used Google Cloud KMS in a personal lab to create a software-protected symmetric key and performed envelope encryption by hand — encrypting a file locally with a random data key and wrapping that key with Cloud KMS. I configured a Cloud Storage bucket with a customer-managed encryption key (CMEK), authorized only the Cloud Storage service agent on the key, and verified that disabling the key version blocked reads of protected objects until it was re-enabled. I rotated the key and confirmed that rotation applies only to newly written data, stored a credential in Secret Manager, and confirmed which KMS operations appear in Admin Activity audit logs. [Optional: I generated an AWS KMS data key and created an Azure Key Vault secret using the RBAC permission model.] I destroyed the key versions and deleted all resources afterward.
