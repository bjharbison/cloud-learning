# Glossary

Plain-language definition first, then how practitioners use the term. Alphabetical. Modules append as they're built.

**Admission controller (Kubernetes)** — Code in the API server that inspects create/update requests after authentication and can reject or modify them before they're stored. Pod Security Admission, OPA Gatekeeper, Kyverno, and Binary Authorization work here. (Module 06)

**Antideficiency Act** — U.S. law (31 U.S.C. § 1341 and related sections) barring federal employees from obligating or spending more than an appropriation provides, or before funds are appropriated. Why elastic, bill-after-use cloud spend worries government comptrollers. (Module 04)

**Assured Workloads (Google Cloud)** — A service that applies compliance control packages (data residency, personnel access, service restrictions) to folders, used for FedRAMP, DoD IL, CJIS, ITAR and similar needs on Google's commercial infrastructure. (Module 02; deep dive in 27)

**Autoscaling** — Automatically adding or removing VMs (or containers) based on a signal such as CPU, load-balancer capacity, a custom metric, or a schedule, within a minimum and maximum you set. The maximum is a cost and blast-radius control. (Module 05)

**AWS GovCloud (US)** — Isolated AWS Regions (US-East and US-West) for sensitive U.S. government workloads, administered by U.S. citizens per AWS. (Module 02; deep dive in 27)

**AZ ID (AWS)** — A consistent identifier for an Availability Zone (e.g., `use1-az1`) that means the same physical location in every account, unlike AZ names (`us-east-1a`), which can map differently per account in some older Regions. (Module 02)

**Azure Bastion** — Azure's managed service for RDP/SSH to VMs over their private IPs from the portal (or native client on higher SKUs), so VMs need no public IP. The Developer SKU is free for dev/test with tight limits. (Module 05)

**Azure Government** — A physically isolated instance of Azure for eligible U.S. government customers. (Module 02; deep dive in 27)

**Azure Policy** — Azure's guardrail service: rules about what resources may exist or how they must be configured, assigned at management group, subscription, or resource group scope and inherited downward. (Module 03)

**Break-glass account** — An emergency admin identity kept locked away, used only when normal admin access fails, and alerted on whenever it signs in. (Module 00)

**Budget (cloud billing)** — A spending threshold that sends alerts as actual or forecasted cost crosses percentages you set. On all three clouds, budgets notify; they don't stop resources. (Module 00)

**Budget action (AWS)** — An AWS Budgets feature that responds to a threshold automatically or after approval: apply an IAM policy or SCP, or stop specific EC2/RDS instances. The closest thing to a native cost brake on the three clouds — still not a hard cap. (Module 04)

**Cloud Identity** — Google's identity service for organizations, without Workspace email. Its free edition needs a domain you own and verify; it gives you a Google Cloud organization node. (Module 03)

**Cloud Run (Google Cloud)** — Google's serverless platform for containers: services (HTTPS endpoints that autoscale, including to zero), jobs (run to completion), and functions (built from source). Invocation requires IAM by default. (Module 07)

**Cloud Run functions** — Google's functions-as-a-service, renamed from Cloud Functions on August 21, 2024; functions are built into containers with buildpacks and Cloud Build and run on Cloud Run. AWS analog: Lambda; Azure: Azure Functions. (Module 07)

**Cloud shell** — A free, temporary Linux environment in the browser, pre-authenticated and preloaded with the provider's CLI: Google Cloud Shell, AWS CloudShell, Azure Cloud Shell. Keeps credentials off your laptop. (Module 00)

**CNI (Container Network Interface)** — The plugin that gives Kubernetes pods their network. Whether NetworkPolicy is actually enforced depends on it: GKE Dataplane V2 enforces by default; EKS's VPC CNI and AKS need it enabled or chosen. (Module 06)

**Cold start** — The extra latency when a serverless request arrives and a new instance must start first. Reduced with minimum instances, at the cost of paying for idle capacity. (Module 07)

**Committed use discount (CUD, Google Cloud)** — A discount for committing to use specific resources (resource-based) or to spend a minimum amount (spend-based) for one or three years. AWS analogs: Savings Plans and Reserved Instances; Azure: reservations and savings plan for compute. (Module 04)

