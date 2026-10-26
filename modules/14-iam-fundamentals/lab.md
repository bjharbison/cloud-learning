# 14 Lab — Grant, test, and shrink least privilege (no keys allowed)

**Cost:** $0. Google Cloud: one small bucket (inside the always-free 5 GB-month in US regions), one service account, one custom role, IAM bindings, Policy Troubleshooter, and role recommendations for basic roles — all free. AWS (optional): an IAM role, an inline policy, the policy simulator, last accessed data, and an IAM Access Analyzer **external access** analyzer — all free (don't create an **unused access** or **internal access** analyzer; those bill). Azure (optional): a resource group, a user-assigned managed identity, and a role assignment — free. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Create a service account that can **read one bucket** and nothing else — granted at the **lowest scope**.
2. Use it **without a key**, through impersonation, and prove reads work and writes fail.
3. Ask **Policy Troubleshooter** why each request was allowed or denied.
4. Add a **time-limited** grant with an IAM Condition and watch it expire.
5. Build a **custom role**, compare it to a predefined one, and (optional) block key creation with a **deny policy**.
6. (Optional) AWS: simulate identity policy vs **permissions boundary**. Azure: assign a role at **resource-group scope** to a managed identity.

## Prerequisites

- Modules 00–13 done. Your lab project is under "No organization" or your standalone org (module 03) — both work for Part A except the optional deny-policy step.

```bash
PROJECT_ID=$(gcloud config get-value project)
ME=$(gcloud config get-value account)
REGION=us-central1
B=lab14-$PROJECT_ID-$RANDOM
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com storage.googleapis.com \
  policytroubleshooter.googleapis.com recommender.googleapis.com
echo "$B"
```

---

## Part A — Google Cloud

### A1. Look at what you have now (console, then CLI)

Console: **IAM & Admin → IAM**. Find your own account: it has **Owner** — a legacy basic role with thousands of permissions. Click **View by roles** and notice any default service accounts with **Editor** (module 05).

```bash
gcloud projects get-iam-policy $PROJECT_ID --format="table(bindings.role,bindings.members)" | head -30
gcloud iam roles describe roles/editor --format="value(includedPermissions)" | tr ';' '\n' | wc -l
gcloud iam roles describe roles/storage.objectViewer --format="value(includedPermissions)" | tr ';' '\n'
```

**What you should see:** Editor contains thousands of permissions; `roles/storage.objectViewer` contains only a handful, centered on reading and listing objects. That's the gap least privilege closes.

### A2. One bucket, one service account, one grant at the lowest scope (CLI)

```bash
gcloud storage buckets create gs://$B --location=$REGION --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=14
echo "quarterly report — need-to-know" > report.txt && gcloud storage cp report.txt gs://$B/

gcloud iam service-accounts create lab14-analyst --display-name="lab14 analyst (read one bucket)"
SA=lab14-analyst@$PROJECT_ID.iam.gserviceaccount.com
sleep 30   # new service accounts take a moment to propagate

# Grant on the BUCKET, not the project
gcloud storage buckets add-iam-policy-binding gs://$B \
  --member=serviceAccount:$SA --role=roles/storage.objectViewer
```

**Why the bucket and not the project?** A project-level grant would let this SA read *every* bucket in the project, including ones created next year. Bucket-level is reading someone into one compartment, not the whole program.

### A3. Use it without a key — impersonation (CLI)

Let **yourself** mint short-lived tokens for the SA. Even as project Owner, you need this explicit grant:

```bash
gcloud iam service-accounts add-iam-policy-binding $SA \
  --member=user:$ME --role=roles/iam.serviceAccountTokenCreator
sleep 60
```

Now act as the service account:

```bash
gcloud storage cat gs://$B/report.txt --impersonate-service-account=$SA          # expect the text
echo "tampered" > bad.txt
gcloud storage cp bad.txt gs://$B/ --impersonate-service-account=$SA             # expect 403
gcloud storage ls --project=$PROJECT_ID --impersonate-service-account=$SA         # expect 403 (can't list buckets)
```

**What you should see:** the read succeeds; the upload fails with `403 … does not have storage.objects.create access`; listing the project's buckets fails because the grant was on one bucket, not the project. ⚠️ If the first command fails with a token or permission error, wait another minute — IAM changes can take a few minutes to propagate.

**What you did *not* do:** create a JSON key. Nothing sits on disk; each token lasts about an hour; revoking Token Creator ends it.

### A4. Ask "why?" — Policy Troubleshooter (console, then CLI)

Console: **IAM & Admin → Policy Troubleshooter** → principal = the SA's email, resource = `//storage.googleapis.com/projects/_/buckets/BUCKET`, permission = `storage.objects.create` → **Check access**.

CLI:

```bash
for P in storage.objects.get storage.objects.create; do
  echo "== $P"
  gcloud policy-intelligence troubleshoot-policy iam \
    "//storage.googleapis.com/projects/_/buckets/$B" \
    --principal-email=$SA --permission=$P \
    --format="yaml(overallAccessState)"
done
```

**What you should see:** `CAN_ACCESS` for `get`, `CANNOT_ACCESS` for `create`. In the console version, expand the result to see *which* binding on *which* resource (bucket, project) granted or failed to grant — and that deny policies were checked too. This is the tool you use when someone says "I'm getting 403 and I shouldn't be" — or "they can do X and I don't know why." ⚠️ If the CLI returns a permissions error, use the console version.

### A5. Time-boxed access with an IAM Condition (CLI)

Give the SA **write** access for 10 minutes only — a poor-man's just-in-time grant:

```bash
EXP=$(date -u -d '+10 min' +%Y-%m-%dT%H:%M:%SZ); echo "expires $EXP"
gcloud storage buckets add-iam-policy-binding gs://$B \
  --member=serviceAccount:$SA --role=roles/storage.objectCreator \
  --condition="expression=request.time < timestamp('$EXP'),title=lab14-10min-write"
sleep 60
gcloud storage cp bad.txt gs://$B/upload-during-window.txt --impersonate-service-account=$SA   # expect success
```

Wait until after the expiry time, then:

```bash
sleep 600
gcloud storage cp bad.txt gs://$B/upload-after-window.txt --impersonate-service-account=$SA    # expect 403
gcloud storage buckets get-iam-policy gs://$B --format=yaml | grep -A4 condition
```

**What you should see:** success inside the window, `403` after, while the binding is still visible in the policy (expired conditions stay until you remove them). Conditions on bucket policies require uniform bucket-level access — which is why you enabled it in A2. Module 15 shows the purpose-built version: **Privileged Access Manager**.

### A6. A custom role — and why you usually shouldn't (CLI)

```bash
gcloud iam roles create lab14ObjectReader --project=$PROJECT_ID \
  --title="lab14 object reader (get only)" \
  --permissions=storage.objects.get --stage=GA
gcloud iam roles describe lab14ObjectReader --project=$PROJECT_ID --format="yaml(includedPermissions,stage)"
```

**Notice:** narrower than `objectViewer` (no list). Custom roles let you be precise, but **you** now maintain them as services add permissions; predefined roles are maintained by Google. Use custom roles when a predefined role is materially too broad. (Custom roles live at project or org level — not folders.)

### A7. Role recommendations and audit trail (CLI)

```bash
gcloud recommender recommendations list --project=$PROJECT_ID --location=global \
  --recommender=google.iam.policy.Recommender \
  --format="table(description,primaryImpact.category,stateInfo.state)"

gcloud logging read 'protoPayload.methodName="SetIamPolicy" OR protoPayload.methodName:"CreateRole" OR protoPayload.methodName:"CreateServiceAccount"' \
  --limit=10 --freshness=2h \
  --format="table(timestamp,protoPayload.methodName,protoPayload.resourceName,protoPayload.authenticationInfo.principalEmail)"
```

**What you should see:** probably **no recommendations yet** — they use up to 90 days of usage data, and new grants can take up to 15 days to get insights. Come back in a few weeks to your main project: if your default compute SA still holds Editor, you'll likely see a recommendation to replace it. (Free for basic roles; non-basic recommendations need Security Command Center Premium/Enterprise.) The audit log lists every IAM change you made today — `SetIamPolicy` events are among the most important alerts in any cloud (T1098.003).

### A8. (Optional — needs an organization) Block key creation with a deny policy

Skip if your project has **No organization**. Deny policies require `roles/iam.denyAdmin`, which Google's docs grant at the organization.

```bash
ORG_ID=$(gcloud projects get-ancestors $PROJECT_ID --format="value(id,type)" | awk '$2=="organization"{print $1}'); echo "org: $ORG_ID"
gcloud organizations add-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/iam.denyAdmin

cat > deny-keys.json <<'EOF'
{
  "displayName": "lab14: nobody creates service-account keys in this project",
  "rules": [{
    "denyRule": {
      "deniedPrincipals": ["principalSet://goog/public:all"],
      "deniedPermissions": ["iam.googleapis.com/serviceAccountKeys.create"]
    }
  }]
}
EOF
gcloud iam policies create lab14-deny-keys \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/$PROJECT_ID \
  --kind=denypolicies --policy-file=deny-keys.json
sleep 120
gcloud iam service-accounts keys create /dev/null --iam-account=$SA
```

**What you should see:** the key creation fails with a permission-denied error — **even though you're Owner**, because deny is evaluated before allow. If your org was created after May 3, 2024, an **org policy** may have blocked it already (a different error mentioning a constraint) — two layers saying no. ⚠️ If a key *is* created (the deny didn't propagate yet), delete it immediately: `gcloud iam service-accounts keys list --iam-account=$SA --managed-by=user`, then `gcloud iam service-accounts keys delete KEY_ID --iam-account=$SA`.

