# 07 Lab — A private-by-default Cloud Run service (and its AWS and Azure cousins)

**Cost:** $0 expected on Google Cloud for Parts A1–A6. You deploy Google's prebuilt sample image (`us-docker.pkg.dev/cloudrun/container/hello`), so there's **no build step**. Request-based Cloud Run billing charges only while requests are being handled, the monthly free tier is 180,000 vCPU-seconds / 360,000 GiB-seconds / 2 million requests, and **requests denied by IAM aren't billed**. Optional A7 (a function built from source) uses Cloud Build and stores an image in Artifact Registry (0.5 GB free) — ⚠️ Cloud Build's free allowance wasn't verified this run; expect cents at most, and do its cleanup. AWS (optional): one Lambda function, inside Lambda's free tier (1M requests, 400,000 GB-seconds/month). Azure (optional): one Container App on the Consumption plan, inside its monthly free grant, with **logging turned off** so no Log Analytics workspace is created. · **Time:** 75–90 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Deploy a container to Cloud Run that **can't be called without an identity**.
2. Give it its **own** service account with no permissions — not the default.
3. Call it three ways: unauthenticated (refused), with an ID token, and through the local proxy.
4. Layer a **network ingress** restriction on top of IAM.
5. Find the evidence in logs.
6. (Optional) Same idea on Lambda (function URL with `AWS_IAM`) and Azure Container Apps (internal ingress).

## Prerequisites

- Modules 00–06 done; budget alerts active.
- `gcloud config list` shows your lab project.

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
gcloud services enable run.googleapis.com
```

---

## Part A — Google Cloud Run

### A1. A service account with nothing (CLI)

```bash
gcloud iam service-accounts create lab07-run --display-name="lab07 Cloud Run runtime (no roles)"
SA=lab07-run@$PROJECT_ID.iam.gserviceaccount.com
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:$SA" --format="value(bindings.role)"   # expect nothing
```

This is the identity the container will run as. With no roles, code in the container can't read buckets, call APIs, or touch anything else in the project. Compare with the default: the Compute Engine default service account, which may carry Editor (module 05).

### A2. Deploy — private by default (console, then CLI)

Console: **Cloud Run → Deploy container → Service** → **Test with a sample container** → name `lab07-hello`, region `us-central1` → **Authentication: Require authentication** → **Containers, Volumes, Networking, Security → Security → Service account: lab07-run** → **Revision scaling: Maximum instances 2** → **Labels**: `lab=07` → Create.

CLI (either, not both):

```bash
gcloud run deploy lab07-hello \
  --image=us-docker.pkg.dev/cloudrun/container/hello \
  --region=$REGION \
  --no-allow-unauthenticated \
  --service-account=$SA \
  --max-instances=2 \
  --ingress=all \
  --labels=lab=07

URL=$(gcloud run services describe lab07-hello --region=$REGION --format="value(status.url)")
echo $URL
```

Two settings worth saying out loud:

- `--no-allow-unauthenticated` keeps the **Invoker IAM check** on (it's on by default; the flag makes it explicit).
- `--max-instances=2` is the ceiling — the serverless version of module 05's autoscaler max.

### A3. Call it three ways (CLI)

**1. As an anonymous internet caller:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" $URL
```

**What you should see:** `403`. The request was rejected before any container ran — and Google doesn't bill IAM-denied requests.

**2. With your identity (an ID token from your Google account):**

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" $URL | head -20
```

**What you should see:** the sample's HTML. You're project Owner, which includes the invoke permission. In a real org you'd grant `roles/run.invoker` on this one service to a specific group.

**3. Through the authenticated local proxy:**

```bash
gcloud run services proxy lab07-hello --region=$REGION --port=8080 &
sleep 5; curl -s localhost:8080 | head -5
kill %1
```

Cloud Shell's **Web Preview → Preview on port 8080** also works while the proxy runs. The proxy adds your credentials, so you can use a browser against a private service.

### A4. Who can invoke? Read the policy (CLI)

```bash
gcloud run services get-iam-policy lab07-hello --region=$REGION
```

**What you should see:** no `allUsers` and no `allAuthenticatedUsers` bindings. If either ever appears on a service that should be private, that's an incident.

*Don't run this, just read it:* making the service public would be either `gcloud run services update lab07-hello --no-invoker-iam-check` (Google's recommended method when public access is intended) or adding `allUsers` with `roles/run.invoker`. If your organization enforces **Domain Restricted Sharing**, the `allUsers` grant would fail outright — a guardrail from module 03 doing its job.

### A5. Layer a network control on top (CLI)

```bash
gcloud run services update lab07-hello --region=$REGION --ingress=internal
sleep 15
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" $URL
```

**What you should see:** even **with** a valid token, the request from Cloud Shell no longer reaches the service — Cloud Shell isn't inside your VPC. ⚠️ Google doesn't document the exact status code for blocked ingress; note what you get (often a 404 page). Ingress decides **where** requests may come from; IAM decides **who**. Google's docs recommend using both.

Put it back so A6 has traffic to look at, then generate a little:

```bash
gcloud run services update lab07-hello --region=$REGION --ingress=all
sleep 15
for i in 1 2 3; do curl -s -o /dev/null -w "%{http_code} " $URL; done; echo
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $(gcloud auth print-identity-token)" $URL
```

### A6. Find the evidence (console, then CLI)

Console: **Cloud Run → lab07-hello → Logs**. Then **Logging → Logs Explorer** and run:

```
resource.type="cloud_run_revision"
resource.labels.service_name="lab07-hello"
```

CLI:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="lab07-hello" AND httpRequest.status>=200' \
  --limit=10 --freshness=1h \
  --format="table(timestamp,httpRequest.status,httpRequest.remoteIp,httpRequest.userAgent)"
```

