# 03 Lab — Build a small hierarchy and watch a guardrail block you

**Cost:** $0. Folders, projects with no resources, AWS OUs and SCPs, Azure management groups, resource groups, and policy assignments create nothing that runs. The "test" actions are attempts to create a bucket or resource group in a forbidden location — they're **denied**, so nothing gets created. AWS Organizations has no additional charge — **but enabling it automatically moves an AWS free-plan account to the paid plan** (see Part B). · **Time:** 90 min · **Clouds:** GCP (required), AWS, Azure

## Goal

1. Find out what hierarchy your personal Google Cloud setup actually has — and work honestly within it.
2. Build a two-environment tree (prod/dev) on each cloud.
3. Attach a **location guardrail** high in the tree and watch it block a create lower down.
4. See inherited access from the API.

## Prerequisites

- Modules 00–02 done; budget alerts active.
- AWS: read the warning at the top of Part B before doing anything there. Sign in as `labadmin`.
- Azure: if you're past day 30 of the free account, Azure has disabled services until you upgrade to pay-as-you-go (module 00, trial cliff). Management groups, policy assignments, and empty resource groups cost nothing, but you need an active subscription. Sign in as `labadmin`, or as your sign-up identity if you hit a management-group permission error (see C1).

---

## Part A — Google Cloud

### A0. Which situation are you in?

```bash
gcloud organizations list
gcloud projects list
gcloud projects get-ancestors $(gcloud config get-value project)
```

Console: **IAM & Admin → Manage resources**.

| What you see | Do this |
|---|---|
| An organization (e.g., `yourname-org` or your domain) | **Path 1** below |
| `Listed 0 items` for organizations; projects show only themselves as ancestors / "No organization" | **Path 2** below |

> **Getting an organization if you don't have one:** Cloud Identity Free requires a domain you own and can verify in DNS. If you already own one, the setup is free and gives you a real org; buying a domain just for this costs money, so it's optional. Standalone organizations are created at sign-up for new Free Trial customers, not for existing accounts. Don't create a second Google Account just to farm a new trial — that conflicts with the trial's eligibility terms.

---

### Path 1 — You have an organization

**A1. Give yourself only the roles you need.** Org Admin can manage IAM but can't create folders or projects by default.

```bash
ORG_ID=$(gcloud organizations list --format="value(name)" --limit=1)
ME=$(gcloud config get-value account)
gcloud organizations add-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/resourcemanager.folderCreator
gcloud organizations add-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/resourcemanager.projectCreator
gcloud organizations add-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/orgpolicy.policyAdmin
```

**A2. Build the tree (console, then CLI).**

Use **either** the console **or** the CLI, not both — folder names must be unique under a parent, and duplicate projects complicate cleanup.

Console: **Manage resources → Create folder** → `lab03-prod`, then `lab03-dev`. Then **Create project** → `lab03-dev-<initials>` with location = the `lab03-dev` folder, and add the label `lab=03` (**IAM & Admin → Labels**). Note the folder and project IDs for the steps below.

CLI:

```bash
gcloud resource-manager folders create --display-name=lab03-prod --organization=$ORG_ID
gcloud resource-manager folders create --display-name=lab03-dev  --organization=$ORG_ID
gcloud resource-manager folders list --organization=$ORG_ID
DEV_FOLDER=<numeric ID of lab03-dev from the list>

DEV_PROJECT=lab03-dev-$RANDOM
gcloud projects create $DEV_PROJECT --folder=$DEV_FOLDER --labels=lab=03
gcloud projects get-ancestors $DEV_PROJECT
```

`get-ancestors` should list: project → folder → organization.

**A3. Attach a location guardrail to the dev folder.** This uses the `gcp.resourceLocations` constraint with the `in:us-locations` value group.

```bash
cat > /tmp/loc-policy.yaml <<EOF
name: folders/$DEV_FOLDER/policies/gcp.resourceLocations
spec:
  rules:
  - values:
      allowedValues:
      - in:us-locations
EOF
gcloud org-policies set-policy /tmp/loc-policy.yaml
gcloud org-policies describe gcp.resourceLocations --project=$DEV_PROJECT --effective
```

