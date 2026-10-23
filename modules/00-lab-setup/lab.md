# 00 Lab — Lab environment

**Cost:** $0. Nothing in this lab creates a billable resource. Budgets, IAM Identity Center, AWS Organizations, Entra users, and the cloud shells are free (Azure Cloud Shell is free in **ephemeral** mode; persistent mode creates an Azure Files share). · **Time:** 2–3 hours · **Clouds:** all three (GCP required)

## Goal

Three personal sandboxes where:

1. The top-level identity has phishing-resistant MFA and is put away.
2. A separate admin identity does daily work.
3. A budget alert fires long before anything costs real money.
4. You can open a cloud shell and know which account/project you're in.

## Prerequisites

- A **dedicated email** for these labs (not work, not your everyday personal inbox). A new Gmail works for Google Cloud and as the sign-up address for AWS and Azure.
- A credit or debit card (all three require one for identity verification; none charges it during the trial unless you upgrade).
- A phone with an authenticator app, and ideally a **FIDO2 security key** or a platform **passkey** (phone or laptop).
- A password manager.
- Read [`reference/lab-safety.md`](../../reference/lab-safety.md).

> Write down each cloud's **trial end date** in `PROGRESS.md` notes as you go: Google = sign-up + 90 days; AWS = sign-up + 6 months (or when credits run out); Azure = sign-up + 30 days.

---

## Part A — Google Cloud

### A1. Secure the Google Account (console)

1. Sign in at `myaccount.google.com` with your lab Google Account → **Security** → **2-Step Verification** → turn it on.
2. Add a **passkey** or **security key** as the primary factor. Add an authenticator app as backup. Save the backup codes in your password manager.
3. Remove SMS as a factor once the others work, if your account lets you.

### A2. Start the Free Trial

1. Go to `console.cloud.google.com`, accept the terms, and start the **Free Trial** ($300 / 90 days).
2. Note: the trial **doesn't auto-upgrade**. Leave it that way.
3. Look at **IAM & Admin → Manage resources**. Do you see an organization (e.g., `yourname-org`) or **No organization**? New Free Trial sign-ups may get a **standalone organization** automatically; existing accounts don't. Write down which you got — module 03 depends on it.

### A3. Create a lab project (console, then CLI)

Console: project picker → **New project** → name `lab-00-<yourinitials>` → Create.

CLI (in Cloud Shell — click the `>_` icon top right):

```bash
gcloud auth list                         # confirm you're the lab account
gcloud projects create lab-00-bh-$RANDOM --name="lab-00" --labels=lab=00
gcloud projects list
gcloud billing accounts list             # note the ACCOUNT_ID
gcloud billing projects link PROJECT_ID --billing-account=ACCOUNT_ID
```

Project IDs must be 6–30 characters, lowercase letters/digits/hyphens, and can't be changed later.

### A4. Set up a gcloud configuration

```bash
gcloud config configurations create lab
gcloud config set project PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config list
gcloud config configurations list
```

Why `us-central1`? It's one of the three regions where the always-free e2-micro applies.

### A5. Budget alert (console, then CLI)

Console: **Billing → Cost management → Budgets & alerts → Create budget**.

- Scope: the whole billing account.
- Amount: **$10**.
- Thresholds: add **10%** to the defaults (50%, 90%, 100%).
- Credits: **uncheck** "include credits" so the budget tracks gross usage. Otherwise your $300 credit hides spending and alerts won't fire during the trial.

CLI equivalent (if prompted, enable the Cloud Billing Budget API):

```bash
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="lab-monthly-10" \
  --budget-amount=10USD \
  --credit-types-treatment=exclude-all-credits \
  --threshold-rule=percent=0.10 \
  --threshold-rule=percent=0.50 \
  --threshold-rule=percent=0.90 \
  --threshold-rule=percent=1.0

gcloud billing budgets list --billing-account=ACCOUNT_ID
```

Percents are fractions (`0.50` = 50%).

### A6. (Optional) A separate daily-use identity

