# 20 — Infrastructure as code and admin automation: Terraform, CLIs, policy as code (Org Policy, SCPs, Azure Policy)

> **In one sentence:** you'll be able to explain why defining cloud infrastructure and guardrails as reviewed code is a security control, read and run a small Terraform configuration on any of the three clouds, keep state files (and the secrets in them) out of harm's way, and compare the three providers' policy-as-code guardrails.

**Prereqs:** modules 00–19 (module 03 for org policy, SCPs, and Azure Policy basics; module 08 for bucket settings; module 18 for audit logs) · **Time:** ~4 hours incl. lab · **Phase:** 5

## Learning objectives

- Explain **infrastructure as code (IaC)** and why it improves **security, auditability, and repeatability**.
- Read and write basic **Terraform**: providers, resources, variables, outputs, **state**, and the `init → plan → apply → destroy` loop.
- Explain why **state files contain secrets** and how to store them safely.
- Compare **Organization Policy**, **SCPs/RCPs/declarative policies**, and **Azure Policy** as **guardrails as code**.
- Describe **shift-left** scanning (Checkov, Trivy, OPA) and where it fits next to cloud guardrails.
- Map IaC and pipeline abuse to ATT&CK.

## Why this matters for the target roles

- **Customer engineer / architect:** every landing zone, reference architecture, and proof of concept you hand a customer today is Terraform. "Can you give us that as code?" is a standard ask.
- **Cloud security:** most misconfigurations are born in a pull request. Catching them in code review is cheaper than catching them in production (module 21).
- **CTI:** CI/CD pipelines and state files hold the keys to the kingdom. Attackers know it — the March 2026 Trivy supply-chain compromise targeted exactly those pipelines.

---

## Concepts

### Clicking vs code

**Plain version:** instead of building infrastructure by clicking through a console, you write a text file that *describes* what should exist. A tool reads the file and makes the cloud match it.

**Practitioner vocabulary:**

- **Infrastructure as code (IaC)** — infrastructure defined in version-controlled files and deployed by a tool.
- **Declarative** — you describe the end state ("a bucket with versioning on"); the tool works out the steps. Terraform, CloudFormation, and Bicep are declarative. **Imperative** — you list steps (a bash script of `gcloud` commands).
- **Idempotent** — running the same config twice gives the same result; the second run changes nothing.
- **Drift** — the real infrastructure no longer matches the code, usually because someone clicked in the console.
- **ClickOps** — the slang for console-driven changes, and the main source of drift.

**Why security teams care:**

| Without IaC | With IaC |
|---|---|
| "Who opened that port, and why?" — dig through audit logs | Git history: who, when, the reviewer, the ticket |
| Each environment built by hand, slightly differently | Dev, test, and prod from the same reviewed code |
| Misconfig found after deployment | Misconfig found in the pull request by a scanner |
| Rebuild after an incident from memory | Rebuild from code (module 23) |

**Bridge from your homelab:** if you've ever kept a `docker-compose.yml` in git so you could rebuild a stack after a Proxmox failure, you've done IaC. Terraform is the same idea pointed at a cloud API — and the "infra repo" becomes as sensitive as your OPNsense config backup.

**Bridge from intel:** IaC is change control with a built-in audit trail. A merged pull request is the approved change request, signed by the requester and reviewer; the audit log (module 18) is the record of what actually executed. When they disagree, you have drift — or an intruder.

### Terraform in ten minutes

**Terraform** (HashiCorp, now an IBM company — IBM completed the acquisition in February 2025) is the most widely used multi-cloud IaC tool. Current release line: **1.17** (October 2026).

| Piece | What it is | Example |
|---|---|---|
| **Provider** | Plugin that talks to one API | `hashicorp/google` (v8, GA September 2026), `hashicorp/aws`, `hashicorp/azurerm` |
| **Resource** | One thing to create | `google_storage_bucket`, `aws_s3_bucket`, `azurerm_storage_account` |
| **Variable / output** | Inputs and printed results | `var.project_id`, `output "bucket_url"` |
| **State** | Terraform's record of what it built, mapping code to real resource IDs | `terraform.tfstate` |
| **Backend** | Where state lives | local file, Cloud Storage (`gcs`), S3, Azure Blob (`azurerm`), HCP Terraform |

