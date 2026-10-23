# 00 — Lab environment: free-tier accounts, MFA, budget alerts, CLIs, cloud shells

> **In one sentence:** you'll have three locked-down personal sandboxes (Google Cloud, AWS, Azure) with MFA, a non-root admin, budget alerts, and a working command line — so every later lab is safe and cheap.

**Prereqs:** none · **Time:** ~3 hours incl. lab · **Phase:** 0

## Learning objectives

- Explain what you actually get when you "sign up" for each cloud: an identity, a billing relationship, and a container for resources.
- Describe the current (late-2026) free-trial and free-tier terms on all three clouds, and how each one ends.
- Secure the top-level identity on each cloud with phishing-resistant MFA, and stop using it day to day.
- Set budget alerts and explain why they **notify** but don't **stop** spending.
- Use each provider's browser-based cloud shell, and set up `gcloud` configurations.

## Why this matters for the target roles

- **Customer engineer / architect:** the first hour of every proof of concept is account, identity, and billing setup. Doing it cleanly is a credibility signal.
- **Cloud security:** the most common cloud breach pattern starts with a stolen credential on an over-privileged identity. Root/owner hygiene is control #1.
- **CTI:** compromised cloud accounts get used for crypto-mining and as attack infrastructure. Knowing what "normal" setup looks like helps you spot abnormal.

---

## Concepts

### What "signing up" creates

Each cloud gives you three separate things at sign-up. They have different names, and the differences matter later.

| Thing | Google Cloud | AWS | Azure |
|---|---|---|---|
| The **identity** you log in with | A **Google Account** (e.g., a Gmail address) | The **root user** (the email you signed up with) | A **Microsoft account** or work account, which becomes an admin in a new **Microsoft Entra ID tenant** |
| The **billing relationship** | A **Cloud Billing account** | The AWS **account** itself is the billing unit | A **subscription** tied to a billing account |
| The **container** for resources | A **project** | The AWS **account** | A **subscription**, then **resource groups** inside it |

**Plain version:** AWS bundles identity, billing, and resources into one "account." Google and Microsoft separate them. Module 03 goes deep on this; for now just notice that "account" means different things on each cloud.

**Bridge:** think of your homelab. Your Proxmox root login, your ISP bill, and your Proxmox cluster are three different things. Google and Azure model them separately; AWS glues them together.

### Free trials vs free tiers (as of 2026-10-23)

Two different ideas, often confused:

- **Free trial / credits:** a dollar amount you can spend on almost anything, for a limited time.
- **Free tier / always free:** specific services with monthly usage limits that stay free (until the provider changes the terms).

| | Google Cloud | AWS (accounts created on/after 2025-07-15) | Azure |
|---|---|---|---|
| Credits | **$300** Welcome credit | **$100** at sign-up, plus up to **$100** more ($20 each for five starter activities) | **$200** |
| Credit window | **90 days** | Free plan lasts **6 months** or until credits run out | **30 days** |
| At the end | **Does not auto-upgrade.** Resources stop; ~30-day grace to upgrade and recover, then deleted | Free plan ends; you have **90 days** to upgrade to a paid plan to reopen the account | You must **upgrade to pay-as-you-go** (remove the spending limit), or the account and services are disabled |
| Always free | e.g., 1 **e2-micro** VM/month in us-west1, us-central1, or us-east1; 30 GB-month standard persistent disk; 5 GB-month Cloud Storage in US regions; Cloud Shell with 5 GB home | "Over 30" always-free services on the free plan | 65+ always-free services, plus 20+ services free for 12 months |
| Restrictions during trial | No GPUs, no Windows Server VMs, no quota increases, no Marketplace; crypto-mining prohibited | Free plan blocks some services typically used by large enterprises | Spending limit on by default |

Two things to notice:

1. **AWS restructured its free tier in July 2025.** Older articles describing "12 months free" for new AWS accounts are out of date. Accounts created before 2025-07-15 stay on the legacy program.
2. **Two of three trials protect you by default.** Google's trial doesn't auto-bill, AWS's free plan won't charge until you upgrade, and Azure's free account has a spending limit. Once you upgrade any of them, that safety net is gone — which is why budget alerts matter.

### The top-level identity and MFA

Every cloud has an identity that can do *anything*, including close the account or change billing.