**What you should see:** request entries with status codes — your `403`s and your `200`. Note the remote IP and user agent: that's the raw material for detecting someone probing your services. Then look at the **control-plane** side:

```bash
gcloud logging read \
  'protoPayload.serviceName="run.googleapis.com" AND resource.labels.service_name="lab07-hello"' \
  --limit=5 --freshness=1h --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

Those are your deploy and update calls — the events you'd alert on if someone made a service public (module 18).

### A7. (Optional) A Cloud Run function from source

This shows the "functions" shape of Cloud Run. It **builds** a container with Cloud Build and stores it in Artifact Registry.

```bash
mkdir -p ~/lab07-fn && cd ~/lab07-fn
cat > main.py <<'EOF'
import functions_framework

@functions_framework.http
def hello(request):
    return "hello from a Cloud Run function\n"
EOF
echo "functions-framework==3.*" > requirements.txt

gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy lab07-fn \
  --source . --function=hello --base-image=python313 \
  --region=$REGION --no-allow-unauthenticated \
  --service-account=$SA --max-instances=1 --labels=lab=07
cd ~
FN_URL=$(gcloud run services describe lab07-fn --region=$REGION --format="value(status.url)")
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" $FN_URL
```

If `python313` isn't accepted, the error lists valid base images; pick the newest Python one. If gcloud asks to create an Artifact Registry repository, say yes and note its name for cleanup. Notice it's the **same** service type, IAM model, and service identity as A2 — just built from source.

---

## Part B — AWS Lambda (optional): function URL that requires IAM

CloudShell, `us-east-1`, as `labadmin`.

```bash
aws iam create-role --role-name lab07-lambda-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name lab07-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
ROLE_ARN=$(aws iam get-role --role-name lab07-lambda-role --query Role.Arn --output text)

mkdir -p ~/lab07 && cd ~/lab07
cat > lambda_function.py <<'EOF'
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "hello from Lambda\n"}
EOF
zip -q fn.zip lambda_function.py
sleep 30   # IAM changes take time to propagate; if the next command fails with an IAM/role error, wait 30 s and rerun it
aws lambda create-function --function-name lab07-hello \
  --runtime python3.13 --handler lambda_function.lambda_handler \
  --role $ROLE_ARN --zip-file fileb://fn.zip --tags lab=07

FURL=$(aws lambda create-function-url-config --function-name lab07-hello \
  --auth-type AWS_IAM --query FunctionUrl --output text)
curl -s -o /dev/null -w "%{http_code}\n" $FURL                 # expect 403
aws lambda invoke --function-name lab07-hello out.json >/dev/null && cat out.json; echo
cd ~
```

**What you should see:** the anonymous request to the function URL gets `403` — `AWS_IAM` means every request must be SigV4-signed by an authorized principal. Invoking through the API as `labadmin` works, because your identity is authorized. The execution role has only `AWSLambdaBasicExecutionRole` (write its own logs) — nothing else.

## Part C — Azure Container Apps (optional): internal-only ingress

Azure Cloud Shell (Bash).

```bash
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az group create --name rg-lab07 --location eastus --tags lab=07
az containerapp env create --name lab07-env --resource-group rg-lab07 \
  --location eastus --logs-destination none
az containerapp create --name lab07-hello --resource-group rg-lab07 \
  --environment lab07-env \
  --image mcr.microsoft.com/k8se/quickstart:latest \
  --target-port 80 --ingress internal \
  --min-replicas 0 --max-replicas 1 --tags lab=07
