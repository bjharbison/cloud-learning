# 27 Lab — Compare the government cloud models hands-on: a free Assured Workloads boundary, partition endpoints, and a scope matrix

**Cost:** $0. Google Cloud Path 1 uses a **free-tier** Assured Workloads package (US Data Boundary or Data Boundary for FedRAMP Moderate — no Assured Workloads charge per Google's pricing page) with one empty test bucket created and deleted. **Do not choose a Premium package** (FedRAMP High, IL2/4/5, ITAR, CJIS, IRS 1075, or any "…and Support") — those add 5–20% of in-folder spend and may need paid support. Path 2 and the AWS/Azure parts are read-only. Nobody needs (or can casually get) a GovCloud or Azure Government account for this lab. · **Time:** 1.5–2 hours · **Clouds:** GCP (required), AWS and Azure (read-only)

## Goal

1. **See a policy boundary work:** create a free Assured Workloads folder and watch it block a non-U.S. resource (Path 1), or inspect the packages and pricing (Path 2).
2. **See a partition boundary:** compare commercial and government endpoints for AWS and Azure without touching a government system.
3. **Build a scope matrix** for a fictional agency workload across all three providers, with dates and sources.
4. **Cost a boundary:** compare Premium-package pricing with a separate-environment model.

## Prerequisites

- Modules 00–26 done; budget alerts on.
- Know your module 03 path: **Path 1** (you have an organization) or **Path 2** (no organization). Assured Workloads requires an organization.
- Cloud Shell.

**Rules of engagement:** don't sign up for, sign in to, or send requests to AWS GovCloud or Azure Government endpoints. Their eligibility rules exist for good reasons; this lab only reads public documentation and local CLI metadata.

---

## Part A — Google Cloud

### Path 1 (organization): a free Assured Workloads folder

**A1. Check roles.** You need Assured Workloads Administrator (`roles/assuredworkloads.admin`) on the organization, plus permission to create folders and projects ⚠️ (role list from Google's IAM docs; check *Create a folder for a control package* for the current list).

```bash
ORG=$(gcloud organizations list --format="value(name)" | head -1); echo $ORG
BILLING=XXXXXX-XXXXXX-XXXXXX          # gcloud billing accounts list
gcloud organizations get-iam-policy $ORG --flatten="bindings[].members" \
  --filter="bindings.members:$(gcloud config get-value account)" --format="value(bindings.role)"
```

If you're missing the Assured Workloads role and you're the org owner, grant it to yourself for the lab:

```bash
gcloud organizations add-iam-policy-binding $ORG \
  --member=user:$(gcloud config get-value account) --role=roles/assuredworkloads.admin --condition=None
```

**A2. Create the folder (console).** Go to **Assured Workloads** (search the console for it) → **Create folder** ⚠️ (button wording may differ). Choose:

- Control package: **US Data Boundary** or **Data Boundary for FedRAMP Moderate** — confirm the screen labels it **Free** before continuing.
- Location: **United States**.
- Folder name: `lab27-aw`.
- Billing account: your lab billing account.
- Leave key-management and optional settings at their defaults.

Creation takes a few minutes. Note the folder ID.

**A3. Inspect what the package set (CLI).**

```bash
FOLDER=<folder-id>
gcloud org-policies list --folder=$FOLDER
```

**What you should see:** several organization policy constraints set on the folder — look for one restricting **resource locations** and one restricting **service usage**. Describe one:

```bash
gcloud org-policies describe gcp.resourceLocations --folder=$FOLDER
```

⚠️ If that constraint name isn't in your list, describe whichever location constraint is. The point: the boundary is **ordinary organization policy** (module 20) applied and monitored by the service.

**A4. Test the boundary (CLI).** Create a project inside the folder and try to create one bucket outside the U.S. and one inside:

```bash
P=lab27-aw-$RANDOM
gcloud projects create $P --folder=$FOLDER --labels=lab=27
gcloud billing projects link $P --billing-account=$BILLING
gcloud storage buckets create gs://$P-eu --location=europe-west1 --project=$P      # expect: denied by org policy
gcloud storage buckets create gs://$P-us --location=us-central1 --project=$P       # expect: success
```

**What you should see:** the `europe-west1` request **fails** with an organization-policy (location constraint) error; the `us-central1` bucket succeeds. That's data residency enforced before anything is created — preventive, not detective.

**A5. Check the monitoring view (console).** Open the workload in **Assured Workloads** and look at **violations** (or the monitoring tab). Then try to break the boundary: in the console, at the `lab27-aw` folder, try to **edit** the location org policy. Note whether it's allowed and whether a violation appears ⚠️ (behavior may depend on package and your roles — record what you see).

**A6. Clean up Path 1 now** (see Cleanup — don't leave the folder around).

### Path 2 (no organization): read the packages and price a boundary

```bash
gcloud assured workloads create --help | sed -n '/--compliance-regime/,/--display-name/p'
```

**What you should see:** the full list of compliance regimes the CLI accepts — both legacy values (`fedramp-high`, `il4`, `il5`) and current "data boundary" names (`data-boundary-for-il5`, `data-boundary-for-fedramp-high`). Match each U.S. one to a row on Google's [control packages page](https://docs.cloud.google.com/assured-workloads/docs/control-packages) and its [pricing tier](https://cloud.google.com/assured-workloads/pricing).

Path 1 learners: do this too — it takes five minutes.

### A7. Price the boundary (your notes)

An agency expects $20,000/month of Google Cloud spend for an IL4 workload. Using Google's published pricing:

1. What does the IL4 package add per month? (Google's own example: $1,500 → +$300.)
2. What if only $5,000/month of that spend truly needs IL4 and the rest can sit in a free-tier folder? How would you structure the folders?
3. What support plan does the package require for screened support, and how does that change the total? (Read the pricing page; don't guess a number.)

---

## Part B — AWS (read-only): partitions and authorizations

AWS CloudShell, as `labadmin` (commercial). Nothing here contacts GovCloud.

```bash
aws sts get-caller-identity --query Arn --output text              # note: arn:aws:...
aws ec2 describe-regions --all-regions --query "Regions[].RegionName" --output text | tr '\t' '\n' | sort | head -40
```

**What you should see:** your ARN starts with `arn:aws:`, and the region list from the commercial partition **does not include** `us-gov-west-1` or `us-gov-east-1`. GovCloud is a different partition (`arn:aws-us-gov:`) with its own IAM — your commercial credentials don't exist there.

Then, in a browser:

1. Read the [GovCloud sign-up page](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/getting-started-sign-up.html). List the eligibility conditions and the steps (don't start them).
2. Open [FedRAMP services in scope](https://aws.amazon.com/compliance/services-in-scope/FedRAMP/). Pick the three AWS services equivalent to your Part A choices and record their GovCloud authorization level and the label AWS uses (High or "Class D").
3. Read the [Secret-West announcement](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-secret-west-region-is-now-available/). What two authorization regimes does it cite?

## Part C — Azure (read-only): sovereign cloud endpoints

Azure Cloud Shell (Bash). These commands read the CLI's built-in cloud definitions — no sign-in to Azure Government.

```bash
az cloud list --query "[].{name:name, active:isActive}" -o table
az cloud show --name AzureUSGovernment \
  --query "{portal:endpoints.portal, arm:endpoints.resourceManager, login:endpoints.activeDirectory}" -o json
az cloud show --name AzureCloud \
  --query "{portal:endpoints.portal, arm:endpoints.resourceManager, login:endpoints.activeDirectory}" -o json
```

**What you should see:** `AzureCloud` active, plus `AzureUSGovernment` and other sovereign clouds; government endpoints ending in `.us` / `usgovcloudapi.net` versus commercial `azure.com` / `microsoftonline.com`. An app moving to Azure Government must change every one of these — and authenticate against a **different Entra tenant**.

Then read Microsoft's [Azure Government for DoD](https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-dod) page and record which regions are DoD-only and the IL each supports.

---

## Part D — Scope matrix (your notes)

Fictional customer: a DoD component needs an **IL5** data-analytics workload (object storage, a managed data warehouse, serverless containers, a key-management service). Build `scope-matrix.md`:

| Need | Google Cloud service + IL5 in scope? | AWS GovCloud service + IL5? | Azure Government service + IL5? | Source + date |
|---|---|---|---|---|

Use only the official scope pages (Google's FedRAMP/DoD scope page, AWS services in scope, Microsoft's Azure Government compliance pages). Where a page doesn't answer, write **"not confirmed"** — don't guess. Finish with three lines: which provider model fits best for this customer and why, the main trade-off, and what the mission owner still has to do for an ATO.

## Verify it worked

| Check | Expected |
|---|---|
| (Path 1) Boundary | `europe-west1` bucket denied; `us-central1` bucket created; constraints listed |
| (Path 2) Packages | Regime list mapped to packages and tiers |
| Pricing | IL4 premium worked out; folder split proposed |
| AWS | Commercial ARN and region list without GovCloud; GovCloud eligibility notes |
| Azure | Commercial vs government endpoints compared |
| Matrix | Four needs × three providers, each cell sourced and dated |

## What to notice (reflection questions)

1. Assured Workloads blocked a non-U.S. bucket **before** it existed. What's the equivalent preventive control in GovCloud and Azure Government — and do you even need it there?
2. What's the operational cost of a second identity plane (GovCloud Organization, Azure Government tenant) versus Google's single organization with a boundary folder?
3. Which matrix cells said "not confirmed"? What would you send the customer instead of guessing?
4. A customer says, "We need physically separate infrastructure." Is that an IL5 requirement as written, or a policy preference? How would you find out?
5. JWCC lists four vendors at every classification level. Why might a component still choose different providers for SECRET and unclassified work?

## Cleanup

**Google Cloud — Path 1 (do this the same day)**

```bash
gcloud storage rm --recursive gs://$P-us
gcloud billing projects unlink $P
gcloud projects delete $P --quiet
```

Then delete the Assured Workloads environment: console → **Assured Workloads** → select `lab27-aw` → **Delete** ⚠️ (Google requires the folder to be empty of active resources first; a just-deleted project in pending deletion may block it — if so, retry after it's purged, or check the *Delete an Assured Workloads folder* doc). CLI alternative:

```bash
gcloud assured workloads list --organization=${ORG#organizations/} --location=us   # ⚠️ location value may differ; use the console if this fails
gcloud assured workloads delete <workload-id> --organization=${ORG#organizations/} --location=us
```

Confirm the folder is gone (`gcloud resource-manager folders list --organization=${ORG#organizations/}`), and remove the role you granted yourself in A1 if you added it:

```bash
gcloud organizations remove-iam-policy-binding $ORG \
  --member=user:$(gcloud config get-value account) --role=roles/assuredworkloads.admin --condition=None
```

**Path 2, AWS, Azure:** nothing was created. Make sure `az cloud list` still shows `AzureCloud` as active.

**Final check — nothing billable remains:** no `lab27-aw` workload or folder; project `$P` in `DELETE_REQUESTED` with billing unlinked; no buckets; no Premium package was ever selected (check the billing report for a "GCP Assured Workloads" line item — there should be none).

## Write-up prompt

> On [date] I compared U.S. government cloud delivery models in a personal lab. [Path 1: I created a free-tier Google Cloud Assured Workloads folder, inspected the organization policies its control package applied, and confirmed it blocked creating a resource outside U.S. regions while allowing one inside, then removed it.] [Path 2: I mapped Google Cloud Assured Workloads compliance regimes to its control packages and pricing tiers.] I compared commercial and government partitions and endpoints for AWS (GovCloud) and Azure (Azure Government) without accessing government systems, priced a premium IL4 boundary, and built a sourced, dated IL5 service-scope matrix across all three providers for a fictional DoD workload.
