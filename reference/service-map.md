# Cross-Cloud Service Map

Rough equivalents. "Equivalent" rarely means identical — the **Notes** column is where the interview-worthy differences go. Modules append rows as they're built; the weekly review re-checks names.

| Category | Google Cloud | AWS | Azure | Notes |
|---|---|---|---|---|
| Top of hierarchy | Organization | AWS Organizations root (management account pays) | Microsoft Entra tenant / tenant root management group | Personal Google accounts may have no organization. Module 03 |
| Billing/isolation unit | Project | Account | Subscription | Projects are lighter-weight than AWS accounts or Azure subscriptions |
| Grouping | Folder (10 levels) | Organizational Unit (OU, 5 levels) | Management group (6 levels) | Azure resource groups sit *inside* subscriptions; see row below. Module 03 |
| Virtual machines | Compute Engine | Amazon EC2 | Azure Virtual Machines | Module 05 |
| Managed Kubernetes | Google Kubernetes Engine (GKE) | Amazon EKS | Azure Kubernetes Service (AKS) | Kubernetes originated at Google. Module 06 |
| Object storage | Cloud Storage | Amazon S3 | Azure Blob Storage | Azure adds a storage-account layer (keys, network settings) above containers. Module 08 |
| Virtual network | VPC network | Amazon VPC | Azure Virtual Network (VNet) | GCP VPCs are global; AWS VPCs and Azure VNets are regional. Module 10 |
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
| VM blueprint | Instance template | Launch template | Scale set model | Module 05 |
| Managed VM fleet | Managed instance group (zonal or regional) | Auto Scaling group | Virtual Machine Scale Set (Uniform / Flexible) | Azure's orchestration mode is fixed at creation. Module 05 |
| Identity-based admin access to VMs | OS Login + IAP TCP forwarding | Systems Manager Session Manager | Azure Bastion (Developer SKU free for dev/test) | Only Session Manager needs no inbound network path at all. Module 05 |
| VM's own cloud identity | Attached service account | Instance profile (IAM role) | Managed identity | Google's default compute SA may hold Editor. Module 05 |
| Instance metadata hardening | Metadata server (`Metadata-Flavor` header ⚠️ unverified) | IMDSv2 (session tokens) | IMDS | Module 05 |
| Boot integrity | Shielded VM | NitroTPM / UEFI Secure Boot | Trusted Launch (default for new Gen2 VMs) | Module 05 |
| Confidential VMs | Confidential VM (AMD SEV / SEV-SNP, Intel TDX) | AMD SEV-SNP instances | Confidential VMs (AMD SEV-SNP, Intel TDX) | AWS adds a 10% fee on shared tenancy. Module 05 |
| Container registry | Artifact Registry | Amazon ECR | Azure Container Registry (ACR) | Module 06 |
| Kubernetes with provider-managed nodes | GKE Autopilot (pod-request billing) | EKS Auto Mode; EKS on Fargate | AKS Automatic | Module 06 |
| Kubernetes control-plane fee | $0.10/cluster-hr; $74.40/month credit covers one Autopilot or zonal cluster | $0.10/cluster-hr (standard support) | Free tier: no fee (no SLA); Standard/Premium paid | GKE and EKS charge $0.60/hr on extended support. Module 06 |
| Pod-to-cloud identity | Workload Identity Federation for GKE | EKS Pod Identity / IRSA | Microsoft Entra Workload ID | Always on in GKE Autopilot. Module 06 |
| Human access to the Kubernetes API | Google IAM + Kubernetes RBAC | EKS access entries + RBAC | Entra ID + Kubernetes RBAC or Azure RBAC | Module 06 |
| Kubernetes network policy enforcement | GKE Dataplane V2 (default on new Autopilot; choose on Standard) | VPC CNI network policy (must enable) | Standard: Cilium / NPM / Calico (must choose); AKS Automatic: Cilium by default | Module 06 |
| Serverless containers (HTTP) | Cloud Run services | AWS Fargate (tasks for ECS/EKS); App Runner ⚠️ not covered | Azure Container Apps | Cloud Run and Container Apps share the same free-grant numbers. Module 07 |
| Functions (FaaS) | Cloud Run functions (renamed from Cloud Functions, Aug 2024) | AWS Lambda | Azure Functions (Flex Consumption recommended) | Module 07 |
| Run-to-completion containers | Cloud Run jobs | ECS tasks / AWS Batch | Container Apps jobs | Module 07 |
| Serverless invocation auth | Invoker IAM check (on by default; `roles/run.invoker`) | Function URL `AuthType` `AWS_IAM` / `NONE` | Ingress external/internal + built-in authentication | Cloud Run is private by default. Module 07 |
| Serverless runtime identity | Service account (default: Compute default SA) | Execution role | Managed identity | Module 07 |
| Block storage | Persistent Disk / Hyperdisk / Local SSD | Amazon EBS | Azure Managed Disks | Local SSD data is lost when the VM stops. Modules 05, 08 |
| Managed file storage | Filestore (NFS) | Amazon EFS (NFS); FSx family | Azure Files (SMB/NFS) | Module 08 |
| Coldest storage class | Archive (online, ms reads, 365-day min) | S3 Glacier Deep Archive (restore first, 180-day min) | Archive tier (offline, rehydrate up to 15 h, 180-day min) | Google's archive class stays online. Module 08 |
| Automatic storage tiering | Autoclass | S3 Intelligent-Tiering | Lifecycle management (+ smart tier ⚠️ unverified) | Module 08 |
| Recover deleted objects | Soft delete (on by default, 7 days) + Object Versioning | S3 Versioning (delete markers) | Blob/container soft delete + blob versioning | Module 08 |
| WORM / immutability | Retention policy + Bucket Lock; Object Retention Lock | S3 Object Lock (governance/compliance) + legal hold | Immutable storage (unlocked/locked) + legal hold | Locking is irreversible on all three. Module 08 |
| Block public object access | Uniform bucket-level access + public access prevention | S3 Block Public Access + ACLs disabled (defaults since Apr 2023) | `AllowBlobPublicAccess = false` | Module 08 |
| Bearer URL to an object | Signed URL | Presigned URL | SAS token | Treat as secrets; keep short-lived. Module 08 |
| Managed relational (MySQL/PostgreSQL/SQL Server) | Cloud SQL | Amazon RDS | Azure Database for MySQL/PostgreSQL (flexible server); Azure SQL Database / SQL Managed Instance | Module 09 |
| High-performance PostgreSQL-compatible | AlloyDB for PostgreSQL | Amazon Aurora | Azure Database for PostgreSQL ⚠️ closest match not verified | Module 09 |
| Globally distributed relational | Spanner | Amazon Aurora DSQL | Cosmos DB (multi-model) | Spanner offers up to 99.999% SLA. Module 09 |
| Document database | Firestore | DynamoDB / DocumentDB ⚠️ | Azure Cosmos DB | Module 09 |
| Wide-column NoSQL | Bigtable | DynamoDB; Keyspaces ⚠️ | Cosmos DB (Cassandra API) ⚠️ | Module 09 |
| In-memory cache | Memorystore (Valkey, Redis, Memcached) | ElastiCache ⚠️ | Azure Cache for Redis ⚠️ | Module 09 |
| Data warehouse | BigQuery (serverless; per-TiB or slots) | Amazon Redshift (provisioned / Serverless); Athena for SQL on S3 | Synapse dedicated SQL pools; Fabric Data Warehouse | Module 09 |
| Security data lake | BigQuery / Observability Analytics via aggregated log sinks | Amazon Security Lake (S3 + OCSF) | Microsoft Sentinel data lake | Module 09; SIEMs in 22 |
| Subnet scope | Regional | One Availability Zone | Regional (spans zones) | Reserved IPs per subnet: Google 4, AWS 5, Azure 5. Module 10 |
| Default network | `default` auto-mode VPC (permissive rules) | Default VPC per region (public subnets) | None | Block with `compute.skipDefaultNetworkCreation`. Module 10 |
| Central multi-team network | Shared VPC (host + service projects) | VPC sharing (AWS RAM, same Organization) | Hub-and-spoke VNets | Module 10 |
| Network peering | VPC Network Peering | VPC peering | VNet peering (incl. global) | Non-transitive on all three. Module 10 |
| Network hub | Network Connectivity Center | Transit Gateway / Cloud WAN | Virtual WAN | Module 10; hybrid in 13 |
| Custom routes | Static routes (optionally by network tag) | Route tables | User-defined routes (UDRs) | Module 10 |
| Dynamic routing (BGP) | Cloud Router | Transit Gateway / virtual private gateway propagation | VPN/ExpressRoute gateways; Route Server ⚠️ | Module 13 |
| Outbound internet for private VMs | Cloud NAT | NAT gateway (hourly + per GB) | NAT Gateway (new VNets private by default after Mar 31, 2026 API versions) | Module 10–11 |
| Per-workload stateful rules | VPC firewall rules / network firewall policies (target by SA or secure tag) | Security groups (allow-only) | NSGs + application security groups | Module 11 |
| Subnet-level stateless rules | — | Network ACLs | — (NSGs are stateful) | Module 11 |
| Org-level network rules | Hierarchical firewall policies (org/folder) | AWS Firewall Manager | Virtual Network Manager security admin rules | Lower levels can't override Google's hierarchical rules. Module 11 |
| L7 firewall / IPS | Cloud NGFW Enterprise | AWS Network Firewall | Azure Firewall (Premium: IDPS) | Module 11 |
| Private access to provider APIs (free) | Private Google Access | Gateway endpoints (S3, DynamoDB) | Service endpoints | Module 11 |
| Private endpoint to a specific service | Private Service Connect | Interface endpoints (PrivateLink) | Private Endpoint (Private Link) | Turn off the public path afterward. Module 11 |
| API-level exfiltration boundary | VPC Service Controls | Data perimeter pattern (SCP/RCP + endpoint/resource policies) | Private Endpoints + network security perimeter | Module 11 |
| Global L7 load balancer | Global external Application Load Balancer (one anycast IP, Premium tier) | CloudFront / Global Accelerator in front of regional ALBs | Azure Front Door Standard/Premium (classic retires Mar 31, 2027) | Google's is a single global service. Module 12 |
| Regional L7 load balancer | Regional external / internal Application Load Balancer | Application Load Balancer (ALB) | Application Gateway v2 (v1 retired Apr 28, 2026) | Module 12 |
| L4 load balancer | Network Load Balancer (proxy or passthrough) | Network Load Balancer (NLB) | Azure Load Balancer (Standard; Basic retired Sep 30, 2025) | Passthrough preserves client IP. Module 12 |
| Appliance insertion load balancer | — (NGFW endpoints / packet mirroring) | Gateway Load Balancer | Gateway Load Balancer SKU | Module 12 |
| DNS-based global routing | Cloud DNS routing policies (geo, weighted, failover) | Route 53 routing policies | Traffic Manager | Module 12 |
| Authoritative / private DNS | Cloud DNS public and private zones (100% SLO) | Route 53 public and private hosted zones | Azure DNS + Private DNS zones | Route 53 zones aren't prorated. Module 12 |
| Hybrid DNS resolution | Cloud DNS forwarding zones + inbound/outbound server policies | Route 53 VPC Resolver endpoints (renamed from Route 53 Resolver) | DNS Private Resolver | Module 12–13 |
| DNS-layer filtering | Response policies; DNS Armor ⚠️ | Route 53 Resolver DNS Firewall | DNS security policy ⚠️ | Module 12 |
| CDN | Cloud CDN (on global external ALB); Media CDN | Amazon CloudFront (pay-as-you-go or flat-rate plans) | Azure Front Door | Azure CDN from Edgio retired Jan 2025. Module 12 |
| WAF | Cloud Armor security policies (OWASP CRS 4.22 / 3.3 rules) | AWS WAF web ACLs + managed rule groups | Azure WAF (DRS 2.2 on App Gateway / Front Door) | Module 12 |
| Free DDoS baseline | Always-on L3/L4 for global external and proxy load balancers | AWS Shield Standard | DDoS infrastructure protection | Module 12 |
| Paid DDoS tier | Cloud Armor Enterprise (Paygo / Annual) | AWS Shield Advanced ($3,000/mo, 1-yr) | DDoS Network Protection / IP Protection | Top tiers include cost protection. Module 12 |

*Seed rows reflect long-standing service names (pending first weekly review). Rows tagged Module 00–03 verified 2026-10-23; Module 04–07 rows verified 2026-10-24; Module 08–11 rows verified 2026-10-25; Module 12–15 rows verified 2026-10-26.*