Google Cloud has no "root user," but your lab Google Account is the most powerful identity you have. If you want a daily-use identity: create a second Google Account, then **IAM & Admin → IAM → Grant access** on the `lab-00` project with the **Editor** role. Keep the first account for billing and org-level changes. (Module 14 explains why Editor is still too broad for production.)

---

## Part B — AWS

### B1. Create the account and lock down root (console)

1. Sign up at `aws.amazon.com`. Choose the **Free plan** (not Paid). This is what prevents charges.
2. Sign in as root → account menu → **Security credentials** → **Multi-factor authentication** → **Assign MFA device**. Use a **passkey or security key** (AWS's recommendation). Register a second device as backup.
3. On the same page, confirm there are **no access keys** for root. Never create them.
4. Store the root password and recovery info in your password manager. From here on, you'll use root only for account-level tasks.

### B2. Create a daily admin with IAM Identity Center (console)

1. Console → **IAM Identity Center** → **Enable**. Choose the **organization instance**; this enables **AWS Organizations** (free) with your account as the management account.
2. **Users → Add user** → `labadmin`, your lab email. Accept the invitation email and set a password; register MFA when prompted.
3. **Permission sets → Create permission set** → predefined **AdministratorAccess**.
4. **AWS accounts** → select your account → **Assign users or groups** → `labadmin` → AdministratorAccess.
5. Bookmark the **AWS access portal URL** shown on the Identity Center dashboard. That's your daily login from now on.

> **Why not an account instance?** Account instances don't support permission sets, so they can't grant access to the AWS account itself.

**Fallback** (if Identity Center gives you trouble): IAM → Users → Create user `labadmin`, console access, attach `AdministratorAccess`, enforce MFA. It works, but it's a long-lived credential. Plan to replace it.

### B3. Budget alert (console)

1. Sign in through the access portal as `labadmin`.
2. **Billing and Cost Management → Budgets → Create budget → Use a template**.
3. Create the **Zero spend budget** (alerts when spend exceeds free-tier limits).
4. Create a **Monthly cost budget** of **$10**.
5. Doing this also completes one of the free plan's $20 credit activities. Check **Billing → Credits** (or the Free Tier page) to see it.

### B4. CloudShell (CLI)

Click the CloudShell icon in the console toolbar. Then:

```bash
aws sts get-caller-identity     # who am I? Should show the labadmin role session, not root
aws configure list
aws budgets describe-budgets --account-id $(aws sts get-caller-identity --query Account --output text)
```

Note the region in the toolbar: CloudShell storage (1 GB) is **per Region**.

---

## Part C — Azure

### C1. Create the free account (console)

1. Sign up at `azure.microsoft.com/free` with your lab email. You get **$200 for 30 days** and a **spending limit**. Don't remove the spending limit.
2. Sign-up creates a **Microsoft Entra ID tenant** and a **subscription**. MFA is mandatory for the Azure portal; register a **passkey or Microsoft Authenticator** when prompted.

### C2. Create a daily admin (console, then CLI)

Console:

1. **Microsoft Entra ID → Users → New user → Create new user** → `labadmin@<yourtenant>.onmicrosoft.com`.
2. **Subscriptions** → your subscription → **Access control (IAM)** → **Add role assignment** → **Owner** → assign to `labadmin`. (Owner on the subscription manages resources. It is *not* Global Administrator of the tenant — keep that separation.)
3. Sign in as `labadmin` in a private browser window and register MFA.

CLI equivalent in Cloud Shell (run as your sign-up identity):

```bash
az account show --output table
SUB_ID=$(az account show --query id -o tsv)
az ad user create \
  --display-name "Lab Admin" \
  --user-principal-name labadmin@<yourtenant>.onmicrosoft.com \
  --password '<generate-in-password-manager>' \
  --force-change-password-next-sign-in true
az role assignment create --assignee labadmin@<yourtenant>.onmicrosoft.com \
  --role Owner --scope /subscriptions/$SUB_ID
```

Never paste a real password into a file in this repo.

### C3. Budget alert (console)

**Cost Management → Budgets → Add** → scope: your subscription → **$10/month** → alerts at **10% actual**, **50% actual**, **100% forecasted** → your lab email.

### C4. Cloud Shell, ephemeral mode

Click the Cloud Shell icon → choose **Bash** → when asked about storage, choose **No storage account required** (ephemeral). Then:

```bash
az account show --output table
az ad signed-in-user show --query userPrincipalName -o tsv
```

---

## Part D — Local CLIs (optional)

Only if you want them on your laptop. Use each vendor's official installer:

- `gcloud`: [Install the gcloud CLI](https://docs.cloud.google.com/sdk/docs/install) → then `gcloud init`
- `aws` (v2): [Install the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) → then `aws configure sso` (uses your Identity Center user; no long-lived keys)
- `az`: [Install the Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) → then `az login`

Check: `gcloud --version`, `aws --version`, `az version`.

---

## Verify it worked

| Check | Google Cloud | AWS | Azure |
|---|---|---|---|
| MFA on top-level identity | Google Account → Security shows 2SV on, passkey/key listed | Root → Security credentials shows MFA device(s) | Sign-up identity prompts for MFA at portal sign-in |
| Separate admin works | (Optional) second account sees `lab-00` | Access portal login → `sts get-caller-identity` shows `AWSReservedSSO_AdministratorAccess…` | `labadmin` can open the subscription |
| Budget exists | `gcloud billing budgets list` shows `lab-monthly-10` | Budgets page shows zero-spend + $10 monthly | Cost Management → Budgets shows $10 |
| Shell works | `gcloud config list` shows `lab` config | `aws sts get-caller-identity` | `az account show` |

## What to notice (reflection questions)

1. Which cloud made it easiest to *not* work as the top-level identity? Which made it hardest?
2. Why does including credits in a Google Cloud budget make it useless during the trial?
3. In AWS, the "best practice" admin path required turning on AWS Organizations. What does that tell you about how AWS expects customers to grow?
4. Owner (Azure RBAC) vs Global Administrator (Entra): which would an attacker want more, and why?
5. In intel terms: what is your baseline now, and which of today's settings would show you a deviation?

## Cleanup

This lab created **no billable resources**. Keep the accounts, admins, and budgets — every later lab depends on them. Do confirm:

**Google Cloud**

```bash
gcloud compute instances list --project=PROJECT_ID   # expect: Listed 0 items (or API not enabled)
gcloud billing budgets list --billing-account=ACCOUNT_ID
```

Optional: delete the `lab-00` project if you don't want to reuse it (`gcloud projects delete PROJECT_ID`; it goes into a 30-day pending-deletion state).

**AWS**

- Billing and Cost Management → **Bills**: current month $0.00.
- CloudShell: nothing to delete (storage is free; it's removed after 120 days without use).

**Azure**

- **Cost Management → Cost analysis**: $0.00.
- **Resource groups**: if you accidentally chose persistent Cloud Shell storage, you'll see a group like `cloud-shell-storage-<region>`. Delete it:

```bash
az group list --output table
az group delete --name <cloud-shell-storage-group> --yes
```

**Final check — nothing billable remains:** all three billing pages show $0 current-month charges, and each budget exists with your email as recipient.

> **When the curriculum ends:** Google Cloud trial resources stop automatically; AWS free-plan accounts close if not upgraded; Azure free accounts are disabled if not upgraded. If you upgraded any of them, close the account deliberately rather than abandoning it.

## Write-up prompt

Paste into `PROGRESS.md` notes or your lab journal:

> On [date] I set up personal Google Cloud, AWS, and Azure lab environments. I enforced phishing-resistant MFA on each top-level identity, created separate daily admin identities (AWS IAM Identity Center with an AdministratorAccess permission set; an Entra ID user with Owner on the Azure subscription), and configured budget alerts on all three, excluding credits on Google Cloud so alerts reflect real usage. Trial end dates: GCP ___, AWS ___, Azure ___.