---

## Part B — AWS (optional, $0): identity policy vs permissions boundary

CloudShell, as `labadmin`.

```bash
ACCT=$(aws sts get-caller-identity --query Account --output text)
cat > trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"AWS":"arn:aws:iam::$ACCT:root"},"Action":"sts:AssumeRole"}]}
EOF
cat > s3-all.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"}]}
EOF
cat > boundary.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Action":["s3:GetObject","s3:ListBucket"],"Resource":"*"}]}
EOF

aws iam create-role --role-name lab14-role --assume-role-policy-document file://trust.json \
  --tags Key=lab,Value=14 --query Role.Arn --output text
aws iam put-role-policy --role-name lab14-role --policy-name lab14-s3-all --policy-document file://s3-all.json
ROLE_ARN=arn:aws:iam::$ACCT:role/lab14-role

echo "--- identity policy only"
aws iam simulate-principal-policy --policy-source-arn $ROLE_ARN \
  --action-names s3:GetObject s3:PutObject s3:DeleteBucket \
  --resource-arns "arn:aws:s3:::example-agency-bucket/*" \
  --query "EvaluationResults[].[EvalActionName,EvalDecision]" --output table

echo "--- with a permissions boundary"
aws iam simulate-principal-policy --policy-source-arn $ROLE_ARN \
  --action-names s3:GetObject s3:PutObject s3:DeleteBucket \
  --resource-arns "arn:aws:s3:::example-agency-bucket/*" \
  --permissions-boundary-policy-input-list file://boundary.json \
  --query "EvaluationResults[].[EvalActionName,EvalDecision]" --output table
```