The project shows the policy as **effective** even though you set it on the folder. That's inheritance. (Enforcement can take up to 15 minutes.)

**A4. Watch it block you.** Cloud Storage needs a billing-linked project:

```bash
gcloud billing projects link $DEV_PROJECT --billing-account=<ACCOUNT_ID>
gcloud storage buckets create gs://$DEV_PROJECT-eu --location=europe-west1 --project=$DEV_PROJECT
```

Expect a **constraint violation** error — and you're the org admin. Guardrails beat roles. Now confirm a US location works, then delete it right away:

```bash
gcloud storage buckets create gs://$DEV_PROJECT-us --location=us-central1 --project=$DEV_PROJECT
gcloud storage buckets delete gs://$DEV_PROJECT-us
```

**A5. See inherited access.**

```bash
gcloud projects get-ancestors-iam-policy $DEV_PROJECT --format=json | head -60
```

Your org-level role bindings appear as inherited at the project. You never granted anything on the project itself.

---

### Path 2 — No organization ("No organization")

You can't create folders or set org policies, so you'll learn what you *can't* do and why.

**A1. Confirm the limits.**

```bash
P=$(gcloud config get-value project)
gcloud projects get-ancestors $P                       # only the project itself
gcloud organizations list                              # Listed 0 items
```

In the console, **Manage resources** shows no **Create folder** option without an organization — folders need an org (or another folder) as their parent.

**A2. Simulate environments with projects (console, then CLI).**

Use **either** the console **or** the CLI, not both.

Console: project picker → **New project** → `lab03-prod-<initials>`, then `lab03-dev-<initials>`; Location: **No organization**. Add labels `lab=03` and `env=prod`/`env=dev` under **IAM & Admin → Labels**.

```bash
gcloud projects create lab03-prod-$RANDOM --labels=lab=03,env=prod
gcloud projects create lab03-dev-$RANDOM  --labels=lab=03,env=dev
gcloud projects list --filter="labels.lab=03"
```

**A3. Read (not set) the effective guardrails.**

```bash
gcloud org-policies list --project=<lab03-dev project> --show-unset | head -30
gcloud org-policies describe gcp.resourceLocations --project=<lab03-dev project> --effective
```

You can read constraints, but setting them needs the Organization Policy Administrator role, which Google grants on an organization. **Reflection:** without an org, every project is an island — no inherited guardrails, no central place to grant access. That's exactly why enterprises never run without one.

**A4. See access is per-project.**

```bash
gcloud projects get-ancestors-iam-policy <lab03-dev project> --format=json | head -40
```

Only the project's own bindings appear; there's no ancestor to inherit from.

---

## Part B — AWS

> ⚠️ **Free-plan warning.** AWS's billing docs say a free-plan account that joins AWS Organizations is **automatically upgraded to the paid plan** (remaining credits still apply to future bills, but you stop earning new ones). Creating an organization almost certainly counts — ⚠️ AWS doesn't say so explicitly.
>
> - **Still on the free plan and want to stay there?** Do Part B as a **read-along**: study the commands and the SCP, but don't run them. You'll lose nothing conceptually — SCPs can't be tested from the management account anyway (B4).
> - **Already upgraded, or ready to upgrade deliberately?** Run it. This is also the moment to move your admin from the module 00 IAM user to **IAM Identity Center** (organization instance, AdministratorAccess permission set), then delete the IAM user.

All commands run in CloudShell as your admin in the **management account**. Creating the organization (console: **AWS Organizations → Create an organization**, or `aws organizations create-organization --feature-set ALL`) makes your account the management account.

**B1. Inspect the organization.**

```bash
aws organizations describe-organization
ROOT_ID=$(aws organizations list-roots --query "Roots[0].Id" --output text)
echo $ROOT_ID
```

