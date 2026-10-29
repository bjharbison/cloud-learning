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
| Key management | Cloud KMS (key ring → key → versions) | AWS KMS | Azure Key Vault (Standard/Premium); Managed HSM | Key Vault also holds secrets and certificates. Module 16 |
| Identity & access | Cloud IAM (allow + deny policies on the hierarchy) | AWS IAM (identity + resource policies) | Azure RBAC (resources) + Microsoft Entra roles (directory) | Azure has two separate systems. Module 14 |
| Audit logging | Cloud Audit Logs (Admin Activity 400 d free; Data Access off) | AWS CloudTrail (Event history 90 d; data events off) | Azure Activity Log (90 d) + resource logs via diagnostic settings | Data-plane audit is opt-in on all three. Module 18 |
| Monitoring | Cloud Monitoring (Google Cloud Observability) | Amazon CloudWatch | Azure Monitor | Module 19 |
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
| Network hub | Network Connectivity Center (global; VPC + hybrid spokes) | Transit Gateway / Cloud WAN | Virtual WAN | Modules 10, 13 |
| Custom routes | Static routes (optionally by network tag) | Route tables | User-defined routes (UDRs) | Module 10 |
| Dynamic routing (BGP) | Cloud Router | Transit Gateway / virtual private gateway propagation | VPN/ExpressRoute gateways; Azure Route Server (BGP with NVAs) | Module 13 |
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
| Site-to-site VPN | HA VPN (2 interfaces, BGP, 99.99%); Classic VPN static only | Site-to-Site VPN (2 tunnels/connection; 5 Gbps tunnels on TGW/Cloud WAN) | VPN Gateway (AZ SKUs; Basic not for production) | Module 13 |
| Dedicated private circuit | Dedicated Interconnect (10/100/400 Gbps) | Direct Connect dedicated (1/10/100/400 Gbps) | ExpressRoute Direct (10/100/400 Gbps) | None encrypt by default. Module 13 |
| Partner private circuit | Partner Interconnect (50 Mbps–50 Gbps) | Direct Connect hosted connections (50 Mbps–25 Gbps) | ExpressRoute via provider (50 Mbps–10 Gbps) | Module 13 |
| Circuit encryption | MACsec; HA VPN over Cloud Interconnect | MACsec; VPN over Direct Connect | MACsec (Direct); IPsec over private peering | Module 13 |
| Cloud-to-cloud private link | Cross-Cloud Interconnect; Partner Cross-Cloud Interconnect for AWS | AWS Interconnect – multicloud (GA Apr 2026) | (via partners / Google CCI) | Module 13 |
| Global WAN over provider backbone | NCC site-to-site data transfer | Cloud WAN | ExpressRoute Global Reach; Virtual WAN | Module 13 |
| Explicit deny | IAM deny policies (org/folder/project) | `"Effect": "Deny"` in any policy type | Deny assignments (Azure-created only) | Module 14 |
| Permission ceiling (doesn't grant) | Principal access boundary policies | Permissions boundaries, SCPs, RCPs, session policies | — (Azure Policy governs configuration) ⚠️ | Module 14 |
| "Why allowed/denied?" | Policy Troubleshooter | IAM policy simulator | Check access | Module 14 |
| Excess-permission findings | Role recommendations; Policy Analyzer | Access Analyzer (unused/internal paid); last accessed info | Defender CSPM Permissions Management (CIEM) | Entra Permissions Management retired 2025. Module 14 |
| Keyless use of a workload identity | Service account impersonation (Token Creator) | `sts:AssumeRole` | Managed identity token | Module 14 |
| Human SSO from an external IdP | Cloud Identity/Workspace SSO; Workforce Identity Federation (sync-less) | IAM Identity Center (SAML 2.0 + SCIM) | Microsoft Entra ID (is the IdP) | Module 15 |
| Workload federation (CI/CD, other clouds) | Workload Identity Federation (OIDC, SAML, AWS, Azure, X.509) | IAM OIDC/SAML providers; IAM Roles Anywhere (X.509) | Federated identity credentials (app registration / user-assigned MI) | Module 15 |
| Sign-in policy engine | Context-Aware Access | IdP policies + IAM conditions | Conditional Access (Entra ID P1) | Module 15 |
| Just-in-time privileged access | Privileged Access Manager | Partners / TEAM sample (no native JIT) | Privileged Identity Management (P2/Governance) | Module 15 |
| Customer-managed encryption key | CMEK (Cloud KMS key on the resource; service agent needs encrypter/decrypter) | Customer managed key (AWS managed keys are legacy) | Customer-managed key in Key Vault / Managed HSM | Disable = kill switch; destroy = crypto-shred. Module 16 |
| Automated CMEK provisioning | Cloud KMS Autokey | — | — | Module 16 |
| Customer-supplied key per request | CSEK (Cloud Storage, Compute Engine) | SSE-C (blocked by default on new S3 buckets since Apr 2026) | Customer-provided keys (Blob) | Abused for ransomware in 2025. Module 16 |
| Single-tenant HSM | Single-tenant Cloud HSM (GA Dec 2025) | AWS CloudHSM (hsm2m.medium, FIPS 140-3 L3) | Managed HSM; Azure Cloud HSM (Dedicated HSM retiring Jul 2028) | Module 16 |
| Externally held keys | Cloud External Key Manager (Fortanix, Futurex, Thales) | KMS external key store (XKS) | Managed HSM external keys ⚠️ preview | Your key manager's uptime becomes the cloud's. Module 16 |
| Approve provider use of keys / data | Key Access Justifications (Assured Workloads); Access Approval | — ⚠️ | Customer Lockbox (Developer support plan or higher) | Module 16; Access Transparency in 18 |
| Secrets manager | Secret Manager (rotation = notifications) | AWS Secrets Manager (native rotation); SSM Parameter Store | Key Vault secrets (RBAC default for new vaults) | Module 16 |
| Key deletion safety net | Scheduled destroy 24 h–120 d (default 30), then delete | Pending deletion 7–30 d (not billed) | Soft delete 7–90 d + optional purge protection | Module 16 |
| Identity-aware web access (zero-trust PEP) | Identity-Aware Proxy (free core; direct on Cloud Run since Mar 2026) | AWS Verified Access (~$0.27/app-hour, no free tier) | Entra application proxy; Entra Private Access | Module 17 |
| Zero-trust policy engine | IAM + Access Context Manager access levels | Verified Access Cedar policies + trust providers | Conditional Access (Entra ID P1) | Module 17 |
| Enterprise zero-trust suite / SSE | Chrome Enterprise Premium (formerly BeyondCorp Enterprise) | — (building blocks + partners) | Global Secure Access (Entra Internet + Private Access; Entra Suite) | Google's App Connector shut down Jul 31, 2026. Module 17 |
| Device trust signal | Endpoint Verification (paid CEP feature) | Third-party device trust providers | Intune device compliance | Module 17 |
| Data-plane audit | Data Access audit logs (BigQuery always on) | CloudTrail data events ($0.10/100k) | Resource logs (diagnostic settings) | Module 18 |
| Org-wide log collection | Aggregated sink (org/folder, `--include-children`) | Organization trail → log archive account | Diagnostic settings deployed by Azure Policy | Module 18 |
| Log store + query language | Log buckets; Logging query language; Observability Analytics (SQL) | CloudWatch Logs + Logs Insights; Athena; CloudTrail Lake (closed to new customers May 2026) | Log Analytics workspace (KQL) | Module 18 |
| Identity sign-in logs | Cloud Identity / Workspace login audit | `ConsoleLogin` + Identity Center events in CloudTrail | Entra sign-in logs (7 d Free / 30 d P1+; export needs P1/P2) | Module 18 |
| Log integrity / immutability | `_Required` (undeletable); locked log buckets | Log file integrity validation (signed digests); S3 Object Lock | Immutable storage | Module 18 |
| Provider-staff access logs | Access Transparency (+ Access Approval) | — ⚠️ | Customer Lockbox | Module 18 |
| SaaS/productivity audit | Workspace audit logs ⚠️ | — | Microsoft Purview Audit (Standard expanded after Storm-0558) | Module 18 |
| Uptime / synthetic checks | Uptime checks (1M executions free/project/month); private uptime checks | CloudWatch Synthetics canaries | Application Insights standard availability tests (URL ping retires Sept 30, 2028) | Google warns against public checks for IL4/Assured Workloads. Module 19 |
| Alert notification target | Notification channels (email, Slack, PagerDuty, Pub/Sub, webhook) | SNS topics | Action groups | Module 19 |
| Alerting | Alerting policies (no charge before Sept 2027) | CloudWatch alarms (10 free; static, anomaly, composite) | Alert rules (metric, log search, activity log) | Module 19 |
| Guest OS telemetry agent | Ops Agent | CloudWatch agent | Azure Monitor Agent | Memory metrics need it on all three. Module 19 |
| Managed Prometheus | Managed Service for Prometheus (Monarch, 24-mo retention) | Amazon Managed Service for Prometheus | Azure Monitor managed Prometheus (18 mo) | Module 19 |
| Distributed tracing / APM | Cloud Trace (OTel) | X-Ray (SDKs in maintenance → OpenTelemetry); Application Signals | Application Insights | Module 19 |
| SLO tooling | Service monitoring SLOs + burn-rate alerts | Application Signals SLOs | ⚠️ not verified | Module 19 |
| Grafana | — (PromQL/Grafana-compatible querying) | Amazon Managed Grafana | Azure Managed Grafana; built-in Grafana dashboards | Module 19 |
| Native infrastructure as code | Infrastructure Manager (managed Terraform); Deployment Manager shuts down after June 30, 2027 | CloudFormation; AWS CDK | ARM templates / Bicep; deployment stacks (Blueprints retire Jan 31, 2027) | Google standardizes on Terraform. Module 20 |
| Terraform remote state backend | `gcs` (native locking) | `s3` (`use_lockfile`; DynamoDB locking deprecated) | `azurerm` (Blob Storage, native locking) | State holds secrets in plain text. Module 20 |
| Service-configuration baseline policy | Org policy managed constraints; security baseline (orgs created on/after May 3, 2024) | Declarative policies (EC2, VPC, EBS…) | Azure Policy `modify` / `deployIfNotExists` | AWS declarative policies also bind the management account. Module 20 |
| Guardrail dry run | Org policy `dryRunSpec`; Policy Simulator | — (test in a sandbox OU) ⚠️ | Assignment enforcement mode `DoNotEnforce` | Module 20 |
| Pre-deployment template/plan checks | `gcloud beta terraform vet` (Preview) | CloudFormation Guard; Control Tower proactive controls | Bicep linter; `what-if` | Third-party: Checkov, Trivy, Conftest. Module 20 |
| Cloud Shell Terraform | Not included since June 20, 2026 (install to `$HOME`) | Not included (CDK and SAM CLIs are) | Preinstalled, auth preconfigured | Module 20 |
| Posture management (CSPM) | Security Command Center Standard (free, needs an org) / Premium | AWS Security Hub CSPM (renamed original; needs AWS Config) | Defender for Cloud Foundational CSPM (free) / Defender CSPM | SCC Enterprise deprecated May 2026. Module 21 |
| Cloud threat detection | SCC Premium Event / Container / VM Threat Detection | Amazon GuardDuty (+ Extended Threat Detection) | Defender for Cloud workload plans (Servers, Storage, Containers…) | GuardDuty and Security Hub aren't on the AWS Free plan. Module 21 |
| Unified risk / attack paths | SCC Premium attack path simulations (org level) | AWS Security Hub (new, Dec 2025, OCSF) | Defender CSPM attack paths; Exposure Management | Module 21 |
| Default security benchmark | Google Cloud security baseline; Compliance Manager frameworks | AWS Foundational Security Best Practices | Microsoft cloud security benchmark (MCSB) | Module 21 |
| Findings to tickets | SCC notifications → Pub/Sub → your integration | Native Jira Cloud / ServiceNow; EventBridge | Workflow automation (Logic Apps); ServiceNow; governance rules | Module 21 |
| SIEM | Google Security Operations (UDM, YARA-L 2.0; sales-led, no self-serve trial) | No single SIEM: GuardDuty + Security Hub + Security Lake + OpenSearch Security Analytics | Microsoft Sentinel (KQL; Defender portal only after Mar 31, 2027; 31-day trial) | Many AWS shops bring Splunk, SecOps, or Sentinel. Module 22 |
| Detection rule language | YARA-L 2.0 | CloudWatch Logs Insights; EventBridge patterns; Sigma (OpenSearch) | KQL analytics rules (scheduled, NRT) | Sigma converts to most. Module 22 |
| Cross-source schema | UDM | OCSF | ASIM ⚠️ (not covered) | Module 22 |
| Cloud audit logs in the other SIEM | — | Sentinel `AWSCloudTrail` via S3 + SQS connector | Sentinel `GCPAuditLogs` via Pub/Sub connector (workload identity federation) | Module 22 |
| Lightweight native alerting on audit logs | Log-based alerting policies | Metric filters + alarms; EventBridge rules | Activity log alerts (free); log search alerts (billed) | Module 19, 22 |
| Disable a leaked workload credential | `gcloud iam service-accounts keys disable` | `aws iam update-access-key --status Inactive` | Remove app secret/certificate ⚠️ | Then deal with tokens already issued. Module 23 |
| Kill issued sessions/tokens | Disable SA or IAM deny policy (tokens live ≤ 1 h) | Revoke active sessions (`AWSRevokeOlderSessions`); deny policy | `revokeSignInSessions` + CAE (≤ ~15 min) | Module 23 |
| Provider action on publicly leaked keys | Auto-disable (`iam.serviceAccountKeyExposureResponse`, default since June 2024) | `AWSCompromisedKeyQuarantineV3` attached | ⚠️ not verified | Module 23 |
| Forensic disk copy | `gcloud compute snapshots create` | `aws ec2 create-snapshot` | `az snapshot create` | Snapshot before stopping/deleting. Module 23 |
| Evidence isolation pattern | Separate forensics project ⚠️ (pattern) | SRA forensics account | SOC subscription + immutable blob (legal hold) + Key Vault hashes | Module 23 |
| Provider IR service | Mandiant Incident Response | AWS Security Incident Response (metered, free tier) | Microsoft Incident Response | Module 23 |
| Threat-intel product | Google Threat Intelligence (Mandiant + VirusTotal + Google telemetry); GTIG reporting | Intel embedded in GuardDuty and automatic protections (MadPot, Mithra, Sonaris); no standalone feed ⚠️ | Defender Threat Intelligence capabilities inside Defender XDR and Sentinel | AWS embeds; Google and Microsoft sell. Module 24 |
| Bring-your-own threat intel | SecOps IOC ingestion / Applied Threat Intelligence ⚠️ details | GuardDuty threat / trusted entity lists | Sentinel TAXII 2.x connector; threat intelligence upload API (STIX) | Module 24 |
| Multi-stage attack correlation | SecOps composite detections | GuardDuty Extended Threat Detection (attack sequences, no extra charge) | Defender XDR incidents | Module 24 |
| Actor naming | UNC#### clusters; two-word cryptonyms (2026) | — | Weather families + Storm-#### | Module 24 |
| Disposable attack-emulation sandbox | Dedicated project (delete → 30-day pending deletion) | Separate account (needs AWS Organizations) | Separate subscription / resource group | Module 25 |
| Customer security-testing policy | No notice needed; follow AUP | Listed services without prior approval | No pre-approval since 2017; Rules of Engagement | Module 25 |

*Seed rows reflect long-standing service names (pending first weekly review). Rows tagged Module 00–03 verified 2026-10-23; Module 04–07 rows verified 2026-10-24; Module 08–11 rows verified 2026-10-25; Module 12–15 rows verified 2026-10-26; Module 16–19 rows verified 2026-10-27; Module 20–23 rows verified 2026-10-28; Module 24–27 rows verified 2026-10-29.*