FQDN=$(az containerapp show -n lab07-hello -g rg-lab07 --query properties.configuration.ingress.fqdn -o tsv)
echo $FQDN
curl -s -o /dev/null -m 10 -w "%{http_code}\n" https://$FQDN || echo "not reachable from outside (expected)"
```

**What you should see:** the app has an FQDN, but it isn't reachable from Cloud Shell — `internal` ingress means only other apps in the same environment can reach it. `--logs-destination none` avoids an auto-created Log Analytics workspace (ingestion can bill). `--min-replicas 0` lets it scale to zero. Note that Azure separates **ingress** (network reachability) from **authentication** (a separate built-in feature) — closer to Cloud Run's ingress + IAM split than to Lambda's single `AuthType` switch.

---

## Verify it worked

| Check | Expected |
|---|---|
| Anonymous `curl $URL` | `403` |
| `curl` with `print-identity-token` | `200` and HTML |
| `get-iam-policy` | No `allUsers` / `allAuthenticatedUsers` |
| `--ingress=internal` test from Cloud Shell | Blocked even with a valid token |
| Logs | 403 and 200 request entries; deploy/update audit entries |
| (B) Lambda URL anonymous | `403`; API invoke works |
| (C) Container App | Internal FQDN not reachable from Cloud Shell |

## What to notice (reflection questions)

1. Cloud Run denied the anonymous request *before* your container ran. Why does that matter for both cost and attack surface?
2. Your service ran as `lab07-run` with zero roles. What would change if it ran as a default service account holding Editor, and an attacker found a code-execution bug in the app?
3. Compare how each cloud expresses "public": Cloud Run (`allUsers` or invoker check off), Lambda (`AuthType NONE` + resource policy), Container Apps (external ingress, no auth). Which is easiest to do by accident?
4. Ingress `internal` blocked you even with a token. Describe a real design where you'd want both controls.
5. Write a plain-English detection rule for T1648 persistence in this project.

## Cleanup

**Google Cloud**

```bash
gcloud run services delete lab07-hello --region=$REGION --quiet
gcloud run services delete lab07-fn --region=$REGION --quiet 2>/dev/null || true    # if you did A7
gcloud iam service-accounts delete $SA --quiet
```

If you did **A7**, remove the build artifacts:

```bash
gcloud artifacts repositories list --location=$REGION
# delete the repository the source deploy created (often named cloud-run-source-deploy):
gcloud artifacts repositories delete REPO_NAME --location=$REGION --quiet
gcloud storage ls     # delete any bucket the source deploy created for uploads (name contains your project ID and "run-sources" or "cloudbuild"):
# gcloud storage rm -r gs://BUCKET_NAME
rm -rf ~/lab07-fn
```

Confirm:

```bash
gcloud run services list --region=$REGION                          # no lab07-*
gcloud iam service-accounts list --filter="email:lab07-run"        # Listed 0 items
gcloud artifacts repositories list --location=$REGION              # nothing from A7
```

**AWS**

```bash
aws lambda delete-function-url-config --function-name lab07-hello
aws lambda delete-function --function-name lab07-hello
aws logs delete-log-group --log-group-name /aws/lambda/lab07-hello 2>/dev/null || true
aws iam detach-role-policy --role-name lab07-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name lab07-lambda-role
rm -rf ~/lab07
aws lambda list-functions --query "Functions[?FunctionName=='lab07-hello']" --output text   # expect empty
```

**Azure**

```bash
az group delete --name rg-lab07 --yes
az group list --query "[?name=='rg-lab07']" -o table      # expect empty
```

**Final check — nothing billable remains:** no `lab07` Cloud Run services, service account, or Artifact Registry repo on Google; no `lab07-hello` function, role, or log group on AWS; no `rg-lab07` on Azure. Tomorrow, check Google **Billing → Reports** filtered by `lab=07`: expect $0.00 (or cents if you did A7).

## Write-up prompt

> On [date] I deployed a container to Google Cloud Run with the invoker IAM check enforced, a dedicated runtime service account holding no roles, and a maximum-instances ceiling. I verified anonymous requests were rejected with 403 while ID-token-authenticated requests succeeded, confirmed the service's IAM policy had no public principals, layered an internal-only ingress restriction on top of IAM, and reviewed the request and audit logs. [Optional: I deployed an AWS Lambda function URL with `AWS_IAM` auth and a minimal execution role, and an Azure Container App with internal-only ingress.] I deleted all resources afterward.
