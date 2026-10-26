# 15 Lab — Keyless CI/CD: GitHub Actions → Google Cloud with Workload Identity Federation (and see why the condition matters)

**Cost:** $0. Workload Identity Federation has no added per-identity cost; the lab bucket fits in the always-free 5 GB-month (US regions); a few GitHub Actions runs use a minute or two of your GitHub plan's included minutes ⚠️ (check your plan's allowance; public repos weren't used here, on purpose). AWS (optional): an IAM OIDC identity provider and a role — free. Azure (optional): an app registration with a federated credential, and reviewing Entra settings — free. **No Entra P1/P2 trial is required**; a P2 trial for exploring PIM is optional and subject to availability. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Create a **workload identity pool** and a GitHub **OIDC provider** with an **attribute condition** locking it to *your* repository and *main* branch.
2. Grant a federated **principalSet** read access to one bucket — **no service account, no key**.
3. From a GitHub Actions workflow, exchange GitHub's OIDC token for a Google access token **by hand** with `curl`, so you see every step, and read the object.
4. Run the same workflow from another branch and watch it be **refused**.
5. (Optional) Do the AWS equivalent with an IAM OIDC provider and a role trust policy; inspect an Entra federated credential and your tenant's consent settings.

## Prerequisites

- Modules 00–14 done. Your GitHub account with MFA enabled (a passkey or security key, ideally).
- A **new private repository** on GitHub just for this lab, e.g. `wif-lab` (Settings → Create repository → Private, add a README). **Don't use the `cloud-learning` repo.**
- In Cloud Shell:

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
GH_OWNER=your-github-username        # <-- edit
GH_REPO=wif-lab                      # <-- edit if you named it differently
GH_OWNER_ID=$(curl -s https://api.github.com/users/$GH_OWNER | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "owner id: $GH_OWNER_ID"
REGION=us-central1
B=lab15-$PROJECT_ID-$RANDOM
gcloud services enable iam.googleapis.com sts.googleapis.com iamcredentials.googleapis.com storage.googleapis.com
echo "$B"
```

The numeric owner ID matters: names can be changed and later re-registered by someone else; IDs can't. Google recommends conditioning on IDs. Type `GH_OWNER` with the **exact letter case** GitHub shows for your username — the repository comparison in the condition is case-sensitive.

---

## Part A — Google Cloud

### A1. A bucket with something to read

```bash
gcloud storage buckets create gs://$B --location=$REGION --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=15
echo "deployed by a pipeline with no stored secrets" > hello.txt && gcloud storage cp hello.txt gs://$B/
```

### A2. Workload identity pool and GitHub provider (console, then CLI)

Console tour: **IAM & Admin → Workload Identity Federation → Create pool**. Note the fields — pool, then provider type **OpenID Connect (OIDC)**, issuer URL, **attribute mapping**, **attribute conditions** — then cancel and use the CLI.

```bash
gcloud iam workload-identity-pools create lab15-pool --location=global \
  --display-name="lab15 GitHub pool"

gcloud iam workload-identity-pools providers create-oidc lab15-github \
  --location=global --workload-identity-pool=lab15-pool \
  --display-name="lab15 GitHub provider" \
  --issuer-uri="https://token.actions.githubusercontent.com/" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner_id=assertion.repository_owner_id,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner_id == '$GH_OWNER_ID' && assertion.repository == '$GH_OWNER/$GH_REPO' && assertion.ref == 'refs/heads/main'"

gcloud iam workload-identity-pools providers describe lab15-github \
  --location=global --workload-identity-pool=lab15-pool --format="yaml(attributeCondition,attributeMapping,oidc)"
```

**Read the condition out loud:** "Accept a GitHub token only if it was issued to a workflow in a repository owned by *my* account ID, in *this* repository, running on *main*." Without it, every GitHub repository on earth can mint a token from the same issuer — Google says you **must** set one.

### A3. Grant the federated identity access to one bucket — directly

```bash
MEMBER="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/lab15-pool/attribute.repository/$GH_OWNER/$GH_REPO"
gcloud storage buckets add-iam-policy-binding gs://$B --member="$MEMBER" --role=roles/storage.objectViewer

AUD="https://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/lab15-pool/providers/lab15-github"
echo; echo "Paste these into the workflow:"; echo "  PROVIDER_AUD: $AUD"; echo "  BUCKET: $B"
```

(Google prefers the numeric `repository_id`; this lab binds on the name because a private repo's ID isn't available without authenticating to GitHub — the owner-ID check in the provider condition covers the re-registration risk. You'll see `repository_id` in step 1's output and could switch to it.)

No service account was created. The grant goes to "any workload from this repository that passed the provider's condition" — Google's recommended **direct resource access** pattern. (Some products still need **service-account impersonation**; then you'd grant the principalSet `roles/iam.workloadIdentityUser` on an SA.)

### A4. The workflow (GitHub web UI)

In your `wif-lab` repo: **Add file → Create new file** → `.github/workflows/wif.yml` → paste, replacing the two values → **Commit to main**.

```yaml
name: wif-lab
on: workflow_dispatch
permissions:
  contents: read
  id-token: write          # lets the job request a GitHub OIDC token
env:
  PROVIDER_AUD: "https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/lab15-pool/providers/lab15-github"
  BUCKET: "lab15-REPLACE-ME"
jobs:
  read:
    runs-on: ubuntu-latest
    steps:
      - name: 1. Get a GitHub OIDC token for Google's audience
        run: |
          GH_TOKEN=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
            "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=$PROVIDER_AUD" | jq -r .value)
          echo "::add-mask::$GH_TOKEN"
          echo "GH_TOKEN=$GH_TOKEN" >> "$GITHUB_ENV"
          echo "Claims in the token (signature not shown):"
          python3 -c 'import sys,base64,json; p=sys.argv[1].split(".")[1]; p+="="*(-len(p)%4); c=json.loads(base64.urlsafe_b64decode(p)); print(json.dumps({k:c.get(k) for k in ["iss","aud","sub","repository","repository_id","repository_owner_id","ref","exp"]},indent=1))' "$GH_TOKEN"
      - name: 2. Exchange it at Google STS for a federated access token
        run: |
          AUDIENCE="${PROVIDER_AUD#https:}"
          RESP=$(jq -n --arg aud "$AUDIENCE" --arg tok "$GH_TOKEN" '{
            audience: $aud,
            grantType: "urn:ietf:params:oauth:grant-type:token-exchange",
            requestedTokenType: "urn:ietf:params:oauth:token-type:access_token",
            scope: "https://www.googleapis.com/auth/cloud-platform",
            subjectTokenType: "urn:ietf:params:oauth:token-type:jwt",
            subjectToken: $tok }' | curl -sS -X POST https://sts.googleapis.com/v1/token \
            -H "Content-Type: application/json" -d @-)
          G_TOKEN=$(echo "$RESP" | jq -r '.access_token // empty')
          if [ -z "$G_TOKEN" ]; then echo "STS refused:"; echo "$RESP" | jq .; exit 1; fi
          echo "::add-mask::$G_TOKEN"
          echo "G_TOKEN=$G_TOKEN" >> "$GITHUB_ENV"
          echo "Got a short-lived Google token (expires_in: $(echo "$RESP" | jq .expires_in)s)"
      - name: 3. Read the object with it
        run: |
          curl -sS -f -H "Authorization: Bearer $G_TOKEN" \
            "https://storage.googleapis.com/storage/v1/b/$BUCKET/o/hello.txt?alt=media"