**Confidential VM** — A VM whose memory is encrypted by the CPU with keys the hypervisor can't read (AMD SEV/SEV-SNP, Intel TDX), with hardware attestation of its state. Protects data in use. Available on specific machine series on all three clouds. (Module 05)

**Container** — A packaged app plus its libraries that runs as an isolated process on a shared host kernel, separated by Linux namespaces (what it can see) and cgroups (what it can use). Faster and denser than a VM; a weaker isolation boundary. Homelab equivalent: Docker or Proxmox LXC. (Module 01)

**Control plane / data plane** — The control plane is where you *manage* resources (create a VM, change a policy) — almost always API calls. The data plane is where the resource *does its work* (traffic through a VM, reads from a bucket). Logging and permissions often differ between the two.

**Cost allocation tag (AWS)** — A resource tag that AWS Billing uses to group costs. User-defined tags must be activated in the Billing console before they appear in cost reports. (Module 04)

**Dataplane V2 (GKE)** — GKE's eBPF-based networking layer, which always enforces Kubernetes NetworkPolicy and offers network policy logging; enabled by default on new Autopilot clusters. (Module 06)

**Deployment (Kubernetes)** — An object declaring how many identical pods to run and how to roll out changes; a controller keeps reality matching it. Docker analog: `restart: always` plus "run N copies." (Module 06)

**Edge location** — A small provider site near users, used for caching (CDN), DNS, and traffic entry rather than general compute. AWS also offers Local Zones (metro compute) and Wavelength Zones (inside 5G networks). (Module 02)

**etcd** — The key-value database where Kubernetes stores all cluster state, including Secrets. Managed services run it for you; whoever can read it can read everything. (Module 06)

**Execution role (AWS Lambda)** — The IAM role a Lambda function runs as; it decides what AWS APIs the function's code can call. Google analog: the Cloud Run service account; Azure: a managed identity. (Module 07)

**FinOps** — The practice of making engineering, finance, and leadership jointly accountable for cloud spend. The FinOps Foundation describes three repeating phases: Inform, Optimize, Operate. (Module 04)

**Flex Consumption plan (Azure Functions)** — Microsoft's recommended serverless hosting plan for new Azure Functions apps: event-driven scaling (including to zero), pay per execution, and VNet integration. Replaces the legacy Consumption plan. (Module 07)

**Folder (Google Cloud)** — A grouping node between the organization and projects, nestable up to 10 levels. IAM and organization policies set on a folder apply to everything under it. (Module 03)

**Free trial vs free tier** — A free trial is time-limited credit you can spend broadly (Google $300/90 days; AWS up to $200 on a 6-month free plan; Azure $200/30 days, as of 2026). A free tier is specific services with monthly limits that stay free. (Module 00)

**Function URL (AWS Lambda)** — A dedicated HTTPS endpoint for a Lambda function. Auth type `AWS_IAM` requires signed, IAM-authorized requests; `NONE` is public but still needs a resource-based policy. (Module 07)

**GKE Autopilot** — GKE mode where Google manages nodes, scaling, and hardened defaults, and general-purpose pods are billed by their resource requests. Google recommends it for most workloads; the alternative is Standard mode with self-managed node pools. (Module 06)

**Golden image** — A hardened, patched custom VM image used as the standard base for a fleet. Software supply chain: whatever is baked in ships to every VM (ATT&CK T1525 targets this). (Module 05)

**Hardware root of trust** — A chip that verifies a server's firmware before the main CPU runs anything, so tampered hardware won't boot. Google: Titan (and Caliptra); AWS: Nitro Controller + Nitro Security Chip; Azure: Cerberus. (Module 01)

**Hypervisor** — Software that runs multiple isolated virtual machines on one physical server. Type 1 runs on bare metal (KVM, Hyper-V, Nitro Hypervisor); Type 2 runs as an app on a normal OS. (Module 01)

**IaaS / PaaS / SaaS** — How much of the stack the provider runs for you. IaaS: they run hardware and virtualization; you run the OS up. PaaS: they also run the OS and runtime; you bring code and data. SaaS: they run the whole application; you manage users and data. (Module 01)

