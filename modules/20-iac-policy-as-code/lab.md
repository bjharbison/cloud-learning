# 20 Lab — Terraform a secure bucket, find the secret in state, catch drift, and let a guardrail say no

**Cost:** $0 expected. Google Cloud: one empty-ish Cloud Storage bucket (a few bytes) in `us-central1`, inside the always-free 5 GB-month in US regions; org policies cost nothing. AWS (optional): one S3 bucket with a few bytes — fractions of a cent at most. Azure (optional): one resource group and one storage account holding no data — no meaningful charge while empty ⚠️ (Azure storage accounts can bill small transaction amounts; delete it the same session). Terraform itself is free. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Install Terraform in Cloud Shell (Google removed it from the default image in June 2026) and verify the download's checksum.
2. Deploy a Cloud Storage bucket with a **secure configuration** from code: uniform bucket-level access, public access prevention, versioning, labels.
3. Prove that **state holds secrets** even when you mark them `sensitive`.
4. Create **drift** with a console-style change and watch `terraform plan` catch and fix it — then see both changes in the audit log.
5. **Shift left:** scan an insecure version of the code with Checkov.
6. Set a **guardrail as code** (org policy, dry run → enforce) and watch it block a public grant.
7. `terraform destroy` everything.

## Prerequisites

- Modules 00–19 done; budget alerts active.
- Know which module 03 path you're on: **Path 1** (you have an organization and the Organization Policy Administrator role) or **Path 2** (no organization). Step A7 differs.
- Work in a folder **outside** this repository (the lab uses `~/lab20`). Even so, `.gitignore` here already blocks `*.tfstate`, `*.tfvars`, `*.tfplan`, and `.terraform/` — open it and look before you start.

```bash
PROJECT_ID=$(gcloud config get-value project)
BUCKET=lab20-$PROJECT_ID-$RANDOM
echo "$BUCKET"
gcloud services enable storage.googleapis.com
```

---

## Part A — Google Cloud

### A0. Install Terraform into your home directory (CLI)

