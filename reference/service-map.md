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

*Seed rows reflect long-standing service names. Verified: pending first weekly review.*