Console: **AWS Organizations → AWS accounts** shows Root and your management account.

**B2. Create OUs (console, then CLI).**

Console: **AWS accounts → Root → Actions → Create new** → `Lab03-Prod`, then `Lab03-Dev`.

```bash
aws organizations create-organizational-unit --parent-id $ROOT_ID --name Lab03-Prod
aws organizations create-organizational-unit --parent-id $ROOT_ID --name Lab03-Dev
aws organizations list-organizational-units-for-parent --parent-id $ROOT_ID
DEV_OU=<ou-… ID of Lab03-Dev>
```

**B3. Write a region guardrail (SCP).**

```bash
aws organizations enable-policy-type --root-id $ROOT_ID --policy-type SERVICE_CONTROL_POLICY
# If this returns PolicyTypeAlreadyEnabledException, SCPs are already on — continue.

cat > /tmp/deny-regions.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyOutsideApprovedRegions",
    "Effect": "Deny",
    "NotAction": ["iam:*", "organizations:*", "sts:*", "support:*", "budgets:*", "route53:*", "cloudfront:*"],
    "Resource": "*",
    "Condition": {"StringNotEquals": {"aws:RequestedRegion": ["us-east-1", "us-west-2"]}}
  }]
}
EOF

POLICY_ID=$(aws organizations create-policy --name Lab03-DenyRegions \
  --description "Lab 03: allow only us-east-1 and us-west-2" \
  --type SERVICE_CONTROL_POLICY --content file:///tmp/deny-regions.json \
  --query "Policy.PolicySummary.Id" --output text)
aws organizations attach-policy --policy-id $POLICY_ID --target-id $DEV_OU
aws organizations list-policies-for-target --target-id $DEV_OU --filter SERVICE_CONTROL_POLICY
```

`NotAction` exempts global services that don't run in a specific region. Notice `FullAWSAccess` is also attached — SCPs only cap; that default policy is what leaves room for IAM to grant.

**B4. Why you won't see it block anything.** The Dev OU has **no accounts**, and SCPs **never apply to the management account** — where you're working. To test it for real you'd create a member account in the OU. That needs a unique email and a later account closure, so it's **optional** and not part of this lab. The lesson stands: if you ran workloads in the management account, this guardrail would never protect them.

---

## Part C — Azure

**C1. Create management groups (console, then CLI).**

Console: search **Management groups** → **Create** → ID `lab03-root`, display name `Lab03`. Then create `lab03-prod` and `lab03-dev` with parent `lab03-root`. The first management group in a directory can take up to 15 minutes to appear.

If you get an authorization error: sign in as your sign-up identity (Global Administrator) → **Microsoft Entra ID → Properties → Access management for Azure resources → Yes** to elevate, create the groups, then set it back to **No**.

```bash
az account management-group create --name lab03-root --display-name "Lab03"
az account management-group create --name lab03-prod --parent lab03-root
az account management-group create --name lab03-dev  --parent lab03-root
az account management-group list -o table
```

**C2. Put your subscription under Dev.**

Console: **Management groups → lab03-dev → Add subscription** → your subscription.

CLI (confirm syntax with `az account management-group subscription add --help`):

```bash
SUB_ID=$(az account show --query id -o tsv)
az account management-group subscription add --name lab03-dev --subscription $SUB_ID
```

**C3. Assign a location guardrail at the management group (console).**

**Policy → Assignments → Assign policy** → Scope: `lab03-dev` → Policy definition: search **"Allowed locations for resource groups"** → Allowed locations: **East US** → Review + create. (Policy assignments can take several minutes to take effect.)

**C4. Watch it block you.**

```bash
az group create --name lab03-west --location westus    # expect: RequestDisallowedByPolicy
az group create --name lab03-east --location eastus    # allowed
az group delete --name lab03-east --yes
```

The policy was set on the management group; it blocked you in the subscription below it. Inheritance again.

---

## Verify it worked

