# 07 Interview Prep — Serverless

## Likely questions

### Q1. "When would you recommend Cloud Run over GKE?"

**Answer outline:**
- Stateless, request- or event-driven services; spiky traffic; small team without platform engineers.
- Cloud Run gives you containers without managing a cluster: scale to zero, per-use billing, revisions and traffic splitting, private by default.
- GKE when you need many tightly coupled services, custom networking or scheduling, stateful workloads, daemonsets/sidecars at scale, or portability across environments.
- Start at the most managed option; move toward GKE or VMs only for a concrete requirement.

**Strong signal:** a crisp decision rule plus one example each way.
**Avoid:** "serverless is always cheaper."

### Q2. "How do you secure a Cloud Run service?"

**Answer outline:**
- **Who can invoke:** keep the invoker IAM check on; grant `roles/run.invoker` to specific identities; Domain Restricted Sharing org policy blocks accidental `allUsers`.
- **Where from:** ingress `internal` or `internal-and-cloud-load-balancing` for non-public services; IAP or a load balancer with Cloud Armor for user-facing ones (module 12).
- **What it can do:** dedicated least-privilege service account, never the default.
- Secrets from Secret Manager; max instances; signed images; audit-log alerts on IAM changes to services.

**Strong signal:** "ingress is where, IAM is who — use both."

### Q3. "Compare Cloud Run, Lambda, and Azure's options."

**Answer outline:**
- Cloud Run: containers (services, jobs) and functions on one platform; private by default; concurrency per instance.
- Lambda: functions (zip or image) with rich AWS event sources; Firecracker microVMs; function URLs with `AWS_IAM` or `NONE`.
- Azure: Functions (Flex Consumption recommended) and Container Apps (closest to Cloud Run; same free-grant numbers).
- Biggest practical difference: default exposure and how "public" is expressed.

### Q4. "What's the threat model for serverless?"

**Answer outline:**
- No OS to patch, so risk concentrates in IAM: public invocation, over-privileged identities, untrusted triggers, vulnerable dependencies.
- Adversaries: T1648 for execution and persistence (event-triggered backdoors), T1583.007/T1584.007 for infrastructure behind provider domains.
- Telemetry: request logs (status, IP, user agent) and audit logs (who created/changed functions and IAM policies).

### Q5. "A customer worries serverless costs are unpredictable. What do you say?"

**Answer outline:**
- At low or spiky volume, it's usually far cheaper than always-on servers; IAM-denied requests on Cloud Run aren't billed.
- Control it: max instances, budgets and anomaly alerts (module 04), request-based vs instance-based billing choice, commitments for steady baselines.
- Be honest: at sustained high load, VMs or committed capacity can be cheaper — model it.

## 60-second executive explanation

"Serverless means we hand the cloud our application and it runs it only when someone needs it — thousands of copies during a surge, none at all overnight — and we pay only for the time it's actually working. There are no servers for our team to patch. That makes it ideal for things like data-intake services, partner integrations, and internal tools. The security work shifts to two questions we control completely: who is allowed to call the service, and what the service itself is allowed to touch. We set both to the minimum, so even if someone found a flaw in the application, there'd be very little they could reach."

## Whiteboard prompt

Draw an event pipeline: a partner uploads a file to a Cloud Storage bucket → an event triggers a Cloud Run service → it writes results to BigQuery. Label each identity (uploader, trigger, service account) and the single role each needs. Mark the ingress setting and who has `roles/run.invoker`. Then draw how an attacker with write access to the bucket could abuse the trigger, and what control limits the damage.

## What you can honestly claim

- **After reading + quiz:** "I've studied serverless platforms on Google Cloud, AWS, and Azure — Cloud Run, Lambda, Azure Functions, and Container Apps — including invocation security, service identities, and when serverless fits."
- **After completing the lab:** "In a personal lab I deployed a Cloud Run service that required IAM-authenticated invocation, ran it under a dedicated zero-permission service account, layered ingress restrictions, and verified behavior in request and audit logs." Add the Lambda/Container Apps sentence only if you did those parts.
- **Still requires (cert / production experience / clearance):** building and operating production serverless systems, event-driven architectures at scale, or serverless deployments inside an authorized government boundary. Don't claim "serverless developer experience." The Google Associate Cloud Engineer and Professional Cloud Developer exams (⚠️ Developer exam not checked this run) are claimable milestones.