**What you should see:** with the identity policy alone, all three actions are `allowed`. With the boundary, only `s3:GetObject` stays `allowed`; the others become `implicitDeny` — the boundary **limits** but never **grants**. (The trust policy lets principals in your own account assume the role; you never actually assume it.)

Two more free tools:

```bash
aws accessanalyzer create-analyzer --analyzer-name lab14-external --type ACCOUNT --tags lab=14
sleep 60
aws accessanalyzer list-findings --analyzer-arn $(aws accessanalyzer list-analyzers --query "analyzers[?name=='lab14-external'].arn" --output text) \
  --query "findings[].[resourceType,resource,status]" --output table

JOB=$(aws iam generate-service-last-accessed-details --arn arn:aws:iam::$ACCT:user/labadmin --query JobId --output text)
sleep 10
aws iam get-service-last-accessed-details --job-id $JOB \
  --query "ServicesLastAccessed[?TotalAuthenticatedEntities>\`0\`].[ServiceNamespace,LastAuthenticated]" --output table
```

**What you should see:** the external access analyzer lists any resource shared outside your account (possibly none — that's good); last-accessed data shows which services `labadmin` actually used — the evidence you'd use to shrink `AdministratorAccess` to something smaller.

## Part C — Azure (optional, $0): RBAC at resource-group scope

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab14 --location eastus --tags lab=14
az identity create -g rg-lab14 -n lab14-mi --tags lab=14
MI_OID=$(az identity show -g rg-lab14 -n lab14-mi --query principalId -o tsv)
RG_ID=$(az group show -n rg-lab14 --query id -o tsv)

az role assignment create --assignee-object-id $MI_OID --assignee-principal-type ServicePrincipal \
  --role "Reader" --scope $RG_ID
az role assignment list --scope $RG_ID --query "[].{who:principalName,role:roleDefinitionName,scope:scope}" -o table
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --all \
  --query "[].{role:roleDefinitionName,scope:scope}" -o table
```

**What you should see:** the managed identity holds **Reader** on `rg-lab14` only. Your own account (`labadmin`) holds **Owner** at subscription scope (module 00) — inherited by every resource group. Then open the portal: **Microsoft Entra ID → Roles and administrators** and note that your Entra directory roles are listed in a completely different place from Azure RBAC — the two-systems point from the README.

---

## Verify it worked

| Check | Expected |
|---|---|
| Impersonated read | Object text |
| Impersonated write / bucket list | 403 / 403 |
| Troubleshooter | `get` → CAN_ACCESS; `create` → CANNOT_ACCESS |
| Conditional grant | Upload works in window, 403 after |
| Custom role | One permission, stage GA |
| (A8) Key creation | Denied despite Owner |
| (B) Simulator | All allowed → only GetObject allowed with boundary |
| (C) Azure | MI has Reader at RG scope only |

## What to notice (reflection questions)

1. You're Owner, yet you had to grant yourself Token Creator to impersonate the SA. Why is that a good design?
2. What's the risk of granting `roles/iam.serviceAccountTokenCreator` or `roles/iam.serviceAccountUser` on a powerful service account to a developer group?
3. In A5, the expired binding stayed in the policy. What hygiene problem does that create over time, and what tool solves it properly?
4. Compare Google's deny policy, AWS's explicit Deny and permissions boundary, and Azure's deny assignments. Which can *you* write on each cloud?
5. Write one detection each for T1098.001 and T1098.003 using the audit events you saw.

## Cleanup

**Google Cloud**

```bash
gcloud storage rm --recursive gs://$B
gcloud iam service-accounts delete $SA --quiet
gcloud iam roles delete lab14ObjectReader --project=$PROJECT_ID --quiet
rm -f report.txt bad.txt deny-keys.json
```

If you did **A8**:

```bash
gcloud iam policies delete lab14-deny-keys \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/$PROJECT_ID --kind=denypolicies
gcloud organizations remove-iam-policy-binding $ORG_ID --member=user:$ME --role=roles/iam.denyAdmin
```

Deleting the service account also removes its own IAM policy (your Token Creator grant). Confirm:

```bash
gcloud storage ls | grep lab14 || echo "no lab14 buckets"
gcloud iam service-accounts list --filter="email:lab14-analyst"          # Listed 0 items
gcloud iam roles list --project=$PROJECT_ID --filter="name:lab14" --show-deleted --format="table(name,deleted)"   # deleted: True
gcloud projects get-iam-policy $PROJECT_ID --format=json | grep lab14 || echo "no lab14 bindings on the project"
```

A deleted custom role stays in a **deleted** state for a period and its ID can't be reused immediately ⚠️ (exact retention not re-verified this run) — it grants nothing and costs nothing.

**AWS**

```bash
aws iam delete-role-policy --role-name lab14-role --policy-name lab14-s3-all
aws iam delete-role --role-name lab14-role
aws accessanalyzer delete-analyzer --analyzer-name lab14-external
rm -f trust.json s3-all.json boundary.json
aws iam get-role --role-name lab14-role 2>&1 | grep -q NoSuchEntity && echo "role gone"
aws accessanalyzer list-analyzers --query "analyzers[?name=='lab14-external']" --output text   # expect empty
```

**Azure**

```bash
az role assignment delete --assignee $MI_OID --role "Reader" --scope $RG_ID
az group delete --name rg-lab14 --yes
az group list --query "[?name=='rg-lab14']" -o table   # expect empty
```

**Final check — nothing billable remains:** no `lab14` bucket, service account, or project bindings on Google (and no deny policy or org-level Deny Admin grant if you did A8); no `lab14-role` or analyzer on AWS; no `rg-lab14` on Azure. Nothing in this lab bills, but leftover grants are a security liability — which is the point of the module.

## Write-up prompt

> On [date] I implemented least privilege for a Google Cloud service account: I granted a predefined object-viewer role on a single bucket rather than the project, used the account without any key through service-account impersonation, and verified that reads succeeded while writes and bucket listing were denied. I used Policy Troubleshooter to explain the allow and deny results, added a time-limited write grant with an IAM Condition and confirmed it stopped working at expiry, created a single-permission custom role, and reviewed IAM changes in Admin Activity audit logs. [Optional: I created an IAM deny policy that blocked service-account key creation even for a project Owner.] [Optional: I used the AWS IAM policy simulator to show a permissions boundary restricting an over-broad identity policy, ran an IAM Access Analyzer external-access analyzer, and reviewed last-accessed data; and assigned an Azure RBAC role to a managed identity at resource-group scope.] I deleted all resources afterward.