The loop:

```
terraform init      → download providers, set up the backend
terraform fmt       → normalize formatting
terraform validate  → check syntax and references (no API calls)
terraform plan      → compare code + state + reality; show the diff
terraform apply     → make the changes (asks "yes" unless -auto-approve)
terraform destroy   → delete everything this state tracks
```

**The plan is the security artifact.** It's the exact diff a reviewer approves. HashiCorp warns against `-auto-approve` outside of a pipeline that already shows a reviewed plan.

**Licensing note:** HashiCorp moved Terraform from an open-source license to the **Business Source License (BSL 1.1)** in August 2023. The community fork **OpenTofu** (a Linux Foundation project, accepted into the CNCF Sandbox in April 2025; v1.13 current) keeps a compatible language under an open-source license ⚠️ (license name not re-verified this run). Agencies and vendors ask about this; know both exist. **HCP Terraform** (renamed from Terraform Cloud in 2024) is HashiCorp's hosted runner, with a free tier of 500 managed resources.

### State files contain secrets

This is the single most important Terraform security fact.

- State holds **every attribute** of every resource — including database passwords, generated keys, connection strings, and object contents — in **plain text** for local state.
- Marking a variable `sensitive = true` **only hides it from screen output**. The value is still written to state and plan files, and `terraform output -raw` prints it.
- **Ephemeral** values (Terraform 1.10+) and **write-only arguments** (1.11+, provider support required, e.g., `password_wo` on `google_sql_user`) keep some secrets out of state entirely. Use them where the provider supports them.

**Rules:**

1. **Never commit state or plan files.** This repo's `.gitignore` already blocks `*.tfstate`, `*.tfstate.*`, `*.tfplan`, `*.tfvars`, and `.terraform/` — look at it. Still run `git status` before every commit.
2. **Use a remote backend** with encryption and tight IAM: a Cloud Storage bucket (with **Object Versioning**, optionally a **CMEK** key — module 16), S3 with encryption and versioning, or Azure Blob Storage.
3. **Lock state** so two people can't apply at once: the `gcs` and `azurerm` backends lock natively; the S3 backend now uses `use_lockfile = true` (GA in Terraform 1.11), and DynamoDB-based locking is **deprecated**.
4. **Audit access to state** (Data Access logs on the state bucket, module 18). Reading state is credential access.

**Bridge to intel:** treat a state file like a classified annex. The main document (your `.tf` code) is shareable for review; the annex (state) has the sensitive particulars and needs its own handling caveat and access list.

