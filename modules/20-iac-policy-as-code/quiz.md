# 20 Quiz — Infrastructure as code and policy as code

1. In one sentence each: what do **declarative**, **idempotent**, and **drift** mean in IaC?
<details><summary>Answer</summary>

Declarative: you describe the end state and the tool figures out the steps. Idempotent: applying the same code again changes nothing. Drift: real infrastructure no longer matches the code, usually from manual (ClickOps) changes.
</details>

2. Put these in order and say which one a reviewer should approve: `apply`, `init`, `plan`, `validate`, `fmt`.
<details><summary>Answer</summary>

`init → fmt → validate → plan → apply`. The reviewer approves the **plan** — the exact diff — and the pipeline applies that saved plan.
</details>

3. True or false: marking a Terraform variable `sensitive = true` keeps it out of the state file.
<details><summary>Answer</summary>

False. It only redacts the value from CLI/UI output. It's still in state and plan files in plain text. Ephemeral values (1.10+) and write-only arguments (1.11+, where the provider supports them) are the features that keep values out of state.
</details>

4. Spot the misconfiguration: a team stores Terraform state in a Cloud Storage bucket that every project Editor can read, with versioning off, and the pipeline authenticates with a downloaded service-account key stored as a CI secret.
<details><summary>Answer</summary>

Three problems: state (which contains secrets) is readable by too many people; no versioning means a corrupted or deleted state can't be recovered; and a long-lived SA key in CI is a theft target. Fix: dedicated state bucket with narrow IAM, versioning, CMEK if required, Data Access logs; workload identity federation for the pipeline.
</details>

5. Which state-locking method does the Terraform S3 backend now recommend, and what happened to the old one?
<details><summary>Answer</summary>

`use_lockfile = true` (native S3 lock file, GA in Terraform 1.11). DynamoDB-based locking is deprecated and slated for removal.
</details>

6. Compare the three clouds' preventive guardrails in one line each, including one gotcha.
<details><summary>Answer</summary>

Google: Organization Policy (managed, legacy, and custom constraints; dry run) — needs an organization. AWS: SCPs (principal ceilings), RCPs (resource ceilings), declarative policies (service config) — SCPs/RCPs don't apply to the management account, declarative policies do. Azure: Azure Policy with effects like deny, modify, deployIfNotExists — can remediate as well as block; `DoNotEnforce` is its dry run.
</details>

7. A customer is still using Google Cloud Deployment Manager and Azure Blueprints. What do you tell them?
<details><summary>Answer</summary>

Both are retiring: Deployment Manager reached end of support March 31, 2026 and shuts down after June 30, 2027 (migrate to Infrastructure Manager/Terraform); Azure Blueprints retire January 31, 2027 (migrate to template specs and deployment stacks). Plan the migration now.
</details>

8. Scenario: an agency wants to guarantee no Cloud Storage bucket in its production folder can ever be made public, including buckets created by hand. What do you recommend, and why isn't Terraform alone enough?
<details><summary>Answer</summary>

Enforce the `storage.publicAccessPrevention` org policy at the production folder (dry run first, then enforce), managed as code. Terraform only controls what goes through the pipeline; a guardrail applies to every bucket regardless of how it was created. Add Checkov/Trivy in CI and posture management (module 21) to catch drift.
</details>

9. What did the March 2026 Trivy compromise target, and which ATT&CK techniques fit?
<details><summary>Answer</summary>

CI/CD pipelines: per the published advisory, a malicious release and repointed `trivy-action` tags ran credential-stealing code in build jobs ⚠️ (details relayed second-hand; read GHSA-69fq-xp46-6x23). T1195.001 (Compromise Software Dependencies and Development Tools) / T1195.002, leading to T1552.001-style credential theft. Mitigate by pinning actions to commit SHAs and using short-lived federated CI credentials.
</details>

10. Google Cloud Shell no longer includes Terraform. Where does that leave you, and what security step should accompany the install?
<details><summary>Answer</summary>

Install it yourself (e.g., into `$HOME`, which persists) or customize the environment to install at startup — and verify the download against HashiCorp's published SHA256SUMS (and ideally its GPG signature). Azure Cloud Shell still preinstalls Terraform; AWS CloudShell doesn't.
</details>

11. Where should you look to see whether a resource was changed by the pipeline or by a person, on Google Cloud?
<details><summary>Answer</summary>

Admin Activity audit logs: `principalEmail` (pipeline service account vs a human) and `requestMetadata.callerSuppliedUserAgent` (Terraform vs gcloud vs console). A human changing a Terraform-managed resource is a drift and detection signal.
</details>
