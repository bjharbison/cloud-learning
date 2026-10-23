# Cross-Cloud Service Map

Rough equivalents. "Equivalent" rarely means identical — the **Notes** column is where the interview-worthy differences go. Modules append rows as they're built; the weekly review re-checks names.

| Category | Google Cloud | AWS | Azure | Notes |
|---|---|---|---|---|
| Top of hierarchy | Organization | AWS Organizations (management account) | Microsoft Entra tenant / root management group | Module 03 |
| Billing/isolation unit | Project | Account | Subscription | Projects are lighter-weight than AWS accounts or Azure subscriptions |
| Grouping | Folder | Organizational Unit (OU) | Management group / resource group | |
| Virtual machines | Compute Engine | Amazon EC2 | Azure Virtual Machines | |
| Managed Kubernetes | Google Kubernetes Engine (GKE) | Amazon EKS | Azure Kubernetes Service (AKS) | Kubernetes originated at Google |
| Object storage | Cloud Storage | Amazon S3 | Azure Blob Storage | |
| Virtual network | VPC network | Amazon VPC | Azure Virtual Network (VNet) | GCP VPCs are global; AWS VPCs and Azure VNets are regional |
| Key management | Cloud KMS | AWS KMS | Azure Key Vault | |
| Identity & access | Cloud IAM | AWS IAM | Azure RBAC + Microsoft Entra ID | |
| Audit logging | Cloud Audit Logs | AWS CloudTrail | Azure Activity Log | Module 18 |
| Monitoring | Cloud Monitoring | Amazon CloudWatch | Azure Monitor | Module 19 |
| Top-level identity | Google Account (2SV required) | Root user (MFA required) | Sign-up identity → Microsoft Entra ID tenant admin | Only AWS has a distinct "root user." Module 00 |
| Human admin sign-in | Google Account / Cloud Identity user with IAM roles | IAM Identity Center (permission sets) | Microsoft Entra ID user + Azure RBAC role | AWS's org instance of Identity Center needs AWS Organizations. Module 00 |
| Budgets and alerts | Cloud Billing budgets | AWS Budgets | Microsoft Cost Management budgets | All alert-only; none stop spend by default. Module 00 |
| Browser shell | Cloud Shell | AWS CloudShell | Azure Cloud Shell | Azure offers an ephemeral, no-storage mode. Module 00 |
| CLI | `gcloud` (named configurations) | `aws` (named profiles) | `az` | Module 00 |
| Hypervisor | KVM-based (custom VMM) | Nitro Hypervisor | Hyper-V-based | Module 01 |
| Hardware root of trust / offload | Titan, Caliptra / Titanium Offload Processors | Nitro Controller, Nitro Security Chip / Nitro Cards | Cerberus / Azure Boost | Same architectural pattern under different names. Module 01 |
| Metro / 5G edge compute | — (edge PoPs for CDN and load balancing) | Local Zones, Wavelength Zones | — (edge PoPs for Front Door/CDN) | Module 02 |
| U.S. government environment | Assured Workloads (controls on commercial regions); Google Distributed Cloud for disconnected | AWS GovCloud (US) Regions | Azure Government (isolated instance) | Different models: policy boundary vs separate environment. Modules 02, 27 |
| Provider health status | Google Cloud Service Health | AWS Health Dashboard | Azure Service Health | Module 02 |
| Restrict allowed regions | Org policy resource-location constraint | SCP with requested-region condition | Azure Policy "Allowed locations" | Module 02; detail in 20 |

*Seed rows reflect long-standing service names. Verified: pending first weekly review.*
