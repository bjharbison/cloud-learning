# 07 — Serverless: Cloud Run and Cloud Run functions, Lambda, Azure Functions and Container Apps

> **In one sentence:** you'll be able to say when serverless is the right answer, deploy a container that nobody on the internet can call without an identity, and explain what an attacker does with a serverless function they control.

**Prereqs:** modules 00–06 (module 06 for containers and workload identity; module 04 for billing) · **Time:** ~3 hours incl. lab · **Phase:** 2

## Learning objectives

- Define serverless in practitioner terms: scale to zero, pay per use, provider-run infrastructure.
- Compare **Cloud Run** (services, jobs, functions), **AWS Lambda**, **Azure Functions**, and **Azure Container Apps**.
- Decide when serverless fits — and when VMs (module 05) or Kubernetes (module 06) fit better.
- Secure the two things that matter most: **who can invoke it** and **what its identity can do**.
- Explain serverless abuse in ATT&CK terms (T1648 and friends).

## Why this matters for the target roles

- **Customer engineer / architect:** "Do we need Kubernetes?" is often answered "no — use Cloud Run." Knowing where that line is saves customers a platform team.
- **Cloud security:** serverless removes OS patching but concentrates risk in IAM: invoker permissions, the service identity, and event triggers.
- **CTI:** adversaries use victims' functions for persistence and their own functions as cheap, disposable infrastructure.

---

## Concepts

### What "serverless" actually means

**Plain version:** you hand the provider code or a container; it runs it when requests or events arrive, scales the number of copies up and down — down to **zero** when idle — and bills for what you use.

There are still servers. You just don't see, size, patch, or pay for them while idle.

**Practitioner vocabulary:**

- **Scale to zero** — no running instances (and, on request-based billing, no compute charge) when there's no traffic.
- **Cold start** — the delay when a request arrives and a new instance must start first.
- **Concurrency** — how many requests one instance handles at once. Cloud Run instances can handle many; a classic Lambda execution environment handles one at a time ⚠️ (Lambda's newer managed-instance options weren't checked this run).
- **Event-driven** — triggered by something other than an HTTP call: a file landing in a bucket, a Pub/Sub message, a schedule.
- **Service identity / execution role** — the cloud identity the code runs as.

**Bridge to your homelab:** imagine Docker containers on your Proxmox host that don't exist until an MQTT message arrives, start in a second, handle it, and disappear — and you're billed per second of that work, not for the host.

### The serverless spectrum

Module 01's sliding line: serverless sits between PaaS and FaaS.

```
 VMs (05) ──► Kubernetes (06) ──► Serverless containers ──► Functions (FaaS)
 you run the OS   you run workloads    you bring a container     you bring a function
                  on a cluster         (Cloud Run, Container     (Cloud Run functions,
                                        Apps, Fargate*)            Lambda, Azure Functions)
 * AWS Fargate is serverless compute for ECS/EKS tasks (module 06), not an HTTP endpoint by itself.
```

### Google Cloud: Cloud Run (one platform, three shapes)

- **Cloud Run services** — an HTTPS endpoint backed by your container. Autoscales, including to zero.
- **Cloud Run jobs** — run a container to completion (batch, scheduled tasks). No endpoint.
- **Cloud Run functions** — you supply source code and an entry point; Google builds the container with buildpacks and **Cloud Build**. Google renamed **Cloud Functions** to **Cloud Run functions** on **August 21, 2024**; 1st-gen functions became "Cloud Run functions (1st gen)." You can deploy functions with `gcloud run deploy --source . --function …`.

**Billing (Tier 1 regions, default request-based):** you're charged only while an instance starts, shuts down, or is handling at least one request. Monthly free tier: **180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests**, aggregated per billing account. **Requests denied by IAM aren't billed.** Minimum instances keep instances warm at a lower idle rate — but they bill continuously. Instance-based billing is an alternative for steady workloads. Cloud Build and Artifact Registry (used by source deploys) are billed separately.

**Isolation:** Cloud Run offers two execution environments — first generation built on **gVisor** (a user-space kernel), second generation on **Linux microVMs** — both with seccomp filtering and two sandbox layers. Each instance is separated by a VM-monitor-enforced boundary.