Cloud Shell's home directory persists between sessions; the rest of the VM doesn't. Install there. Check the [releases page](https://releases.hashicorp.com/terraform/) for the current version — this lab was written against **1.17.0**.

```bash
TFV=1.17.0
mkdir -p ~/bin && cd ~
curl -sSLO https://releases.hashicorp.com/terraform/${TFV}/terraform_${TFV}_linux_amd64.zip
curl -sSLO https://releases.hashicorp.com/terraform/${TFV}/terraform_${TFV}_SHA256SUMS
grep "linux_amd64.zip" terraform_${TFV}_SHA256SUMS | sha256sum -c -
unzip -o terraform_${TFV}_linux_amd64.zip terraform -d ~/bin
rm terraform_${TFV}_linux_amd64.zip terraform_${TFV}_SHA256SUMS
export PATH="$HOME/bin:$PATH"
grep -q 'HOME/bin' ~/.bashrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc   # persists for later sessions
terraform version
```

**What you should see:** `terraform_1.17.0_linux_amd64.zip: OK`, then `Terraform v1.17.0`. The checksum proves the file matches what HashiCorp published. (Full assurance also checks the SHA256SUMS file's **GPG signature** against HashiCorp's public key — that's what you'd do in a real pipeline. After the Trivy incident in the README, you can see why.)

### A1. Write the configuration (CLI)

```bash
mkdir -p ~/lab20 && cd ~/lab20
cat > main.tf <<'EOF'
terraform {
  required_version = ">= 1.11"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

variable "project_id" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "demo_secret" {
  type      = string
  sensitive = true
}

resource "google_storage_bucket" "secure" {
  name                        = var.bucket_name
  location                    = "US-CENTRAL1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # lab only: lets destroy remove a non-empty bucket

  labels = {
    lab        = "20"
    managed_by = "terraform"
  }

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_object" "note" {
  name    = "note.txt"
  bucket  = google_storage_bucket.secure.name
  content = var.demo_secret
}

output "bucket_url" {
  value = google_storage_bucket.secure.url
}
EOF
```

Read it before running it. Each line of the bucket block maps to a module 08 control: **UBLA** (no per-object ACLs), **public access prevention = enforced** (no `allUsers` ever), **versioning** (recover overwritten objects), a **lifecycle rule** (cap old versions so versioning doesn't grow forever), and **labels** for cleanup and cost. `force_destroy` is a lab convenience — in production you'd leave it `false` so `destroy` can't wipe data.

Pass inputs as environment variables, **not** a `.tfvars` file (which is easy to commit by accident):

```bash
export TF_VAR_project_id=$PROJECT_ID
export TF_VAR_bucket_name=$BUCKET
export TF_VAR_demo_secret="lab20-not-a-real-secret-$RANDOM"
```

### A2. init → fmt → validate → plan → apply (CLI)

```bash
terraform init
terraform fmt -check || terraform fmt
terraform validate
terraform plan -out=lab20.tfplan
```

**What you should see:** `init` downloads the Google provider (8.x) into `.terraform/` and writes `.terraform.lock.hcl` (the dependency pin file). `validate` says `Success!`. `plan` shows **2 to add, 0 to change, 0 to destroy** and `content = (sensitive value)` for the object. ⚠️ If `validate` reports an unknown argument, the provider has changed — check the argument on the [registry page for `google_storage_bucket`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) and adjust.

Read the plan the way a reviewer would: is anything public? Is anything being **destroyed**? Then apply exactly that reviewed plan:

```bash
terraform apply lab20.tfplan
terraform state list
gcloud storage buckets describe gs://$BUCKET \
  --format="yaml(name,location,uniform_bucket_level_access,public_access_prevention,versioning_enabled,labels)"
```

**What you should see:** two resources in state, and a bucket with `uniform_bucket_level_access: true`, `public_access_prevention: enforced`, `versioning_enabled: true`, and both labels.

### A3. Find the secret in state (CLI)

```bash
terraform output                       # the secret isn't an output, and plan hid it…
grep -c "$TF_VAR_demo_secret" terraform.tfstate lab20.tfplan 2>/dev/null
grep -o "\"content\": \"[^\"]*\"" terraform.tfstate | head -1
```

**What you should see:** a count of at least 1 for `terraform.tfstate`, and the "secret" in plain text in the `content` attribute. (The binary plan file holds it too, though `grep` may or may not match its compressed contents.) `sensitive = true` hid it from the screen, not from disk. This is why state goes in an encrypted, access-controlled, audited backend — and **never** in git.

**What a remote backend looks like** (read-along — don't add it to this lab, because the state bucket must exist before `init` and outlive the stack):

```hcl
terraform {
  backend "gcs" {
    bucket = "tfstate-agency-prod" # versioned bucket, CMEK, Data Access logs on
    prefix = "network/prod"
  }
}
```

### A4. Make drift, then catch it (CLI)

Play the engineer who "just fixes it in the console":

```bash
gcloud storage buckets update gs://$BUCKET --no-versioning
cd ~/lab20 && terraform plan
```

**What you should see:** `~ update in-place` on the bucket with `enabled = false -> true` inside `versioning`. Terraform noticed reality drifted from code. Put it back:

```bash
terraform apply -auto-approve      # fine here: you just read the plan above
```

Now the audit trail (module 18). Who made each change, and with what tool?

```bash
sleep 30
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND protoPayload.serviceName=\"storage.googleapis.com\" AND protoPayload.resourceName:\"$BUCKET\"" \
  --freshness=1h --limit=10 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail,protoPayload.requestMetadata.callerSuppliedUserAgent)"
```

**What you should see:** `storage.buckets.create` and an `update` with a user agent mentioning **Terraform**, and an `update` with a user agent mentioning **gcloud** — same principal, different tools. In a real org the pipeline would be a service account, so a human principal changing a Terraform-managed resource is itself a detection idea (module 22 uses exactly this user-agent field).

### A5. Shift left: scan an insecure version (CLI)

```bash
mkdir -p ~/lab20-insecure && cd ~/lab20-insecure
sed -e 's/uniform_bucket_level_access = true/uniform_bucket_level_access = false/' \
    -e 's/public_access_prevention    = "enforced"/public_access_prevention    = "inherited"/' \
    -e '/versioning {/,/}/d' ~/lab20/main.tf > main.tf
grep -n "uniform_bucket\|public_access" main.tf

python3 -m venv ~/venv-checkov && ~/venv-checkov/bin/pip install -q checkov
~/venv-checkov/bin/checkov -d ~/lab20-insecure --framework terraform --compact | tail -40
~/venv-checkov/bin/checkov -d ~/lab20 --framework terraform --compact | tail -15
```

**What you should see:** failed checks on the insecure copy for uniform bucket-level access, public access prevention, and versioning ⚠️ (check IDs and wording vary by Checkov version), and fewer failures on the original. Some checks will still fail on the "secure" one (for example, access logging or CMEK) — read them and decide which you'd accept for a lab. That judgment is the job. Note this scanned only files; nothing was deployed from the insecure copy.

### A6. Guardrail as code (Path 1: you have an organization)

You'll enforce public access prevention for the whole **project** with an org policy written as a file — first dry run, then enforce.

```bash
gcloud org-policies describe storage.publicAccessPrevention --project=$PROJECT_ID --effective
```

If it already shows `enforce: true` (inherited from your org, e.g., via a baseline), note that and still do the steps — you'll be setting it explicitly at the project.

```bash
cd ~/lab20
cat > pap-dryrun.yaml <<EOF
name: projects/$PROJECT_ID/policies/storage.publicAccessPrevention
dryRunSpec:
  rules:
  - enforce: true
EOF
gcloud org-policies set-policy pap-dryrun.yaml --update-mask=dryRunSpec
# ⚠️ Dry-run support depends on the constraint type; if this legacy constraint rejects dryRunSpec, skip to the enforce step.

cat > pap.yaml <<EOF
name: projects/$PROJECT_ID/policies/storage.publicAccessPrevention
spec:
  rules:
  - enforce: true
EOF
gcloud org-policies set-policy pap.yaml --update-mask=spec
gcloud org-policies describe storage.publicAccessPrevention --project=$PROJECT_ID
```

Wait a few minutes (changes can take up to 15), then test it against a bucket that was **not** built with public access prevention — the kind ClickOps creates:

```bash
gcloud storage buckets create gs://$BUCKET-clickops --location=us-central1 \
  --uniform-bucket-level-access --no-public-access-prevention
gcloud storage buckets add-iam-policy-binding gs://$BUCKET-clickops \
  --member=allUsers --role=roles/storage.objectViewer
```

**What you should see:** the `allUsers` grant **fails** — the org policy enforces public access prevention on every bucket in the project, whatever the bucket's own setting says. **Read the error:** it names the constraint that denied you. If it names `iam.allowedPolicyMemberDomains` (domain-restricted sharing, part of the security baseline for newer organizations), a different guardrail stopped the grant before public access prevention was even evaluated — two layers saying no. That's the difference between a configuration (one bucket) and a guardrail (all of them, including the ones nobody reviewed). The empty bucket was never public; nothing was exposed.

Store `pap.yaml` in git next to your Terraform in a real setup — or manage it in Terraform with the `google_org_policy_policy` resource ⚠️ (resource name not re-verified this run). That's policy as code.

### A6 (Path 2: no organization)

Projects without an organization can't use org policies; Google's guidance is to set public access prevention on each bucket — which your Terraform did. Read the Path 1 steps and answer: what stops the *next* engineer from creating a public bucket in this project? (Answer: nothing but review. That's the argument for having an organization.) **Do not** test an `allUsers` grant without a guardrail.

---

## Part B — AWS (optional): the same bucket in Terraform

AWS CloudShell doesn't include Terraform. Its `$HOME` (1 GB) persists, so install the same way as A0 (as `labadmin`), then:

```bash
mkdir -p ~/lab20 && cd ~/lab20
cat > main.tf <<'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" # ⚠️ check the registry for the current major version
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "secure" {
  bucket_prefix = "lab20-"
  force_destroy = true # lab only
  tags = {
    lab        = "20"
    managed_by = "terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "secure" {
  bucket                  = aws_s3_bucket.secure.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secure" {
  bucket = aws_s3_bucket.secure.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket" {
  value = aws_s3_bucket.secure.id
}
EOF
terraform init && terraform validate && terraform plan -out=b.tfplan && terraform apply b.tfplan
aws s3api get-public-access-block --bucket $(terraform output -raw bucket)
```

**What to notice:** AWS splits one bucket into several Terraform resources (public access block, versioning, encryption…) — and new buckets already block public access and encrypt by default (module 08), so the code makes the defaults explicit and reviewable. A real AWS backend would be `backend "s3"` with `use_lockfile = true` (DynamoDB locking is deprecated).

## Part C — Azure (optional): Terraform is preinstalled

Azure Cloud Shell includes Terraform with authentication preconfigured. **If you use ephemeral mode, your state file disappears when the session ends** — so destroy before you close it. (That's a live lesson in why state needs a remote backend.)

```bash
mkdir -p ~/lab20 && cd ~/lab20
SUB=$(az account show --query id -o tsv)
cat > main.tf <<'EOF'
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # ⚠️ check the registry for the current major version
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  type = string
}

resource "random_string" "sfx" {
  length  = 8
  upper   = false
  special = false
}

resource "azurerm_resource_group" "lab" {
  name     = "lab20-rg"
  location = "eastus"
  tags     = { lab = "20" }
}

resource "azurerm_storage_account" "secure" {
  name                            = "lab20${random_string.sfx.result}"
  resource_group_name             = azurerm_resource_group.lab.name
  location                        = azurerm_resource_group.lab.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = { lab = "20" }
}
EOF
export TF_VAR_subscription_id=$SUB
terraform init && terraform validate && terraform plan -out=c.tfplan && terraform apply c.tfplan
az storage account show -g lab20-rg -n $(az storage account list -g lab20-rg --query "[0].name" -o tsv) \
  --query "{publicBlob:allowBlobPublicAccess, tls:minimumTlsVersion}"
az policy assignment list --query "[].{name:displayName, mode:enforcementMode}" -o table
```

**What to notice:** `allow_nested_items_to_be_public = false` is Terraform's name for the `AllowBlobPublicAccess=false` setting from module 08. The last command lists any Azure Policy assignments on your subscription (module 03's location policy, if you kept it; Defender's default initiative, module 21) and whether each is `Default` (enforced) or `DoNotEnforce` (dry run). Destroy now (see Cleanup) if you're in ephemeral mode.

---

## Verify it worked

| Check | Expected |
|---|---|
| Terraform checksum | `OK` |
| `plan` before apply | 2 to add; object content shown as `(sensitive value)` |
| Bucket | UBLA true, PAP enforced, versioning on, labels `lab=20`, `managed_by=terraform` |
| State | Contains the demo secret in plain text |
| Drift | `plan` shows versioning `false -> true`; apply restores it |
| Audit log | Terraform and gcloud user agents on the same bucket |
| Checkov | Insecure copy fails UBLA/PAP/versioning checks |
| (Path 1) Org policy | `allUsers` grant on the ClickOps bucket refused |

## What to notice (reflection questions)

1. Your plan hid the secret, but state didn't. Name two ways a real attacker could read a state file, and the control that stops each.
2. Drift was fixed by re-applying code. During an incident (module 23) a responder makes an emergency console change. What happens on the next pipeline run, and what process prevents it?
3. Which layer caught which problem today: Checkov (code), `plan` (review), org policy (cloud), audit log (after the fact)? Which would have caught a ClickOps public bucket?
4. Google enforces some guardrails by default for new organizations; AWS and Azure leave guardrails to you. Which default would you rather explain to an agency CISO, and why?
5. Map today's Path 1 org policy to its AWS (SCP, RCP, or S3 account-level Block Public Access) and Azure (Azure Policy) equivalents. Which of them would also bind the AWS management account?

## Cleanup

**Google Cloud**

```bash
cd ~/lab20
terraform destroy -auto-approve        # removes the object and the bucket from state and the cloud
gcloud storage rm --recursive gs://$BUCKET-clickops 2>/dev/null || echo "no clickops bucket"
gcloud org-policies delete storage.publicAccessPrevention --project=$PROJECT_ID 2>/dev/null || echo "no project org policy (Path 2)"
cd ~ && rm -rf ~/lab20 ~/lab20-insecure ~/venv-checkov
gcloud storage ls | grep lab20 || echo "no lab20 buckets"
gcloud org-policies list --project=$PROJECT_ID
```

**What you should see:** `Destroy complete! Resources: 2 destroyed.`, no `lab20` buckets, and no `storage.publicAccessPrevention` policy set **at the project** (an inherited org-level one may still apply — that's fine). Deleting `~/lab20` removes the local state file with the demo secret. Keep `~/bin/terraform` for later modules, or `rm ~/bin/terraform`.

**AWS**

```bash
cd ~/lab20 && terraform destroy -auto-approve && cd ~ && rm -rf ~/lab20
aws s3 ls | grep lab20 || echo "no lab20 buckets"
```

**Azure**

```bash
cd ~/lab20 && terraform destroy -auto-approve && cd ~ && rm -rf ~/lab20
az group exists -n lab20-rg       # false
```

If your Azure Cloud Shell session ended before you destroyed (state lost), delete it directly: `az group delete -n lab20-rg --yes`.

**Final check — nothing billable remains:** no `lab20` Cloud Storage or S3 buckets, no `lab20-rg`, no project-level org policy you added, and no local state files left in any cloud shell.

## Write-up prompt

> On [date] I used Terraform in a personal lab to deploy a Google Cloud Storage bucket with uniform bucket-level access, enforced public access prevention, versioning, a lifecycle rule, and labels, after verifying the Terraform download's checksum. I demonstrated that a value marked `sensitive` is still stored in plain text in Terraform state, created configuration drift with a manual change, detected it with `terraform plan`, restored the coded configuration, and traced both changes to different tools in Cloud Audit Logs. I scanned an intentionally insecure version with Checkov and [Path 1: enforced the `storage.publicAccessPrevention` org policy on a project via a policy file (dry run, then enforce) and confirmed it blocked a public grant]. [Optional: I deployed equivalent secure storage on AWS and Azure with Terraform.] I destroyed all resources afterward.