- **AWS root user:** has unrestricted access to the account. AWS now **requires** MFA on the root user for all account types; if it isn't set, you must register it within 14 days of first console sign-in. Supported: passkeys and security keys (AWS's recommendation), authenticator apps, hardware TOTP tokens.
- **Google Account:** Google Cloud is phasing in a **2-Step Verification (2SV) requirement**. For personal accounts (including Gmail) used with Google Cloud, it applies on or after **2025-05-12**. The console requires it; `gcloud` doesn't enforce its own check but inherits 2SV once it's on your account.
- **Azure / Entra ID:** Microsoft enforces **mandatory MFA** for Azure sign-ins. Phase 1 (since October 2024) covers the Azure portal and admin centers. Phase 2 (enforcement date October 1, 2025; tenants could postpone to July 1, 2026) covers create/update/delete actions through Azure CLI, PowerShell, IaC tools, and the REST API. Every tenant, including free ones; no opt-out. It applies to public Azure only, not Azure Government.

**Practitioner vocabulary:**

- **Phishing-resistant MFA** — a factor bound to the real site, so a fake login page can't relay it. Passkeys/FIDO2 security keys qualify. SMS and push prompts do not.
- **Break-glass account** — an emergency admin identity you rarely use, protected heavily, and monitored for any use.

**Bridge:** the root user is your safe combination. You write it down, lock it in a drawer, and alarm the drawer. You don't use it to open the office every morning.

### A non-root admin for daily work

The rule: **create a separate admin identity and use that.** How it looks on each cloud:

- **AWS:** AWS recommends **IAM Identity Center** for human users. Its **organization instance** supports **permission sets** (bundles of permissions you assign to a user for an account). An **account instance** does *not* support permission sets, so it can't give you access to the AWS account itself. In practice that means enabling **AWS Organizations** (free) first. Fallback for a solo lab: an **IAM user** with MFA — workable, but AWS discourages long-lived IAM users for people.
- **Azure:** create a **cloud-only user** in your tenant (e.g., `labadmin@<yourtenant>.onmicrosoft.com`) and give it the **Owner** role on your subscription. Owner is an Azure RBAC role for resources; it is *not* the same as **Global Administrator**, which controls the Entra tenant itself. Keep the sign-up identity as break-glass.
- **Google Cloud:** there's no AWS-style root user. Power comes from roles in the hierarchy (organization, billing account, project). The cleanest personal pattern is a **dedicated Google Account just for labs**, with 2SV. If you signed up as a new Free Trial customer, Google may have created a **standalone organization** for you, and your account holds the Organization Owner and Organization Administrator roles (module 03 explores this).

> **Shared responsibility, first appearance:** who can log in, with what factor, and with what permissions is **always the customer's job** — on every cloud, in every service model. The provider gives you MFA and IAM; it doesn't configure them for you.

### Budgets: alarms, not circuit breakers

A **budget** compares your spend to a number you set and sends alerts at thresholds.

- **Google Cloud:** Billing → Cost management → **Budgets & alerts**. Default thresholds are **50%, 90%, and 100%** of actual spend. An alerts-only budget **doesn't cap** usage.
- **AWS:** **AWS Budgets**, with templates including a **Zero spend budget** (alerts once spend passes free-tier limits) and a **Monthly cost budget**. Setting a Budgets alert is also one of the five $20 credit activities on the new free plan.
- **Azure:** **Cost Management → Budgets**. Alerts on **actual or forecasted** cost. Microsoft says plainly that resources aren't affected and consumption isn't stopped. Budgets are evaluated about every 24 hours, and cost data can lag 8–24 hours.

**The lag matters.** A runaway resource can spend for a day before an alert fires. Your real protection is (1) the trial safety nets above, (2) small instances, and (3) the cleanup step at the end of every lab.

### Cloud shells

A **cloud shell** is a small, temporary Linux VM in your browser, already authenticated as you, with the CLIs preinstalled. No credentials land on your laptop.

| | Google Cloud Shell | AWS CloudShell | Azure Cloud Shell |
|---|---|---|---|
| Cost | Free | Free (1 GB storage per Region at no cost) | Free compute; persistent mode stores files in an Azure Files share in your subscription |
| Persistent home | **5 GB** | **1 GB per Region** | Optional (Azure Files); or **ephemeral** with no storage account |
| Home deleted after | **120 days** with no access | **120 days** after last session in that Region | Ephemeral: at session end |
| Notable limits | **50 hours/week** default; 12-hour max session; VM ends after 40 min inactive | Up to 10 shells per Region; idle timeout ~20–30 min | Choose Bash or PowerShell |