### The provider-native tools

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Native IaC | **Infrastructure Manager** (managed Terraform: runs in Cloud Build, stores state and revisions for you) | **CloudFormation** (JSON/YAML), **CDK** (TypeScript, Python, Java, C#, Go → synthesizes CloudFormation) | **ARM templates** (JSON), **Bicep** (compiles to ARM; no state file — Azure holds state) |
| Retired / retiring | **Deployment Manager**: end of support March 31, 2026; shuts down after June 30, 2027 → migrate to Infrastructure Manager | — | **Azure Blueprints**: retiring January 31, 2027 → template specs + **deployment stacks** (with deny settings) |
| Drift handling | Terraform `plan` | CloudFormation **drift detection** and drift-aware change sets | Bicep / ARM `what-if` |

**Takeaway:** Google's own answer is Terraform (Google co-maintains the provider). AWS and Azure push their native languages but fully support Terraform. In a multi-cloud agency, Terraform is the common language.

### Guardrails as code (policy as code)

Module 03 introduced guardrails — controls on **what may exist**, not **who** can act. Policy as code means those guardrails are also files in git, reviewed and deployed like infrastructure.

**Google Cloud — Organization Policy**

- **Constraints** in three flavors: **managed** (named `service.managed.name`, e.g., `iam.managed.disableServiceAccountKeyCreation`), **managed (legacy)** (formerly "predefined," e.g., `storage.publicAccessPrevention`, `gcp.resourceLocations`), and **custom** constraints you write in CEL for ~100 supported services (Cloud Storage, Compute Engine, GKE, IAM, Cloud SQL…).
- **Dry run**: logs would-be violations without blocking (`gcloud org-policies set-policy FILE --update-mask=dryRunSpec`), then enforce with `--update-mask=spec`. **Policy Simulator** tests custom and managed constraints against your existing resources before you enforce.
- **Google Cloud security baseline** (formerly called "secure by default"): organizations created on or after May 3, 2024 start with constraints enforced, including blocking service-account key creation and upload, disabling automatic Editor grants to default service accounts, domain-restricted sharing, and uniform bucket-level access.
- Setting policies needs **Organization Policy Administrator** at the org (module 03). **Projects without an organization can't use org policies** — they rely on resource-level settings instead.
- Changes can take up to 15 minutes to take effect.

**AWS — Organizations policies**

- **SCPs** cap what principals in member accounts can do. Since **September 2025** they support the full IAM policy language (conditions, resource ARNs, `NotResource`).
- **RCPs** (November 2024) cap what can be done *to* resources — now around 60 services, including S3, STS, KMS, Secrets Manager, and SQS. Both are ceilings; neither grants.
- **Declarative policies** (December 2024) set a service configuration org-wide — e.g., EC2: block public AMIs and EBS snapshots, require IMDSv2 defaults, VPC Block Public Access. Unlike SCPs, they **do** apply to the management account.
- **Detective** side: **AWS Config rules** and **conformance packs**; **AWS Control Tower** packages controls as **preventive** (SCP/RCP/declarative), **detective** (Config), and **proactive** (CloudFormation hooks that check templates before deployment). **CloudFormation Guard** is the open-source rule engine for templates.

**Azure — Azure Policy**

- **Policy definitions** with **effects**: `deny`, `audit`, `append`, `modify`, `auditIfNotExists`, `deployIfNotExists` (auto-remediate, e.g., deploy the diagnostic settings from module 18), `denyAction` (block deletes), `manual`, `disabled`, and others.
- **Initiatives** bundle definitions; **assignments** attach them to a management group, subscription, or resource group; **exemptions** carve out exceptions with an expiry and reason.
- **Enforcement mode `DoNotEnforce`** is Azure's dry run: evaluate and report compliance without denying.
- **Enterprise Policy as Code (EPAC)** is an open-source, Microsoft-employee-maintained community project for managing policy from git — not an officially supported product.

### Shift left: scan the code before it ships

Guardrails catch mistakes at deploy time; scanners catch them at **pull-request time** ("shift left").

| Tool | What it does |
|---|---|
| **Checkov** (Apache 2.0, Prisma Cloud) | Scans Terraform, plans, CloudFormation, ARM/Bicep, Kubernetes for misconfigurations |
| **Trivy** (`trivy config`) | Misconfiguration scanning; **tfsec** has been folded into it |
| **OPA / Conftest** | Write your own rules in **Rego** and test any config format |
| **HCP Terraform policies** | **Sentinel** or OPA policy sets that can block a run (advisory → mandatory) |
| **`gcloud beta terraform vet`** | Checks a Terraform plan against a Google policy library (Preview) |

**Defense in depth:** scanner in the pipeline (advisory) → policy check on the plan (blocking) → cloud guardrail (Org Policy/SCP/Azure Policy, blocking) → posture management finding (module 21, detective). Each layer catches what the previous one missed, including the ClickOps that never went through a pipeline.

---

## Text diagram — a secure IaC pipeline

```
 Engineer ── git push ──► Pull request ──► CI pipeline (identity via workload identity federation, no keys — module 15)
                               │              ├─ terraform fmt / validate
                               │              ├─ Checkov / Trivy / Conftest  ── fail on HIGH
                               │              └─ terraform plan  ──► plan posted to PR
                          Reviewer approves (two-person rule)
                               │
                               ▼
                         terraform apply (pipeline SA, least privilege)
                               │
          ┌────────────────────┼─────────────────────────────┐
          ▼                    ▼                             ▼
  Remote state bucket   Cloud API ── guardrail check ──► Org Policy / SCP / Azure Policy
  (versioned, CMEK,      (Admin Activity / CloudTrail /     (deny = apply fails, logged)
   Data Access logs)      Activity Log record the change)
                               │
                               ▼
                 Posture scan (module 21) finds drift from ClickOps
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Native IaC | Infrastructure Manager (Terraform) | CloudFormation, CDK | ARM, Bicep, deployment stacks | Google standardizes on Terraform rather than its own language |
| Retiring tool | Deployment Manager (shutdown after June 30, 2027) | — | Azure Blueprints (Jan 31, 2027) | Migration deadlines matter for customers still on them |
| Terraform state backend | `gcs` (native locking) | `s3` (`use_lockfile`; DynamoDB deprecated) | `azurerm` (native blob locking) | Bicep/CloudFormation keep state server-side |
| Preventive guardrail | Organization Policy (managed, legacy, custom constraints) | SCPs, RCPs, declarative policies | Azure Policy (`deny`, `denyAction`) | SCPs/RCPs skip the management account; declarative policies don't |
| Dry run | Org policy dry-run spec; Policy Simulator | — (test in a sandbox OU) ⚠️ | `DoNotEnforce` enforcement mode | |
| Auto-remediation | — (pair with detective tools, module 21) | Config remediation actions | `modify`, `deployIfNotExists` | Azure Policy can fix as well as block |
| Pre-deploy template checks | `gcloud beta terraform vet` (Preview) | CloudFormation Guard; Control Tower proactive controls | Bicep linter; what-if | |
| Default baseline | Security baseline for orgs created on/after May 3, 2024 | — (you write SCPs) | — (you assign policies; Defender assigns MCSB audits, module 21) | Google ships enforced guardrails by default |

## Administer and monitor it

- **Who can change guardrails?** Keep Org Policy Administrator, SCP management, and `Microsoft.Authorization/policyAssignments/write` to a small, separately audited group.
- **Alert on guardrail changes** (module 19): Org Policy `SetOrgPolicy`/`UpdatePolicy` ⚠️ (exact method names vary by API version), AWS Organizations `UpdatePolicy`/`DetachPolicy`, Azure policy assignment deletes in the Activity Log.
- **Watch for drift:** scheduled `terraform plan` in CI (non-zero diff = alert); CloudFormation drift detection; Azure Policy compliance.
- **The pipeline is production:** its service account usually has broad rights. Protect it like an admin.

## Security angle

1. **State or `.tfvars` committed to git** — secrets in history forever (rotate them; deleting the commit isn't enough).
2. **State bucket readable by the whole project** — anyone with read can harvest credentials.
3. **Pipeline uses a long-lived service-account key** — use workload identity federation (module 15).
4. **Over-privileged pipeline identity** (Owner/Administrator) — one compromised job owns everything.
5. **Unpinned providers, modules, and CI actions** — a supply-chain attack waiting to happen. Pin versions and commit the dependency lock file in real projects (this curriculum's `.gitignore` excludes it only because labs are throwaway); pin CI actions to commit SHAs.
6. **Guardrails only in audit mode forever** — dry run is a phase, not a destination.
7. **ClickOps fixes during an incident never written back to code** — the next `apply` silently reverts the fix.

> **Shared responsibility — say it plainly:** providers supply the IaC services and the guardrail engines. **Writing the code, protecting state and pipeline credentials, choosing and enforcing guardrails, and the identity, firewall, and access settings your code deploys are always the customer's.** A provider will happily deploy a public bucket if your code asks for one and no guardrail stops it.

## Threat intel angle

| Technique | ATT&CK | What it looks like |
|---|---|---|
| Steal credentials from files (state, `.tfvars`, CI variables) | **T1552.001** Unsecured Credentials: Credentials In Files | Reads of state objects; secrets found in repos |
| Compromise build tools / dependencies | **T1195.001** Compromise Software Dependencies and Development Tools; **T1195.002** Compromise Software Supply Chain | Malicious provider, module, or CI action version |
| Modify cloud compute infrastructure | **T1578** (Defense Impairment tactic since ATT&CK v19) | Unexpected instances, snapshots, or images created outside the pipeline |
| Modify cloud resource hierarchy to escape guardrails | **T1666** | `LeaveOrganization`, projects moved between folders, subscriptions moved to another tenant |
| Disable or modify cloud logs | **T1685.002** (module 18) | Pipeline or attacker removes sinks/trails |

ATT&CK has no dedicated "CI/CD pipeline" technique; T1195.001 is the closest fit.

**The case to know — Trivy, March 2026:** attackers published a malicious Trivy release and repointed most of the `trivy-action` GitHub Action version tags to code that stole CI secrets (CVE-2026-33634 / GitHub advisory GHSA-69fq-xp46-6x23) ⚠️ (details from the published advisory as relayed by a secondary advisory database; read the GitHub advisory directly). The lesson is uncomfortable: a *security scanner* in the pipeline was the way in. Mitigations: pin actions to full commit SHAs, give CI jobs short-lived federated credentials, and scope secrets per job.

**Bridge to your CTI work:** the pipeline is a high-value collection target, like a crypto custodian or a PKI server on a classified network. Ask: what can the pipeline identity touch, where are its credentials, and would you see it act outside a merged change?

## Public sector notes

- IaC makes **configuration baselines and change control** (NIST 800-53 CM family) demonstrable: the repo *is* the baseline, and PR history *is* the change record — strong ATO evidence (module 26).
- Google's Assured Workloads and FedRAMP blueprints, AWS GovCloud landing zones, and Azure Government landing zones are distributed as Terraform/Bicep code — see module 27.
- A customer still on **Deployment Manager** or **Azure Blueprints** has a hard migration deadline (2027) — a real conversation starter.

## Key takeaways

- IaC turns infrastructure into reviewed, versioned code: better security, auditability, and rebuild speed.
- Terraform loop: `init → fmt → validate → plan → apply → destroy`; the **plan** is what reviewers approve.
- **State holds secrets in plain text**; `sensitive` only hides output. Remote, encrypted, versioned, locked, least-privilege state — never in git.
- Guardrails as code: **Org Policy** (managed/custom constraints, dry run), **SCPs/RCPs/declarative policies**, **Azure Policy** (deny, modify, deployIfNotExists, DoNotEnforce).
- Layer scanners (Checkov, Trivy, OPA) → plan policy → cloud guardrails → posture management.
- Google Cloud Shell no longer ships Terraform (June 2026); Deployment Manager and Azure Blueprints are retiring.
- Pipelines and state are attacker targets (T1552.001, T1195); the code and guardrails you deploy are **always the customer's** responsibility.

## Sources

- [HashiCorp — Terraform CLI apply](https://developer.hashicorp.com/terraform/cli/commands/apply), [Manage sensitive data](https://developer.hashicorp.com/terraform/language/manage-sensitive-data), [Ephemeral values](https://developer.hashicorp.com/terraform/language/manage-sensitive-data/ephemeral), [Write-only arguments](https://developer.hashicorp.com/terraform/language/manage-sensitive-data/write-only), [gcs backend](https://developer.hashicorp.com/terraform/language/backend/gcs), [s3 backend](https://developer.hashicorp.com/terraform/language/backend/s3), [azurerm backend](https://developer.hashicorp.com/terraform/language/backend/azurerm), [Terraform releases](https://releases.hashicorp.com/terraform/), [HCP Terraform docs](https://developer.hashicorp.com/terraform/cloud-docs), [HCP Terraform policy sets](https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/manage-policy-sets), [BSL announcement](https://www.hashicorp.com/en/blog/hashicorp-adopts-business-source-license), [Google provider 8.0 GA](https://www.hashicorp.com/en/blog/terraform-provider-for-google-cloud-80-now-generally-available)
- [IBM — completes acquisition of HashiCorp](https://newsroom.ibm.com/2025-02-27-ibm-completes-acquisition-of-hashicorp,-creates-comprehensive,-end-to-end-hybrid-cloud-platform), [OpenTofu](https://opentofu.org/)
- [Google Cloud — Cloud Shell release notes](https://docs.cloud.google.com/shell/docs/release-notes), [Install and configure Terraform](https://docs.cloud.google.com/docs/terraform/install-configure-terraform), [Store Terraform state in Cloud Storage](https://docs.cloud.google.com/docs/terraform/resource-management/store-state), [Infrastructure Manager overview](https://docs.cloud.google.com/infrastructure-manager/docs/overview), [Deployment Manager deprecation](https://docs.cloud.google.com/deployment-manager/docs/deprecations), [Policy validation](https://docs.cloud.google.com/docs/terraform/policy-validation), [gcloud beta terraform vet](https://docs.cloud.google.com/sdk/gcloud/reference/beta/terraform/vet)
- [Google Cloud — Organization Policy overview](https://docs.cloud.google.com/resource-manager/docs/organization-policy/overview), [Create and manage policies](https://docs.cloud.google.com/organization-policy/create-organization-policies), [Security baseline constraints](https://docs.cloud.google.com/organization-policy/manage-baseline-constraints), [Custom constraint supported services](https://docs.cloud.google.com/organization-policy/reference/custom-constraint-supported-services), [Test org policies with Policy Simulator](https://docs.cloud.google.com/policy-intelligence/docs/test-organization-policies), [gcloud org-policies describe](https://docs.cloud.google.com/sdk/gcloud/reference/org-policies/describe), [Public access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention)
- [AWS — Organizations policy types](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies.html), [SCPs support full IAM language (Sept 2025)](https://aws.amazon.com/about-aws/whats-new/2025/09/aws-organizations-iam-language-service-control-policies/), [RCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html), [Declarative policies announcement](https://aws.amazon.com/about-aws/whats-new/2024/12/aws-declarative-policies/), [EC2 declarative policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ec2.html), [Control Tower control behavior](https://docs.aws.amazon.com/controltower/latest/controlreference/control-behavior.html), [Config conformance packs](https://docs.aws.amazon.com/config/latest/developerguide/conformance-packs.html), [CloudFormation Guard](https://docs.aws.amazon.com/cfn-guard/latest/ug/what-is-guard.html), [CloudFormation drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html), [CDK synthesis](https://docs.aws.amazon.com/cdk/v2/guide/configure-synth.html), [CloudShell compute environment](https://docs.aws.amazon.com/cloudshell/latest/userguide/vm-specs.html)
- [Microsoft — Azure Policy effects](https://learn.microsoft.com/en-us/azure/governance/policy/concepts/effect-basics), [Assignment structure (enforcement mode)](https://learn.microsoft.com/en-us/azure/governance/policy/concepts/assignment-structure), [az policy assignment](https://learn.microsoft.com/en-us/cli/azure/policy/assignment?view=azure-cli-latest), [Bicep overview](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview), [Blueprints retirement](https://learn.microsoft.com/en-us/azure/governance/blueprints/blueprint-retirement), [Cloud Shell features](https://learn.microsoft.com/azure/cloud-shell/features), [Store Terraform state in Azure Storage](https://learn.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage), [Enterprise Policy as Code](https://azure.github.io/enterprise-azure-policy-as-code/)
- [Checkov](https://github.com/bridgecrewio/checkov), [tfsec → Trivy](https://github.com/aquasecurity/tfsec), [Trivy Terraform scanning](https://trivy.dev/docs/latest/tutorials/misconfiguration/terraform/), [Conftest](https://www.conftest.dev/)
- [MITRE ATT&CK — v20 release notes (Oct 2026)](https://attack.mitre.org/resources/updates/updates-october-2026/), [v19 (Apr 2026)](https://attack.mitre.org/resources/updates/updates-april-2026/), [T1552.001](https://attack.mitre.org/techniques/T1552/001/), [T1195](https://attack.mitre.org/techniques/T1195/), [T1578](https://attack.mitre.org/techniques/T1578/), [T1666](https://attack.mitre.org/techniques/T1666/), [T1685.002](https://attack.mitre.org/techniques/T1685/002/)

Verified: 2026-10-28
