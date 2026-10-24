# Cross-Cloud Service Map

Rough equivalents. "Equivalent" rarely means identical — the **Notes** column is where the interview-worthy differences go. Modules append rows as they're built; the weekly review re-checks names.

| Category | Google Cloud | AWS | Azure | Notes |
|---|---|---|---|---|
| Top of hierarchy | Organization | AWS Organizations root (management account pays) | Microsoft Entra tenant / tenant root management group | Personal Google accounts may have no organization. Module 03 |
| Billing/isolation unit | Project | Account | Subscription | Projects are lighter-weight than AWS accounts or Azure subscriptions |
| Grouping | Folder (10 levels) | Organizational Unit (OU, 5 levels) | Management group (6 levels) | Azure resource groups sit *inside* subscriptions; see row below. Module 03 |
| Virtual machines | Compute Engine | Amazon EC2 | Azure Virtual Machines | |
| Managed Kubernetes | Google Kubernetes Engine (GKE) | Amazon EKS | Azure Kubernetes Service (AKS) | Kubernetes originated at Google |
| Object storage | Cloud Storage | Amazon S3 | Azure Blob Storage | |
| Virtual network | VPC network | Amazon VPC | Azure Virtual Network (VNet) | GCP VPCs are global; AWS VPCs and Azure VNets are regional |
| Key management | Cloud KMS | AWS KMS | Azure Key Vault | |
| Identity & access | Cloud IAM | AWS IAM | Azure RBAC + Microsoft Entra ID | |
| Audit logging | Cloud Audit Logs | AWS CloudTrail | Azure Activity Log | Module 18 |
| Monitoring | Cloud Monitoring | Amazon CloudWatch | Azure Monitor | Module 19 |
| Top-level identity | Google Account (2SV required) | Root user (MFA required) | Sign-up identity → Microsoft Entra ID tenant admin | Only AWS has a distinct "root user." Module 00 |
| Human admin sign-in | Google Account / Cloud Identity user with IAM roles | IAM Identity Center (permission sets) | Microsoft Entra ID user + Azure RBAC role | AWS's org instance of Identity Center needs AWS Organizations, which ends the AWS free plan; use an MFA-protected IAM user until then. Module 00 |
| Budgets and alerts | Cloud Billing budgets | AWS Budgets | Microsoft Cost Management budgets | All alert-only; none stop spend by default. Module 00 |
| Browser shell | Cloud Shell | AWS CloudShell | Azure Cloud Shell | Azure offers an ephemeral, no-storage mode. Module 00 |
| CLI | `gcloud` (named configurations) | `aws` (named profiles) | `az` | Module 00 |
| Hypervisor | KVM-based (custom VMM) | Nitro Hypervisor | Hyper-V-based | Module 01 |
| Hardware root of trust / offload | Titan, Caliptra / Titanium Offload Processors | Nitro Controller, Nitro Security Chip / Nitro Cards | Cerberus / Azure Boost | Same architectural pattern under different names. Module 01 |
| Metro / 5G edge compute | — (edge PoPs for CDN and load balancing) | Local Zones, Wavelength Zones | — (edge PoPs for Front Door/CDN) | Module 02 |
| U.S. government environment | Assured Workloads (controls on commercial regions); Google Distributed Cloud for disconnected | AWS GovCloud (US) Regions | Azure Government (isolated instance) | Different models: policy boundary vs separate environment. Modules 02, 27 |
| Provider health status | Google Cloud Service Health | AWS Health Dashboard | Azure Service Health | Module 02 |
| Restrict allowed regions | Org policy resource-location constraint | SCP with requested-region condition | Azure Policy "Allowed locations" | Module 02; detail in 20 |
| Guardrail (what may exist) | Organization Policy | SCPs / RCPs (AWS Organizations) | Azure Policy | Can block admins; SCPs skip the AWS management account. Module 03 |
| Lifecycle container inside the billing unit | (labels; no direct equivalent) | (tags; no direct equivalent) | Resource group | Deleting an Azure resource group deletes everything in it. Module 03 |
| Org identity backbone | Cloud Identity / Google Workspace | IAM Identity Center + per-account IAM | Microsoft Entra ID tenant | GCP org requires an identity domain (or a standalone org). Module 03 |
| Automated budget response | Budget → Pub/Sub programmatic notifications → your code | AWS Budgets actions (IAM/SCP deny, stop EC2/RDS) | Budget → action group → your automation | Only AWS has built-in response actions; none is a native hard cap. Module 04 |
| Cost allocation metadata | Labels (flow to billing automatically) | Cost allocation tags (must be activated) | Tags (+ Cost Management tag inheritance) | Google "tags" are a separate, policy-oriented feature. Module 04 |
| Quotas | Cloud Quotas (allocation / rate / concurrent) | Service Quotas | Subscription quotas (vCPUs per family per region) | Free trials restrict increases. Module 04 |
| Spend anomaly detection | Cost anomalies (Cloud Billing) | AWS Cost Anomaly Detection | Cost Management anomaly alerts | None real-time; Azure's isn't available in Azure Government. Module 04 |
| Flexible spend commitment | Spend-based CUDs (incl. flexible compute commitments) | Compute Savings Plans | Savings plan for compute | 1- or 3-year terms. Module 04 |
| Resource commitment | Resource-based CUDs | Reserved Instances / EC2 Instance Savings Plans | Azure Reservations | Google also has automatic sustained use discounts. Module 04 |

*Seed rows reflect long-standing service names (pending first weekly review). Rows tagged Module 00–03 verified 2026-10-23; Module 04–07 rows verified 2026-10-24.*
