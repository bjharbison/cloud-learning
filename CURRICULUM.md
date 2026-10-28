# Curriculum

**Scope:** set up, use, administer, monitor, and secure Google Cloud, AWS, and Azure — novice → intermediate.
**Lens:** cyber threat intelligence, cloud security, and solutions architecture (public sector / national security emphasis). Not full sysadmin depth.

Every module teaches all three clouds side by side. Google Cloud leads each comparison (primary career target), then AWS, then Azure.

## Build status

The automated builder updates the **Build** column; I update [`PROGRESS.md`](PROGRESS.md) as I learn.

| Marker | Meaning |
|---|---|
| ⬜ | Not built yet |
| 🟦 | Drafted — content written, not yet through the weekly review |
| ✅ | Reviewed — facts re-checked against official docs |

Modules are built in numbered order, in batches of four or five by scheduled runs. Each batch gets an independent review pass before it's done.

---

## Phase 0 — Setup

| # | Module | Folder | Build |
|---|---|---|---|
| 00 | Lab environment: free-tier accounts, MFA, budget alerts, CLIs, cloud shells | `modules/00-lab-setup` | 🟦 |

**00** — Create personal accounts on all three clouds; lock down the root/owner identity with MFA; create a non-root admin; set budget alerts; install `gcloud`, `aws`, and `az`; use each cloud shell. Outcome: three safe sandboxes I can't accidentally run up a bill in.

## Phase 1 — Cloud foundations (novice)

| # | Module | Folder | Build |
|---|---|---|---|
| 01 | What the cloud is: NIST 800-145, virtualization, IaaS/PaaS/SaaS, shared responsibility | `modules/01-cloud-fundamentals` | 🟦 |
| 02 | Global infrastructure: regions, zones, availability, SLAs, resilience patterns | `modules/02-global-infrastructure` | 🟦 |
| 03 | Organizing resources: GCP org/folders/projects, AWS Organizations/accounts, Azure tenants/management groups/subscriptions | `modules/03-resource-hierarchy` | 🟦 |
| 04 | Billing, quotas, and cost governance (FinOps basics) | `modules/04-billing-and-cost` | 🟦 |

**01** — NIST's five essential characteristics, what a hyperscaler data center is, hypervisors vs containers, service models as a "sliding line" of responsibility. Heavy emphasis: identity, firewall rules, VPNs, and access control are always the customer's job.
**02** — Region vs zone vs edge location; zonal/regional/multi-regional services; RTO/RPO; reading an SLA; sovereign and government regions as a preview.
**03** — The hierarchy is also the security boundary and the policy inheritance tree. Compare the three models and where policy attaches.
**04** — How cloud billing works, budgets and alerts, labels/tags for chargeback, quotas, and why unpredictable spend collides with government appropriations.

## Phase 2 — Core services

| # | Module | Folder | Build |
|---|---|---|---|
| 05 | Compute: virtual machines, images, instance groups, autoscaling | `modules/05-compute` | 🟦 |
| 06 | Containers and Kubernetes: GKE, EKS, AKS | `modules/06-containers-kubernetes` | 🟦 |
| 07 | Serverless: Cloud Run / Cloud Run functions, Lambda, Azure Functions & Container Apps | `modules/07-serverless` | 🟦 |
| 08 | Storage: object, block, file; lifecycle, versioning, data protection | `modules/08-storage` | 🟦 |
| 09 | Databases and analytics: managed SQL/NoSQL, data warehouses (BigQuery, Redshift, Azure equivalents) | `modules/09-databases-analytics` | 🟦 |

## Phase 3 — Networking

| # | Module | Folder | Build |
|---|---|---|---|
| 10 | Virtual networks: VPC/VNet, subnets, CIDR, routes, how cloud SDN differs from on-prem | `modules/10-virtual-networks` | 🟦 |
| 11 | Network security controls: firewall rules, security groups, NACLs, NSGs, private access/endpoints | `modules/11-network-security` | 🟦 |
| 12 | Load balancing, DNS, CDN, WAF, and DDoS protection | `modules/12-load-balancing-edge` | 🟦 |
| 13 | Hybrid and multi-cloud connectivity: VPN, Interconnect/Direct Connect/ExpressRoute, hub-and-spoke | `modules/13-hybrid-connectivity` | 🟦 |

