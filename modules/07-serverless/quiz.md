# 07 Quiz — Serverless

1. Define "scale to zero" and "cold start," and explain how they're related.
<details><summary>Answer</summary>

Scale to zero: no instances run (and, on request-based billing, no compute is charged) when there's no traffic. Cold start: the extra latency when a request arrives and a new instance must start. Scaling to zero saves money but makes cold starts more likely; minimum instances reduce cold starts but bill continuously.
</details>

2. What happened to Google Cloud Functions in August 2024?
<details><summary>Answer</summary>

It was renamed Cloud Run functions (announced August 21, 2024); 1st-gen functions became Cloud Run functions (1st gen). Functions now run on Cloud Run and can be deployed with `gcloud run deploy --source . --function …`.
</details>

3. A Cloud Run service is deployed with default settings. Can an anonymous internet user call it?
<details><summary>Answer</summary>

No. The Cloud Run Invoker IAM check is on by default; callers need `run.routes.invoke` (e.g., `roles/run.invoker`) and a Google-signed ID token. Public access requires deliberately disabling the check or granting `roles/run.invoker` to `allUsers`.
</details>

4. Compare the free monthly allowances for Cloud Run services, AWS Lambda, and Azure Container Apps.
<details><summary>Answer</summary>

Cloud Run (request-based): 180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests per billing account. Lambda: 1 million requests and 400,000 GB-seconds. Container Apps (Consumption): 180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests per subscription. Cloud Run also doesn't bill requests denied by IAM.
</details>

5. What are Lambda function URL auth types, and what does a `NONE` URL still need?
<details><summary>Answer</summary>

`AWS_IAM` (requests must be signed by an authorized IAM principal) and `NONE` (no authentication). A `NONE` URL still requires a resource-based policy granting public access — and for new URLs since October 2025, both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction`.
</details>

6. Cloud Run ingress is set to `internal` and IAM requires authentication. A developer with `roles/run.invoker` calls it from home with a valid token. What happens, and why?
<details><summary>Answer</summary>

The request can't reach the service: internal ingress only accepts traffic from VPC networks (and certain Google services) in the project/perimeter. Ingress controls *where* traffic may come from; IAM controls *who*. Both must pass.
</details>

7. Spot the misconfiguration: "Our Cloud Run service uses the default service account; it only serves a static page, so it doesn't matter."
<details><summary>Answer</summary>

The default Compute Engine service account may hold Editor on the project. Any code-execution bug or malicious dependency in the container can use that identity against the whole project. Use a dedicated user-managed service account with only the roles needed (here, none).
</details>

8. Which Azure Functions plan does Microsoft recommend for new serverless function apps, and what's happening to Linux Consumption?
<details><summary>Answer</summary>

Flex Consumption. The original Consumption plan is legacy; Linux Consumption retires September 30, 2028.
</details>

9. Scenario: an agency needs a webhook that receives about 200 requests a day from a partner system, plus a nightly batch job. Recommend a Google Cloud design.
<details><summary>Answer</summary>

Cloud Run service for the webhook (scale to zero, near-zero cost at that volume), with IAM-authenticated invocation — the partner calls with a service-account identity granted `roles/run.invoker` — and max instances set. If the partner can't authenticate, put it behind a load balancer with additional controls rather than simply allowing `allUsers`. Cloud Run job for the nightly batch, triggered by Cloud Scheduler. Each runs as its own least-privilege service account; secrets from Secret Manager.
</details>

10. When is serverless the *wrong* answer?
<details><summary>Answer</summary>

Steady 24×7 high load (instance-hours on VMs/commitments may be cheaper), long-running or stateful processes, workloads needing privileged access/kernel modules/specific OS, or latency paths where cold starts are unacceptable and min instances would erase the cost benefit.
</details>

11. Describe two ways an adversary uses serverless, with ATT&CK IDs.
<details><summary>Answer</summary>

T1648 Serverless Execution — running code in the victim's account, e.g., a function triggered on user creation that adds attacker credentials (persistence), or a function given extra roles to escalate. T1583.007 / T1584.007 — acquiring or compromising serverless endpoints as disposable redirectors or C2 behind provider domains.
</details>

12. Why are `*.run.app`-style provider domains hard for defenders to block?
<details><summary>Answer</summary>

They're shared by huge numbers of legitimate applications, so domain-reputation blocking causes collateral damage. Detection has to rely on behavior and identity (who created the function, what it calls, unusual traffic patterns) rather than the domain.
</details>