```

Every line is plain `curl` and `jq` (both on GitHub's Ubuntu runners), so you can see the federation flow from the README's diagram step by step. `::add-mask::` keeps the tokens out of the job log.

> **In real pipelines** you'd use Google's maintained action instead of hand-rolled `curl`: `google-github-actions/auth@v3` with `workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/lab15-pool/providers/lab15-github`. Pin actions to a version (or commit SHA) you've reviewed.

### A5. Run it from main — then from another branch

1. **Actions → wif-lab → Run workflow → Branch: main → Run.** Open the run.
   **What you should see:** step 1 prints claims including `"iss": "https://token.actions.githubusercontent.com"`, your `repository`, `repository_id`, `repository_owner_id`, `"ref": "refs/heads/main"`, and a `sub`; step 2 gets a token; step 3 prints `deployed by a pipeline with no stored secrets`.
   **Copy the `sub` value** into a note — Parts B and C need it. For repositories created since July 15, 2026, GitHub issues **immutable** subjects that embed numeric IDs, like `repo:owner@123456/wif-lab@789012:ref:refs/heads/main`, rather than the older `repo:owner/wif-lab:ref:refs/heads/main`.
2. Create a branch: **Code → main ▾ → type `dev` → Create branch.** Then **Run workflow → Branch: dev → Run.**
   **What you should see:** step 1 shows `"ref": "refs/heads/dev"`; step 2 fails with an STS error (an `unauthorized_client`/`invalid_grant`-style message saying the credential is rejected by the attribute condition ⚠️ exact wording may differ). The token was genuine — GitHub signed it — but **your condition** refused it.

That second run is the module's whole point: a valid token from a trusted issuer is not the same as an authorized caller.

### A6. See it in the logs (CLI)

```bash
gcloud logging read 'protoPayload.serviceName="sts.googleapis.com"' --limit=5 --freshness=1h \
  --format="table(timestamp,protoPayload.methodName,protoPayload.status.code,protoPayload.authenticationInfo.principalSubject)" \
  || echo "no STS entries — see note"