## Phase 4 — Identity and data protection

| # | Module | Folder | Build |
|---|---|---|---|
| 14 | IAM fundamentals: principals, roles, policies, least privilege across all three clouds | `modules/14-iam-fundamentals` | 🟦 |
| 15 | Federation, SSO, workload identity, Microsoft Entra ID, privileged access | `modules/15-identity-federation` | 🟦 |
| 16 | Encryption and key management: KMS, customer-managed keys, HSMs, secrets managers | `modules/16-encryption-kms` | 🟦 |
| 17 | Zero trust: BeyondCorp, identity-aware access, federal zero-trust strategy | `modules/17-zero-trust` | 🟦 |

## Phase 5 — Administration, monitoring, and governance

| # | Module | Folder | Build |
|---|---|---|---|
| 18 | Logging and audit trails: Cloud Audit Logs, CloudTrail, Azure Activity/Entra logs; centralizing logs | `modules/18-logging-audit` | 🟦 |
| 19 | Monitoring and observability: metrics, alerting, dashboards, SLOs (Cloud Monitoring, CloudWatch, Azure Monitor) | `modules/19-monitoring-observability` | 🟦 |
| 20 | Infrastructure as code and admin automation: Terraform, CLIs, policy as code (Org Policy, SCPs, Azure Policy) | `modules/20-iac-policy-as-code` | 🟦 |
| 21 | Security posture management: Security Command Center, Security Hub/GuardDuty, Defender for Cloud; CSPM/CNAPP; CIS benchmarks | `modules/21-security-posture` | 🟦 |

## Phase 6 — Detection, response, and threat intelligence

| # | Module | Folder | Build |
|---|---|---|---|
| 22 | Cloud detection engineering and SIEM: Google SecOps, Microsoft Sentinel, AWS options; MITRE ATT&CK cloud matrices | `modules/22-detection-siem` | 🟦 |
| 23 | Cloud incident response and forensics: evidence, containment, credential compromise playbooks | `modules/23-incident-response` | ⬜ |
| 24 | Cloud threat landscape for CTI: nation-state and criminal TTPs against cloud and identity; vendor threat intel sources | `modules/24-cloud-threat-landscape` | ⬜ |
| 25 | Attack-path lab (purple team): emulate cloud TTPs in my own account and detect them | `modules/25-attack-path-lab` | ⬜ |

## Phase 7 — Regulated and national-security cloud

| # | Module | Folder | Build |
|---|---|---|---|
| 26 | Compliance: FedRAMP, DoD Impact Levels (IL2–IL6), CMMC, NIST 800-53, ATO | `modules/26-compliance-ato` | ⬜ |
| 27 | Government clouds: Assured Workloads, AWS GovCloud and classified regions, Azure Government and classified clouds | `modules/27-government-clouds` | ⬜ |
| 28 | Air-gapped and disconnected cloud: Google Distributed Cloud air-gapped and peers; operating with no internet egress | `modules/28-air-gapped-cloud` | ⬜ |
| 29 | AI in the cloud and AI security: Vertex AI, Bedrock, Azure AI; RAG; OWASP LLM Top 10, MITRE ATLAS; AI in regulated boundaries | `modules/29-ai-and-ai-security` | ⬜ |

## Phase 8 — Architecture and career

| # | Module | Folder | Build |
|---|---|---|---|
| 30 | Well-architected design: the three architecture frameworks, landing zones, reference architectures | `modules/30-well-architected` | ⬜ |
| 31 | Migration: the "Rs," assessment, scoping, de-risking | `modules/31-migration` | ⬜ |
| 32 | Capstone + interview readiness: design and defend a secure architecture for a federal mission customer; whiteboard script; honest resume language | `modules/32-capstone-interview` | ⬜ |

---

## Certification checkpoints

Optional, but these are the claimable milestones. See [`reference/certifications.md`](reference/certifications.md).

| After phase | Reasonable exam to attempt |
|---|---|
| 2 | Google Cloud Digital Leader / AWS Cloud Practitioner / Azure AZ-900 (pick one or two) |
| 5 | Google Associate Cloud Engineer (primary target) |
| 6 | A security-focused cert on one cloud (e.g., Google Professional Cloud Security Engineer, AWS Security Specialty, Microsoft SC-200 or AZ-500) |
| 8 | Google Professional Cloud Architect |