**IAM Identity Center (AWS)** — AWS's service for human sign-in to AWS accounts and apps, using permission sets instead of long-lived IAM users. Its organization instance runs in an AWS Organizations management account — and joining Organizations automatically moves a free-plan account to the paid plan. (Module 00)

**IAP TCP forwarding (Google Cloud)** — Identity-Aware Proxy feature that tunnels SSH/RDP to VMs without public IPs after checking the caller's Google identity and IAM role. The VM's firewall only needs to allow IAP's range (35.235.240.0/20). (Modules 01, 05)

**IMDSv2 (AWS)** — Version 2 of the EC2 Instance Metadata Service, which requires a session token before returning data (including role credentials). Blocks simple SSRF-based credential theft; default on Amazon Linux 2023. (Module 05)

**Ingress setting (Cloud Run)** — Network-level control over where requests may come from: `all`, `internal` (VPC and certain Google sources), or `internal-and-cloud-load-balancing`. Layers with, and doesn't replace, IAM invoker checks. (Module 07)

**Instance template (Google Cloud)** — A reusable blueprint (machine type, image, disk, network, identity, labels) for creating VMs, especially in managed instance groups. AWS: launch template; Azure: scale set model. (Module 05)

**Invoker IAM check (Cloud Run)** — Cloud Run's default requirement that callers present a Google-signed ID token for an identity holding `run.routes.invoke` (e.g., `roles/run.invoker`). Disabling it, or granting `allUsers`, makes a service public. (Module 07)

**kubelet** — The Kubernetes agent on every node that starts containers and reports status. An exposed kubelet API with anonymous access is a well-known initial-access path (e.g., Hildegard malware). (Module 06)

**Kubernetes control plane** — The API server, etcd, scheduler, and controller managers that store desired state and reconcile the cluster toward it. Managed by the provider on GKE, EKS, and AKS. (Module 06)

**Label (Google Cloud)** — A key-value pair on a resource (up to 64 per resource, lowercase) that flows into billing reports and the BigQuery billing export, used for cost allocation. Not usable in policy conditions — Google's separate "tags" feature is for that. (Module 04)

**Least privilege** — Give each identity only the permissions it needs, for only as long as it needs them. The cloud version of need-to-know.

**Machine type / instance type / VM size** — The vCPU and memory shape of a VM. Google machine types (e.g., `e2-micro`), AWS instance types (`t3.micro`), Azure sizes (`Standard_B1s`). Shared-core/burstable types are what free tiers offer. (Module 05)

**Managed instance group (MIG, Google Cloud)** — A group of identical VMs created from an instance template that Google keeps at a target size, autoheals, updates in rolling fashion, and autoscales. A regional MIG spreads VMs across zones. AWS: Auto Scaling group; Azure: Virtual Machine Scale Set. (Module 05)

**Management group (Azure)** — A container above subscriptions for applying Azure RBAC and Azure Policy at scale; up to six levels deep under the tenant root group. (Module 03)

**Metadata server / IMDS** — A link-local endpoint (169.254.169.254) inside every cloud VM that serves configuration and the VM identity's short-lived credentials. A prime target for SSRF and credential theft (ATT&CK T1552.005). (Module 05)

**Multi-tenancy** — Many customers' workloads sharing the same physical infrastructure, kept apart by the hypervisor and hardware. NIST calls it resource pooling. (Module 01)

**Namespace (Kubernetes)** — A named scope inside a cluster for objects, RBAC permissions, quotas, and Pod Security labels. Roughly a Compose project; not a hard security boundary by itself. (Module 06)

**NetworkPolicy (Kubernetes)** — A label-based rule restricting which pods can talk to which. Pods are allow-all by default; a policy only works if the CNI enforces it. (Module 06)

**NIST SP 800-145** — The U.S. government's definition of cloud computing: five essential characteristics (on-demand self-service, broad network access, resource pooling, rapid elasticity, measured service), three service models, four deployment models. Citing it signals fluency with government customers. (Module 01)

**Nitro System (AWS)** — AWS's virtualization platform: Nitro Cards (networking, storage, management offload), the Nitro Security Chip, and the minimal Nitro Hypervisor. (Module 01)