```

⚠️ STS token exchanges are logged as **Data Access** audit logs, which are off by default for most services; if you see nothing, that's expected. To record them, enable Data Access logs for **Security Token Service API** (**IAM & Admin → Audit Logs**) — note that Data Access logs can add Cloud Logging volume. Module 18 covers audit-log configuration.

---

## Part B — AWS (optional, $0): the same idea with an IAM OIDC provider

CloudShell, as `labadmin`.

```bash
GH_SUB='repo:...:ref:refs/heads/main'   # <-- paste the exact sub printed by step 1 of your main-branch run
ACCT=$(aws sts get-caller-identity --query Account --output text)
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com --tags Key=lab,Value=15

cat > gh-trust.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"Federated":"arn:aws:iam::$ACCT:oidc-provider/token.actions.githubusercontent.com"},
 "Action":"sts:AssumeRoleWithWebIdentity",
 "Condition":{"StringEquals":{
   "token.actions.githubusercontent.com:aud":"sts.amazonaws.com",
   "token.actions.githubusercontent.com:sub":"$GH_SUB"}}}]}
EOF
aws iam create-role --role-name lab15-gh-role --assume-role-policy-document file://gh-trust.json \
  --max-session-duration 3600 --tags Key=lab,Value=15 --query Role.Arn --output text
aws iam put-role-policy --role-name lab15-gh-role --policy-name lab15-whoami \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"iam:GetRole","Resource":"*"}]}'
```

No thumbprint was supplied: AWS validates providers with publicly trusted certificates against its trusted CAs. Then add a second job to `wif.yml` (replace the account ID):

```yaml
  aws:
    runs-on: ubuntu-latest
    steps:
      - name: Assume an AWS role with the GitHub token
        run: |
          T=$(curl -sS -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
            "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.amazonaws.com" | jq -r .value)
          echo "::add-mask::$T"
          aws sts assume-role-with-web-identity --role-arn arn:aws:iam::ACCOUNT_ID:role/lab15-gh-role \
            --role-session-name gh-lab15 --web-identity-token "$T" --region us-east-1 \
            --query "AssumedRoleUser.Arn" --output text
```

**What you should see:** on `main`, an assumed-role ARN ending in `lab15-gh-role/gh-lab15`; on `dev`, `AccessDenied`. **Spot the classic mistake:** changing the `sub` condition to `StringLike` with `repo:*` would let any GitHub repository assume your role. Using the exact `sub` from the token — not one typed from memory — is why this works for both GitHub's older and newer (immutable, ID-based) subject formats; a mismatch fails on `main` too.

## Part C — Azure / Entra (optional, $0): federated credential and consent settings

Azure Cloud Shell (Bash). **Which account:** `labadmin` (module 00) has Owner on the subscription but no Entra directory role. Creating an app registration works if your tenant still allows "Users can register applications" (the default); if it's refused, use your tenant's original sign-up (break-glass) identity for Part C only, and sign out afterward. Viewing consent settings and starting a trial may also need that admin identity ⚠️ (role requirements not re-verified).

```bash
GH_SUB='repo:...:ref:refs/heads/main'   # <-- paste the exact sub from step 1
APP_ID=$(az ad app create --display-name lab15-gh-app --query appId -o tsv)
cat > fic.json <<EOF
{"name":"lab15-main","issuer":"https://token.actions.githubusercontent.com",
 "subject":"$GH_SUB","audiences":["api://AzureADTokenExchange"]}