### AWS: Lambda

- Upload a zip or container image; Lambda runs your handler in response to events (S3, SQS, API Gateway, EventBridge, and many more) or an HTTPS **function URL**.
- Runs in **Firecracker** microVMs on Nitro-based hosts; each function executes in a sandbox inside its microVM, bound to the customer's account.
- **Free tier:** 1 million requests and 400,000 GB-seconds per month (Provisioned Concurrency excluded).
- Identity: the function's **execution role** (an IAM role).

### Azure: Functions and Container Apps

- **Azure Functions** — functions with triggers and bindings. Microsoft now says to use the **Flex Consumption** plan for new serverless function apps (scales to zero, VNet integration). The original **Consumption** plan is "legacy"; Linux Consumption retires **September 30, 2028**. Other plans: Premium (prewarmed, no scale to zero), Dedicated (App Service), and running functions on Container Apps.
- **Azure Container Apps** — serverless containers, the closest analog to Cloud Run. Consumption plan monthly free grant per subscription: **180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests**. Scale to zero means no resource charges.

### When serverless fits — and when it doesn't

| Fits well | Fits poorly |
|---|---|
| Spiky or unpredictable traffic | Steady, high, 24×7 load (instance-hours can be cheaper on VMs/commitments) |
| Event-driven glue: file arrives → process it | Long-running or stateful processes |
| Small teams with no platform staff | Workloads needing kernel modules, privileged access, or a specific OS |
| APIs, webhooks, internal tools | Very latency-sensitive paths where cold starts hurt (mitigate with min instances, at a cost) |
| Proofs of concept (pay almost nothing when idle) | Heavy custom networking needs ⚠️ (all three have improved VPC integration; check specifics) |

**CE rule of thumb:** start at the most managed option that meets the requirement; move left (toward Kubernetes or VMs) only for a concrete reason.

**Bridge to your intel background:** serverless is a tasking model — no standing collection platform, just assets that spin up against a requirement and stand down when it's satisfied. The trade-off is the same: low idle cost, some spin-up latency, and you must trust the tasking system's access controls.

---

## Security: the two questions that matter

With no OS to patch, serverless security comes down to **who can call it** and **what it can do once called**.

### 1. Who can invoke it?