**Offload card / processor** — Dedicated hardware that handles networking, storage, encryption, and management off the host CPU, keeping provider control software out of tenant reach. Google Titanium Offload Processors, AWS Nitro Cards, Azure Boost. (Module 01)

**Organization (Google Cloud)** — The root of a Google Cloud resource hierarchy, normally tied to a Cloud Identity or Workspace domain; new Free Trial sign-ups may get a domainless standalone organization. (Module 03)

**Organization Policy (Google Cloud)** — Google's guardrail service: constraints on what can be configured (e.g., allowed resource locations), set on an org, folder, or project and inherited. IAM is "who"; org policy is "what." (Module 03)

**Organizational unit (OU, AWS)** — A grouping of AWS accounts within AWS Organizations, nestable up to five levels under the root; policies attached to an OU apply to accounts inside it. (Module 03)

**OS Login (Google Cloud)** — Ties Linux accounts on Compute Engine VMs to Google identities and IAM roles (`roles/compute.osLogin`, `roles/compute.osAdminLogin`) instead of static SSH keys in metadata, so access is revoked centrally. Enabled with metadata `enable-oslogin=TRUE`. (Module 05)

**Permission set (AWS)** — A reusable bundle of permissions in IAM Identity Center that you assign to a user or group for a specific AWS account. (Module 00)

**Phishing-resistant MFA** — A second factor cryptographically bound to the real website (passkeys, FIDO2 security keys), so a fake login page can't capture and replay it. SMS codes and push approvals are not phishing-resistant. (Module 00)

**Pod** — The smallest unit Kubernetes schedules: one or more containers sharing a network namespace and volumes. (Module 06)

**Pod Security Admission** — Kubernetes' built-in admission controller (stable since v1.25) that enforces the Pod Security Standards — `privileged`, `baseline`, `restricted` — per namespace via labels, in `enforce`, `audit`, or `warn` mode. (Module 06)

**Programmatic budget notification (Google Cloud)** — Budget status that Cloud Billing publishes to a Pub/Sub topic several times a day, so code can react to spend. The building block for any automated cost response on Google Cloud. (Module 04)

**Quota** — A provider-enforced cap on how much of a resource a project/account/subscription can use (e.g., vCPUs per region). Distinct from a budget, which only measures spend. Also limits an attacker's blast radius. Google calls fixed caps "system limits." (Module 04)

**RBAC (Kubernetes)** — Kubernetes' authorization model: Roles/ClusterRoles list allowed verbs on resources; RoleBindings/ClusterRoleBindings grant them to users, groups, or ServiceAccounts. Separate from, and layered under, cloud IAM. (Module 06)

**Region / zone** — A region is a geographic area containing several isolated data-center groups called zones (AWS: Availability Zones). Spreading across zones protects against a single facility failing; spreading across regions protects against a regional outage. (Module 02)

**Region pair (Azure)** — Microsoft's pairing of two regions in the same geography for recovery prioritization and staggered updates. Not a DR plan by itself; newer regions are often nonpaired. (Module 02)

**Resource control policy (RCP, AWS)** — An AWS Organizations policy type that caps what can be done to resources in member accounts, complementing SCPs, which cap what principals can do. (Module 03)

**Resource group (Azure)** — A container inside a subscription for resources that share a lifecycle. Each resource belongs to exactly one; deleting the group deletes its contents. (Module 03)

**Resource scope (zonal / regional / multi-regional / global)** — Where a resource lives and therefore what failure takes it down. On Google Cloud the API path shows it: `/zones/`, `/regions/`, or `/global/`. (Module 02)

**Root user (AWS)** — The identity created with an AWS account, with unrestricted access including billing and account closure. AWS requires MFA on it; best practice is no access keys and rare use. Google Cloud has no direct equivalent. (Module 00)

**RPO (Recovery Point Objective)** — The maximum acceptable amount of data loss, measured in time ("we can lose at most 15 minutes of work"). (Module 02)

**RTO (Recovery Time Objective)** — The maximum acceptable time a system can be offline after an incident. (Module 02)