EOF
az ad app federated-credential create --id $APP_ID --parameters fic.json
az ad app federated-credential list --id $APP_ID --query "[].{name:name,subject:subject,aud:audiences[0]}" -o table
```

**What you should see:** an app registration with **no client secret** and one federated credential bound to exactly one repo and branch (standard credentials allow no wildcards; flexible, expression-based credentials are in Preview). You haven't granted it any Azure role, so it can't do anything yet — deliberately.

Then, in the **Entra admin center** (portal, read-only):

1. **Enterprise apps → Consent and permissions → User consent settings.** Which option is selected? Microsoft recommends **verified publishers, low-impact permissions** (or the Microsoft-managed default) plus the **admin consent workflow**.
2. **Monitoring & health → Sign-in logs.** Open one of your own sign-ins and find the **authentication method** and **Conditional Access** tab (likely "not applied" on a free tenant with security defaults).
3. (Optional) If you activate an Entra ID P2 trial, look at **Identity Governance → Privileged Identity Management → Microsoft Entra roles** and make yourself **eligible** (not active) for a low-risk role. ⚠️ Trial availability varies; cancel it afterward.

---

## Verify it worked

| Check | Expected |
|---|---|
| Provider condition | Owner ID + repo + `refs/heads/main` |
| IAM binding | `principalSet://…/attribute.repository/OWNER/wif-lab` → objectViewer on one bucket |
| Run on `main` | Claims printed, STS token issued, object text printed |
| Run on `dev` | STS rejects the token (condition) |
| Service accounts / keys created | None |
| (B) AWS | Role assumed on `main`; `AccessDenied` on `dev` |
| (C) Entra | Federated credential with exact subject; consent setting reviewed |

## What to notice (reflection questions)

1. The `dev` run carried a genuine, GitHub-signed token. Which *one* line of configuration stopped it — and what would have happened without it?
2. Why condition on `repository_owner_id` rather than only the owner's name?
3. Compare where the trust decision lives: Google provider attribute condition, AWS role trust policy, Entra federated credential subject. Which is easiest to get dangerously wrong?
4. If an attacker compromised a maintainer's GitHub account and pushed to `main`, what would this design *not* stop? What GitHub-side controls (branch protection, environments with reviewers) would you add? (Google's H1 2026 Threat Horizons UNC6426 case — a stolen GitHub token abusing a GitHub-to-AWS OIDC trust — is the real-world version.)
5. Map consent phishing (T1528) to the Entra setting you reviewed in Part C.

## Cleanup

**Google Cloud**

```bash
gcloud storage rm --recursive gs://$B
gcloud iam workload-identity-pools providers delete lab15-github --location=global --workload-identity-pool=lab15-pool --quiet
gcloud iam workload-identity-pools delete lab15-pool --location=global --quiet
rm -f hello.txt
gcloud storage ls | grep lab15 || echo "no lab15 buckets"
gcloud iam workload-identity-pools list --location=global --format="table(name,state)"   # lab15-pool: DELETED (soft-deleted)
```

Deleted pools and providers are **soft-deleted** — they stay in a `DELETED` state for about 30 days (and can be undeleted) before being purged ⚠️ (retention period not re-verified this run); a deleted provider accepts no tokens.

**GitHub:** delete the `wif-lab` repository (**Settings → Danger zone → Delete this repository**), or at least delete `.github/workflows/wif.yml`.

**AWS**

```bash
aws iam delete-role-policy --role-name lab15-gh-role --policy-name lab15-whoami
aws iam delete-role --role-name lab15-gh-role
aws iam delete-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::$ACCT:oidc-provider/token.actions.githubusercontent.com
rm -f gh-trust.json
aws iam list-open-id-connect-providers --output text | grep token.actions || echo "provider gone"
```

(If you already had a GitHub OIDC provider for other work before this lab, the `create` step would have failed with "already exists" — in that case, don't delete it.)

**Azure / Entra**

```bash
az ad app delete --id $APP_ID
az ad app list --display-name lab15-gh-app --query "[].appId" -o tsv   # expect empty
rm -f fic.json
```

If you started an Entra P2 trial, remove any PIM eligibility you created and cancel the trial in **Billing → Your products** ⚠️ (menu path may differ).

**Final check — nothing billable or trusted remains:** no `lab15` bucket or active workload identity pool on Google; no `lab15-gh-role` or leftover GitHub OIDC provider on AWS; no `lab15-gh-app` in Entra; the GitHub sandbox repo deleted. Leftover **trust relationships** are the real risk here, not cost — a forgotten federated trust is a door.

## Write-up prompt

> On [date] I configured keyless authentication from GitHub Actions to Google Cloud using Workload Identity Federation: a workload identity pool and OIDC provider with an attribute condition restricting tokens to my repository (by numeric owner ID and name) and the main branch, and a direct IAM grant of read access on a single bucket to that repository's federated principal set — no service account or key. I performed the OIDC-to-STS token exchange step by step in a workflow, read the object successfully from main, and confirmed that a run from another branch was rejected by the attribute condition. [Optional: I implemented the AWS equivalent with an IAM OIDC identity provider and a role trust policy conditioned on the token's subject, and created a Microsoft Entra federated identity credential; I reviewed my tenant's user-consent settings and sign-in logs.] I deleted all resources and trust relationships afterward.
