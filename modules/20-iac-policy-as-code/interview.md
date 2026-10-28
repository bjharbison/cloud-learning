# 20 Interview Prep — Infrastructure as code and policy as code

## Likely questions

### Q1. "Why should a security team care about infrastructure as code?"

**Answer outline:**
- Every change becomes a reviewed, versioned diff: who, what, when, approver — change control with an audit trail.
- Misconfigurations get caught in the pull request by scanners (Checkov, Trivy, OPA), before deployment.
- Environments are consistent; incident recovery is a rebuild from code.
- Drift detection (`terraform plan`) exposes manual changes, including an intruder's.

**Strong signal:** pairing IaC with guardrails ("code is the happy path; org policy catches everything else"). **Avoid:** "IaC makes things secure" — it makes them *reviewable*.

### Q2. "What are the security risks of Terraform itself?"

**Answer outline:**
- State files hold secrets in plain text; `sensitive` only hides output. Remote, encrypted, versioned, locked, least-privilege state; never in git.
- Pipeline identity is effectively an admin — use workload identity federation, not keys; scope it per environment.
- Supply chain: pin providers, modules, and CI actions (the 2026 Trivy action compromise).
- Emergency console fixes that aren't written back get reverted on the next apply.

### Q3. "How would you stop anyone in an agency from creating resources outside approved U.S. regions or making storage public?"

**Answer outline:**
- Google: org policies `gcp.resourceLocations` and `storage.publicAccessPrevention` at the org or folder, dry run → enforce, managed as code; Policy Simulator before enforcing custom/managed constraints.
- AWS: SCP with a requested-region condition; account-level S3 Block Public Access plus RCPs; remember SCPs/RCPs skip the management account.
- Azure: Azure Policy "Allowed locations" and storage public-access policies with `deny`, starting in `DoNotEnforce`.
- Then detective coverage: posture management (module 21) and alerts on guardrail changes.

**Strong signal:** mentioning the dry-run phase and who is allowed to change guardrails.

### Q4. "Terraform or the native tools?"

**Answer outline:**
- Terraform: one language across clouds; Google's recommended path (Infrastructure Manager runs it as a managed service).
- Native: CloudFormation/CDK and Bicep get new features on day one and keep state server-side.
- Licensing question: Terraform is BSL since 2023; OpenTofu is the community fork. Let the customer's policy and skills decide.
- Note the migrations: Deployment Manager (shutdown after June 2027) and Azure Blueprints (January 2027).

### Q5. "Walk me through a secure IaC pipeline."

**Answer outline:** PR → fmt/validate → scanners → plan posted to PR → human approval → apply by a least-privilege federated identity → remote state with versioning and logging → cloud guardrails deny anything that slipped through → scheduled plan/posture scan for drift → alerts on guardrail and logging changes.

## 60-second executive explanation

"Today, a lot of cloud infrastructure is built by people clicking through web consoles, which means it's hard to know exactly what was changed, by whom, or why. Infrastructure as code means we write down what the environment should look like in files that go through the same review and approval as any software change. Every change has a requester, a reviewer, and a record, and we can rebuild the whole environment from those files after an incident. On top of that, we set organization-wide guardrails — also written as code — that the cloud enforces no matter who asks, such as 'nothing in this agency may be made public' or 'data stays in U.S. regions.' The result is fewer mistakes, faster audits, and evidence for our authorization package that's generated automatically."

## Whiteboard prompt

Draw a pipeline for a federal Google Cloud landing zone: repo → CI (workload identity federation) → scanners → plan → approval → apply → remote state bucket (versioned, CMEK, Data Access logs). Add the org → folders → projects tree with three org policies (resource locations, public access prevention, disable SA key creation) in dry run on a new folder and enforced on prod. Then show the AWS (SCP + RCP + declarative policy) and Azure (Azure Policy initiative) equivalents and circle where each could be bypassed.

## What you can honestly claim

- **After reading + quiz:** "I've studied infrastructure as code and policy as code across Google Cloud, AWS, and Azure — Terraform workflow and state security, native tools such as CloudFormation and Bicep, and guardrails including Organization Policy, SCPs/RCPs, and Azure Policy — and can discuss how they fit into a secure deployment pipeline."
- **After completing the lab:** "In a personal lab I used Terraform to deploy a Google Cloud Storage bucket with a hardened configuration, demonstrated that sensitive values persist in state, detected and corrected configuration drift, scanned Terraform with Checkov, [and enforced an organization policy as code to block public access]." Add AWS/Azure only if you ran those parts.
- **Still requires (cert / production experience / clearance):** building or operating production IaC pipelines, landing zones, or enterprise guardrail programs; a Terraform certification from HashiCorp ⚠️ (check the current exam name) or the Google Associate Cloud Engineer would make basic Terraform/GCP operations claimable. Your change-control and configuration-management experience from national security systems is real — describe it as it was, at a publicly discussable level, not as cloud IaC experience.