**Savings Plan (AWS)** — A one- or three-year commitment to a dollar-per-hour amount of usage in exchange for discounts; Compute Savings Plans apply across EC2 families, Regions, Fargate, and Lambda. (Module 04)

**Scale to zero** — A serverless platform running no instances, and charging no compute on request-based billing, when there's no traffic. (Module 07)

**Serverless** — A model where the provider runs, scales, and patches the infrastructure for code or containers you supply, typically scaling to zero and billing per use. Security shifts to invocation permissions and the workload's identity. (Module 07)

**Service (Kubernetes)** — A stable virtual IP and DNS name in front of a changing set of pods, selected by labels. Type `LoadBalancer` creates a cloud load balancer — a public endpoint and a bill. (Module 06)

**Service control policy (SCP, AWS)** — An AWS Organizations guardrail that sets the maximum permissions available to principals in member accounts. Doesn't grant anything and doesn't apply to the management account. (Module 03)

**ServiceAccount (Kubernetes)** — An identity for workloads inside a cluster. With workload identity (GKE Workload Identity Federation, EKS Pod Identity, Entra Workload ID) it can be exchanged for short-lived cloud credentials. (Module 06)

**Session Manager (AWS Systems Manager)** — Browser or CLI shell access to instances through an agent that connects outbound to AWS, so instances need no inbound ports, bastion hosts, or SSH keys; access is controlled by IAM and sessions can be logged. (Module 05)

**Shared fate** — Google Cloud's framing that the provider should actively help customers secure their workloads (secure defaults, blueprints, guidance), on top of the shared responsibility split. Doesn't move the line: customers still configure identity and access. (Module 01)

**Shared responsibility model** — The provider secures the cloud itself (facilities, hardware, hypervisor); the customer secures what they put in it. Identity, access control, firewall rules, network configuration, and data are always the customer's job. (Module 01)

**Shielded VM / Trusted Launch** — Boot-integrity protections for VMs: Secure Boot (signed boot components only), a virtual TPM, and integrity monitoring. Google calls it Shielded VM; Azure calls it Trusted Launch. (Modules 01, 05)

**Showback / chargeback** — Showback reports each team's share of cloud cost to them; chargeback actually bills their budget for it. Both depend on consistent labels/tags. (Module 04)

**SKU (billing)** — The individual priced item a provider meters, such as a vCPU-hour of a machine family in a region. One resource usually generates several SKUs. (Module 04)

**SLA (Service Level Agreement)** — A provider's contractual uptime commitment; if missed, you can claim a service credit. A refund policy, not an availability guarantee. (Module 02)

**Spot capacity** — Spare provider capacity sold at a deep discount that the provider can reclaim on short notice: Google Spot VMs, AWS Spot Instances, Azure Spot VMs. Good for fault-tolerant batch work; bad for anything that must stay up. (Module 04)

**Standalone organization (Google Cloud)** — A Google Cloud organization created automatically, without a domain, for new Free Trial customers when they accept the console terms. Not available to existing accounts. (Module 03)

**Sustained use discount (Google Cloud)** — An automatic discount on eligible Compute Engine machine series that grows as a resource runs more of the month (after 25%), up to 30% net for a full month. No equivalent on AWS or Azure. (Module 04)

**Titanium (Google Cloud)** — Google's hardware security architecture: Titan root-of-trust chips, Caliptra, Titanium Offload Processors, and related components that verify boot integrity and offload I/O and encryption. (Module 01)

**VM escape** — Code inside a virtual machine breaking out to the hypervisor or host. Rare in public reporting and the provider's responsibility to prevent; container escape (ATT&CK T1611) is the customer-side analog. (Module 01)

**VPC (Virtual Private Cloud)** — A private, software-defined network inside a cloud provider, where you define IP ranges, subnets, routes, and firewall rules. Closest homelab analogy: your OPNsense-managed VLANs — but defined entirely by API. (Module 10)

**Workload identity** — Giving a workload (pod, function, VM) short-lived cloud credentials based on its own identity instead of a stored key. In Kubernetes: GKE Workload Identity Federation, EKS Pod Identity/IRSA, Microsoft Entra Workload ID. (Module 06; deep dive in 15)