**Recommendation for this curriculum:** use Azure Cloud Shell's **ephemeral** mode. It avoids creating a storage account you'd have to remember to clean up.

### Local CLIs (optional)

You can install `gcloud`, `aws`, and `az` on your laptop. It's optional — every lab works in the cloud shells. If you do install them, the trade-off is that credentials now live on your device. Treat your laptop like a jump box: disk encryption, screen lock, and no shared accounts.

### `gcloud` configuration basics

`gcloud` keeps **properties** (account, project, default region/zone) in named **configurations**. Think of a configuration as an SSH config `Host` block: a saved context you switch into.

```bash
gcloud config list                          # what context am I in?
gcloud config configurations create lab     # new named context
gcloud config set project PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config configurations list
gcloud config configurations activate default
```

**Why it matters:** the classic mistake is running a destructive command in the wrong project. Always run `gcloud config list` before anything that deletes.

---

## Text diagram

```
                    YOU (phone with passkey / security key)
                                 │ phishing-resistant MFA
     ┌───────────────────────────┼────────────────────────────┐
     ▼                           ▼                            ▼
 GOOGLE CLOUD                   AWS                          AZURE
 Google Account (2SV)       Root user (MFA, locked away)  Sign-up identity (break-glass)
   │                          │                             │
   ├─ Billing account         ├─ AWS Organizations (free)   ├─ Entra ID tenant
   │   └─ Budget 50/90/100%   │   └─ IAM Identity Center    │   └─ labadmin user (MFA)
   │                          │       └─ admin user ──┐     │
   └─ Project "lab-00"        └─ Account ◄────────────┘     └─ Subscription ◄─ Owner role
        └─ Cloud Shell            ├─ AWS Budgets                 ├─ Budget (actual/forecast)
                                  └─ CloudShell                  └─ Cloud Shell (ephemeral)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Sign-up credit | $300 / 90 days | $100 + up to $100 / 6-month free plan | $200 / 30 days | Azure's window is shortest; AWS's is longest |
| Ends automatically without billing? | Yes (no auto-upgrade) | Yes (free plan) | Yes (spending limit) | All three require an explicit upgrade to start charging |
| Top-level identity | Google Account | Root user | Sign-up identity → Entra tenant admin | Only AWS has a distinct "root user" concept |
| MFA requirement | 2SV required (personal accounts from 2025-05-12) | Root MFA required, all account types | Mandatory MFA, Phases 1 and 2 | All three now *require* MFA; none require phishing-resistant MFA — that's your choice |
| Recommended daily admin | Dedicated Google Account with scoped roles | IAM Identity Center user | Cloud-only Entra user with Owner on the subscription | AWS's best path needs AWS Organizations |
| Budget tool | Budgets & alerts | AWS Budgets | Cost Management budgets | Azure offers forecast-based alerts prominently; AWS has a zero-spend template |
| Browser shell | Cloud Shell | CloudShell | Cloud Shell | Azure's can be fully ephemeral |
| CLI | `gcloud` | `aws` | `az` | `gcloud` uses named configurations; `aws` uses named profiles; `az` uses one active subscription at a time |

## Administer and monitor it

Daily-ish checks, five minutes per cloud:

- **Billing view:** Google Cloud Billing reports; AWS Billing and Cost Management home; Azure Cost Management cost analysis.
- **Who signed in:** Google Cloud audit logs (module 18) and your Google Account's security page; AWS CloudTrail event history (console sign-ins and root activity show up here); Microsoft Entra sign-in logs.
- **Alert inbox:** make sure budget emails go to an inbox you actually read on your phone.

## Security angle

What goes wrong on a fresh account:

- **Root/owner used daily.** One phished session = total loss. Fix: MFA plus a separate admin.
- **Long-lived access keys.** AWS root access keys or a downloaded Google service-account key in a repo. Fix: don't create them; this repo's `.gitignore` blocks common key files, but check `git status` anyway.
- **SMS as the only factor.** Vulnerable to SIM swapping. Fix: passkey or security key, authenticator app as backup.
- **No alerting.** A stolen account mining crypto for a week. Fix: budgets now; anomaly detection later (module 04).

**Shared responsibility line:** the provider secures the login service and offers MFA. *You* choose the factors, create the admin identities, scope their permissions, and watch the bills. That's identity and access control — **always yours**.

## Threat intel angle

- **T1078.004 Valid Accounts: Cloud Accounts** — adversaries log in with stolen cloud credentials. It's the dominant initial-access path in cloud intrusions, and why MFA is mandatory now.
- **T1496.001 Resource Hijacking: Compute Hijacking** — compromised accounts spun up for crypto-mining. Budget alerts are a crude but real detection.
- **T1535 Unused/Unsupported Cloud Regions** — attackers launch resources in regions you never use, hoping you aren't watching. Module 02 returns to this.

**Bridge to your CTI work:** a brand-new cloud account is like a new collection platform. The first question is "what's my baseline?" — which regions, which identities, what normal spend looks like. Anomalies only exist relative to a baseline.

## Public sector notes

- **AWS GovCloud (US)** and **Azure Government** are separate environments with their own eligibility checks. You can't sign up for them with a personal free account. Module 27 covers them.
- Microsoft's mandatory-MFA enforcement applies to public Azure only; it isn't currently enforced in Azure Government or other sovereign clouds — those customers manage MFA through their own policies.
- Agencies often prohibit personal accounts for any work data. Your lab accounts are for learning with public data only.

## Key takeaways

- "Account" means different things: AWS bundles identity + billing + resources; Google and Azure separate them.
- Current credits: Google $300/90 days, AWS up to $200 on a 6-month free plan (since July 2025), Azure $200/30 days. None auto-bill.
- All three clouds now **require** MFA on top-level identities. Choose phishing-resistant factors.
- Don't work as root/owner. AWS → Identity Center; Azure → cloud-only user with Owner; Google → dedicated lab account.
- Budgets **alert**; they don't **stop** spend. Cleanup is your real control.
- Identity and access configuration is **always the customer's responsibility**.

## Sources

- [Google Cloud — Free cloud features and trial offer](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Google Cloud — 2-step verification requirement](https://docs.cloud.google.com/docs/authentication/mfa-requirement)
- [Google Cloud — Create, edit, or delete budgets and budget alerts](https://docs.cloud.google.com/billing/docs/how-to/budgets)
- [Google Cloud Shell — Quotas and limits](https://docs.cloud.google.com/shell/docs/quotas-limits)
- [Google Cloud — Set up standalone organizations](https://docs.cloud.google.com/resource-manager/docs/standalone-organization-overview)
- [AWS News Blog — AWS Free Tier update: up to $200 in credits (2025-07-15)](https://aws.amazon.com/blogs/aws/aws-free-tier-update-new-customers-can-get-started-and-explore-aws-with-up-to-200-in-credits)
- [AWS What's New — Free Tier credits and 6-month free plan](https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan/)
- [AWS IAM — MFA for the root user](https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html)
- [AWS IAM Identity Center — Organization and account instances](https://docs.aws.amazon.com/singlesignon/latest/userguide/identity-center-instances.html)
- [AWS IAM Identity Center — Account instances](https://docs.aws.amazon.com/singlesignon/latest/userguide/account-instances-identity-center.html)
- [AWS Cost Management — Budget templates](https://docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html)
- [AWS CloudShell — Service quotas and restrictions](https://docs.aws.amazon.com/cloudshell/latest/userguide/limits.html)
- [Azure — Free account](https://azure.microsoft.com/pricing/purchase-options/azure-account) and [offer terms](https://azure.microsoft.com/offers/ms-azr-0044p/)
- [Microsoft Entra — Mandatory MFA for Azure](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mandatory-multifactor-authentication)
- [Microsoft Entra — Security defaults](https://learn.microsoft.com/en-us/entra/fundamentals/security-defaults)
- [Azure Cost Management — Create and manage budgets](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
- [Azure Cloud Shell — Ephemeral sessions](https://learn.microsoft.com/en-us/azure/cloud-shell/get-started/ephemeral) and [features](https://learn.microsoft.com/en-us/azure/cloud-shell/features)
- [MITRE ATT&CK — T1078.004](https://attack.mitre.org/techniques/T1078/004/), [T1496.001](https://attack.mitre.org/techniques/T1496/001/), [T1535](https://attack.mitre.org/techniques/T1535/)

Verified: 2026-10-23