| Check | Google Cloud | AWS | Azure |
|---|---|---|---|
| Tree exists | Path 1: project → folder → org in `get-ancestors`. Path 2: two labeled projects | Two OUs under Root | `lab03-root` → `lab03-prod`, `lab03-dev`; subscription under dev |
| Guardrail visible lower down | `describe --effective` on the project | `list-policies-for-target` on Dev OU | Policy shows on the subscription's **Policy** blade as inherited |
| Guardrail blocks | `europe-west1` bucket denied (Path 1) | (Explained, not tested) | `westus` resource group denied |

## What to notice (reflection questions)

1. Which control blocked you: IAM or a guardrail? Why didn't your admin role help?
2. Why do SCPs skip the AWS management account, and what does that imply for where you run workloads?
3. On Google Cloud Path 2, what would break first if a team of 20 tried to work this way?
4. Map this to classification compartments: where would you grant a program manager read access — org, folder, or project?
5. Write a detection rule for ATT&CK T1666 on each cloud in one line each.

## Cleanup

**Google Cloud — Path 1**

```bash
gcloud org-policies delete gcp.resourceLocations --folder=$DEV_FOLDER
gcloud projects list --filter="labels.lab=03 OR projectId:lab03-*" --format="value(projectId)"   # catch any extras
gcloud projects delete $DEV_PROJECT --quiet
gcloud resource-manager folders delete $DEV_FOLDER
gcloud resource-manager folders delete <lab03-prod folder ID>
gcloud organizations remove-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/orgpolicy.policyAdmin
gcloud organizations remove-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/resourcemanager.folderCreator
```

Deleted projects enter a pending-deletion period before they're purged. If the folder delete fails because the project is still pending deletion, leave the empty folder and delete it later — an empty folder runs nothing. Keep `projectCreator` if you'll create projects in later labs.

**Google Cloud — Path 2**

```bash
gcloud projects list --filter="labels.lab=03 OR projectId:lab03-*" --format="value(projectId)"
gcloud projects delete <lab03-prod project> --quiet
gcloud projects delete <lab03-dev project> --quiet
```

**AWS**

```bash
aws organizations detach-policy --policy-id $POLICY_ID --target-id $DEV_OU
aws organizations delete-policy --policy-id $POLICY_ID
aws organizations delete-organizational-unit --organizational-unit-id $DEV_OU
aws organizations delete-organizational-unit --organizational-unit-id <Lab03-Prod ou-… ID>
```

Leave AWS Organizations (and IAM Identity Center, if you moved to it) enabled; later modules build on them. If you did Part B as a read-along, there's nothing to clean up. (You can leave SCPs enabled at the root; `FullAWSAccess` keeps everything allowed.)

**Azure**

1. Console: **Policy → Assignments** → delete the `lab03-dev` assignment.
2. Move the subscription back to the tenant root group:

```bash
TENANT_ID=$(az account show --query tenantId -o tsv)
az account management-group subscription add --name $TENANT_ID --subscription $SUB_ID
az account management-group delete --name lab03-dev
az account management-group delete --name lab03-prod
az account management-group delete --name lab03-root
az group list -o table        # confirm no lab03-* resource groups remain
```

If you elevated access in C1, confirm **Access management for Azure resources** is back to **No**.

**Final check — nothing billable remains:** `gcloud projects list --filter="labels.lab=03 OR projectId:lab03-*"` shows only projects in deletion; `gcloud storage ls` shows no `lab03` buckets; AWS Bills page $0.00; Azure Cost analysis $0.00.

## Write-up prompt

> On [date] I built resource hierarchies on three clouds. On Google Cloud I [created folders and a project under my organization and enforced a `gcp.resourceLocations` org policy at the folder level that blocked a non-US bucket even for an org admin / documented the limits of a no-organization personal account and simulated environments with labeled projects]. On AWS I created OUs and a region-restricting SCP, and documented why SCPs don't apply to the management account. On Azure I created a management-group tree, moved my subscription under it, and used an Azure Policy assignment to block a resource group outside the allowed region. I cleaned up all lab resources.