| | Cloud Run | Lambda function URL | Azure Container Apps / Functions |
|---|---|---|---|
| Default | **Invoker IAM check on** — callers need `roles/run.invoker` and a Google-signed ID token | You choose `AuthType`: **`AWS_IAM`** (SigV4-signed, IAM-authorized) or **`NONE`** (public, but still needs a resource-based policy) | Ingress `external` or `internal`; authentication is a separate built-in feature you turn on |
| Making it public | Disable the invoker check (Google's recommended way) **or** grant `roles/run.invoker` to `allUsers` | `AuthType NONE` + resource policy for `lambda:InvokeFunctionUrl` **and** `lambda:InvokeFunction` (both required for new URLs since October 2025) | `--ingress external` with no auth configured |
| Network-level control | **Ingress**: `all`, `internal`, `internal-and-cloud-load-balancing` — combined with IAM, not instead of it | Resource policies; VPC options ⚠️ not detailed this run | `internal` ingress (reachable only inside the environment); IP restrictions |
| Org-wide guardrail | Domain Restricted Sharing blocks `allUsers` grants; the `run.managed.requireInvokerIam` constraint can block disabling the check (not enforced by default) | SCPs / RCPs (module 03) | Azure Policy |

**Key point:** on Cloud Run, network ingress and IAM are **layers**. Google's docs state IAM authentication still applies to requests that reach the service through any ingress path.

### 2. What can it do once it runs?

Every serverless workload runs as an identity:

- **Cloud Run:** if you don't specify one, it runs as the **Compute Engine default service account** — which may hold **Editor** (module 05). Google strongly recommends a **user-managed service account** with only the roles it needs.
- **Lambda:** the **execution role**. The common anti-pattern is a role with `*` permissions "to get it working."
- **Azure:** a **managed identity** with scoped role assignments.

**Secrets:** use Secret Manager / AWS Secrets Manager / Key Vault references, not plaintext environment variables (module 16).

### 3. Event triggers are an attack surface too

A function triggered by "new object in bucket" runs whatever arrives in that bucket. Validate inputs; restrict who can write to trigger sources; watch for unexpected new triggers.

> **Shared responsibility:** the provider patches the OS, runtime sandbox, and scaling. **Invoker permissions, ingress settings, the service identity's roles, secrets handling, triggers, and the code itself are always the customer's.**

---

## Text diagram — Cloud Run with no public unauthenticated access

```
 Internet caller (no token) ──► run.app URL ──► IAM invoker check ──✗ 403 (not billed)
 Brian (Google identity, roles/run.invoker)
    └─ ID token ─────────────► run.app URL ──► IAM invoker check ──✓──► instance (gVisor / microVM)
                                                                          │ runs as SA "lab07-run"
                                                                          │ (no roles → can't touch other resources)
                                                                          ▼
                                                     Cloud Logging: request logs incl. 403s
 Ingress=internal: same IAM check, but requests from outside the VPC never reach it.
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Serverless containers (HTTP) | Cloud Run services | (App Runner, ⚠️ not covered this run); Fargate for ECS/EKS tasks | Azure Container Apps | Cloud Run and Container Apps have near-identical free grants |
| Functions | Cloud Run functions (renamed from Cloud Functions, Aug 2024) | AWS Lambda | Azure Functions (Flex Consumption recommended) | Google's functions now run on Cloud Run |
| Batch / run-to-completion | Cloud Run jobs | Lambda (short tasks), AWS Batch, ECS tasks | Container Apps jobs | |
| Free monthly allowance | 180k vCPU-s, 360k GiB-s, 2M requests (services); functions have their own allowance | 1M requests, 400k GB-s | Container Apps: 180k vCPU-s, 360k GiB-s, 2M requests | Google doesn't bill IAM-denied requests |
| Default invocation auth | **IAM required** (invoker check on) | Function URL: you choose `AWS_IAM` or `NONE` | Ingress choice; auth opt-in | Cloud Run is private by default |
| Network ingress control | all / internal / internal + Cloud Load Balancing | Resource policy (+ VPC options) | external / internal; IP restrictions | |
| Runtime identity | Service account (default: Compute default SA) | Execution role | Managed identity | Google's default may carry Editor |
| Sandbox | gVisor (gen1) or microVM (gen2) | Firecracker microVM | ⚠️ not verified this run | |

## Administer and monitor it

- **Deploys create revisions.** Cloud Run keeps immutable revisions and can split traffic between them (canary/rollback). Lambda has versions and aliases.
- **Logs:** request logs and stdout/stderr go to Cloud Logging, CloudWatch Logs, and Azure Monitor/Log Analytics. Note that Azure Container Apps creates a Log Analytics workspace by default unless you choose otherwise — and log ingestion can bill.
- **Config changes** (IAM policy on a service, ingress changes, new triggers) are control-plane events in Cloud Audit Logs / CloudTrail / Activity Log (module 18). Alert on a service becoming public.
- **Set a max instances value** — the serverless version of module 05's autoscaler max and module 04's ceiling.

## Security angle

Most common serverless misconfigurations:

1. **Public by accident** — `--allow-unauthenticated`, `AuthType NONE`, or external ingress on an internal tool.
2. **Over-privileged identity** — the default service account with Editor, or a `*` execution role.
3. **Secrets in environment variables** visible to anyone with read access to the configuration.
4. **No max instances** — denial-of-wallet risk.
5. **Untrusted trigger sources** — anyone who can write to the bucket can run your code with your function's identity.
6. **Vulnerable dependencies** in the deployed package or image — you still own the supply chain.

## Threat intel angle

- **T1648 Serverless Execution** — adversaries use serverless services to run code: crypto-mining, expanding access by attaching additional roles to a function, or **persistence** via event-triggered functions (MITRE's example: a function that adds credentials to any newly created user). Pacu (S1091) can create malicious Lambda functions.
- **T1583.007 Acquire Infrastructure: Serverless** and **T1584.007 Compromise Infrastructure: Serverless** — attackers use their own or victims' serverless endpoints as disposable redirectors and C2 front ends, hiding behind provider domains.
- **T1496.001 / T1496.004** — functions and serverless containers as compute or service hijacking (module 04).

**Detection ideas:** alert on new functions/services or new triggers by unusual principals; on IAM changes that make a service public; on a function's identity calling APIs it never used before.

**Bridge to your CTI work:** provider-hosted serverless URLs are hard to block by domain reputation — `*.run.app`, `*.lambda-url.*.on.aws`, `*.azurewebsites.net` (⚠️ domain patterns not re-verified this run) are shared by millions of legitimate apps. That's why adversaries like them and why detection has to lean on behavior and identity, not domains.

## Public sector notes

- **Service availability differs by government environment.** Before designing, check whether a serverless product is covered by the authorization you need (FedRAMP level, IL, Assured Workloads package, GovCloud, Azure Government) — modules 26–27.
- **Data boundary:** event-driven designs move data between services; each hop must stay inside the authorized boundary.
- **Cost predictability:** pay-per-use is attractive for spiky mission workloads, but set max instances and budgets (module 04) so a surge or abuse can't outrun the appropriation.

## Key takeaways

- Serverless = provider runs and scales the infrastructure, scales to zero, bills per use.
- Cloud Run covers services, jobs, and functions (Cloud Functions became Cloud Run functions in August 2024). AWS: Lambda (+ Fargate for containers). Azure: Functions (Flex Consumption) and Container Apps.
- Fits spiky, event-driven, stateless work; VMs or Kubernetes for steady, stateful, or OS-specific needs.
- Two questions decide serverless security: **who can invoke it** and **what its identity can do**.
- Cloud Run is **private by default** (invoker IAM check); keep it that way unless the service is meant to be public — and IAM-denied requests aren't even billed.
- Never run as the default service account; set max instances.
- Invoker access, ingress, identity, secrets, and triggers are **always the customer's**.

## Sources

- [Google Cloud — Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Google Cloud — Free cloud features (Cloud Run and Cloud Run functions free tiers)](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Google Cloud — Cloud Run security design overview](https://docs.cloud.google.com/run/docs/securing/security)
- [Google Cloud — Allowing public (unauthenticated) access](https://docs.cloud.google.com/run/docs/authenticating/public)
- [Google Cloud — Authenticate developers to Cloud Run](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [Google Cloud — Restrict network ingress for Cloud Run](https://docs.cloud.google.com/run/docs/securing/ingress)
- [Google Cloud — Introduction to service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)
- [Google Cloud — Deploy a Cloud Run function](https://docs.cloud.google.com/run/docs/deploy-functions)
- [Google Cloud — Cloud Run functions release notes (Aug 21, 2024 rename)](https://docs.cloud.google.com/functions/docs/release-notes)
- [Google Cloud — Deploy container images (sample `hello` image)](https://docs.cloud.google.com/run/docs/deploying)
- [AWS — Lambda pricing (free tier)](https://aws.amazon.com/lambda/pricing/)
- [AWS — Control access to Lambda function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html)
- [AWS — Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [AWS Whitepaper — Logical separation: serverless and containers (Firecracker)](https://docs.aws.amazon.com/whitepapers/latest/logical-separation/serverless-and-containers.html)
- [Microsoft — Azure Functions hosting options](https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale)
- [Microsoft — Billing in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/billing)
- [Microsoft — Ingress in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview)
- [Microsoft — `az containerapp env` reference (`--logs-destination`)](https://learn.microsoft.com/en-us/cli/azure/containerapp/env?view=azure-cli-latest)
- [MITRE ATT&CK — T1648 Serverless Execution](https://attack.mitre.org/techniques/T1648/), [T1583.007](https://attack.mitre.org/techniques/T1583/007/), [T1584.007](https://attack.mitre.org/techniques/T1584/007/), [Pacu S1091](https://attack.mitre.org/software/S1091/)

Verified: 2026-10-24
