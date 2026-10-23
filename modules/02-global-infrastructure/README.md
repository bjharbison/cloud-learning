# 02 — Global infrastructure: regions, zones, availability, SLAs, resilience patterns

> **In one sentence:** you'll be able to choose where a workload runs, explain what failure it survives, and read a provider's SLA without being misled by the nines.

**Prereqs:** modules 00–01 · **Time:** ~3 hours incl. lab · **Phase:** 1

## Learning objectives

- Define region, zone, and edge location on each cloud, and say what failure each protects against.
- Classify resources as **zonal, regional, multi-regional, or global**, with examples.
- Use **RTO** and **RPO** to match a resilience pattern to a mission requirement.
- Read an SLA: what's covered, how uptime is calculated, what you get when it's missed (hint: credits, not uptime).
- Preview government and sovereign regions — enough to know what to ask, not yet how to architect.

## Why this matters for the target roles

- **Customer engineer:** "What happens if a data center goes down?" is in every discovery call. Your answer shapes cost and architecture.
- **Cloud security:** location is a control. Data residency, region restrictions, and unused-region monitoring are security decisions.
- **CTI:** adversaries hide resources in regions nobody watches (ATT&CK T1535). Knowing the geography is knowing the terrain.

---

## Concepts

### Region, zone, edge

**Plain version:** a **region** is a metro area with several separate data-center sites. A **zone** is one of those sites. **Edge locations** are smaller sites closer to users, used mostly for caching, DNS, and traffic entry.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Region | Independent geographic area made of zones | Separate geographic area, isolated from other Regions | One or more data centers on a low-latency network; Azure has **70+ regions** |
| Zone | A single failure domain in a region. A region has **three or more zones in three or more physical data centers** (a few regions are still expanding to three) | **Availability Zone (AZ):** one or more discrete data centers with redundant power and networking, in separate facilities, linked by dedicated metro fiber | **Availability zone:** AZ-enabled regions have **at least three** zones |
| Zone naming | `us-central1-a` | `us-east-1a` (name) and `use1-az1` (**AZ ID**) | Zones 1, 2, 3 (logical numbers per subscription) |
| Closer-to-user options | Network edge and CDN points of presence (module 12) | **Local Zones** (compute near metro areas), **Wavelength Zones** (inside 5G carrier networks), CloudFront edge locations | Edge points of presence for Front Door/CDN (module 12) |
| Extra grouping | Multi-regions (e.g., `US`) for some services | — | **Geographies** (data-residency boundaries) and **region pairs** |

**Bridge:** your homelab is one zone. A second Proxmox node in the same rack is redundancy *within* a zone. A node at a friend's house across town is a second zone. A node in another state is a second region.

### A subtle AWS detail: AZ names vs AZ IDs

In some older AWS Regions, `us-east-1a` in *your* account might be a different physical facility than `us-east-1a` in someone else's. AWS did this to spread load. The **AZ ID** (e.g., `use1-az1`) is the same physical location in every account. AWS says accounts created from November 2025 get a uniform mapping. **Why it matters:** when two accounts (yours and a partner's, or prod and DR) must be in the *same* or *different* facilities, compare AZ IDs, not names.

### Azure detail: region pairs

Microsoft pairs many regions (e.g., East US ↔ West US) inside the same geography. Pairing gives a prioritized recovery order in a broad outage, staggered platform updates, and data residency within the geography. Microsoft also states plainly that a pair **doesn't automatically make your app more resilient** — you still design your own DR. Newer regions are often **nonpaired** and rely on availability zones.

### Zonal, regional, multi-regional, global

Every resource has a **scope** — where it lives and what failure takes it down.

| Scope | Survives | Google Cloud examples | AWS examples | Azure examples |
|---|---|---|---|---|
| **Zonal** | Nothing beyond its zone | A Compute Engine VM, a zonal persistent disk | An EC2 instance, an EBS volume | A VM pinned to a zone, a zonal managed disk |
| **Regional** | Loss of one zone | Regional managed instance groups, App Engine apps | Most managed services spread across AZs (e.g., S3 storage within a Region) | Zone-redundant services within a region |
| **Multi-regional** | Loss of a region (within the multi-region) | Cloud Storage multi-region buckets, BigQuery, Spanner, Cloud KMS | Services you replicate yourself across Regions | Geo-redundant storage options |
| **Global** | Region loss; one config everywhere | IAM policies, **VPC networks**, global firewall rules, global load balancers | IAM, Route 53, CloudFront | Microsoft Entra ID, Front Door |

### Preview: Google's global VPC

Here's a real architectural difference you'll hit in module 10:

- **Google Cloud:** a VPC network is **global**. One network can have subnets in many regions, and VMs in different regions talk over Google's backbone with internal IPs, no extra peering.
- **AWS and Azure:** a VPC / VNet is **regional**. Multi-region designs need peering or transit gateways/hubs between them.

**Bridge:** imagine one OPNsense instance whose VLANs can span every site you own, versus a separate firewall per site joined by VPN tunnels. That's Google vs AWS/Azure networking.

### RTO and RPO

- **RTO (Recovery Time Objective):** the longest the application can be offline. "How fast must we be back?"
- **RPO (Recovery Point Objective):** the longest period of data you can afford to lose. "How much can we redo?"

Google's DR guide describes three broad patterns (by how ready the standby is):

| Pattern | Standby state | RTO | Cost |
|---|---|---|---|
| **Cold** | Nothing running; rebuild from backups | Hours to days | Lowest |
| **Warm** | Scaled-down copy ready, needs promotion | Minutes to hours | Medium |
| **Hot** | Full copy serving traffic (active-active) | Near zero | Highest |

**Bridge to your mission background:** this is COOP. RTO is how long until the alternate site is operational; RPO is how stale the picture is when it comes up. A cold site is a dark room with a backup tape; a hot site is a second watch floor already manning the feed.

### Reading an SLA

An **SLA (Service Level Agreement)** is a contract promise: "if monthly uptime drops below X, you get a credit." Things to look for:

1. **What's covered and how it's deployed.** The number depends on *your* architecture.
2. **How uptime is measured.** Usually minutes in the month minus downtime minutes. Short blips may not count.
3. **What you get.** A percentage of that service's bill back as **credit**, after you **file a claim** within a deadline.
4. **Exclusions.** Pre-GA features, your own misconfiguration, things outside the provider's control.

Compute SLAs side by side (check current versions before quoting):

| | Google Compute Engine | Amazon EC2 | Azure VMs |
|---|---|---|---|
| Spread across zones | **≥ 99.99%** (instances in multiple zones, Premium Tier) | **99.99%** Region-level (instances in 2+ AZs) | 99.99% for VMs across two or more zones ⚠️ unverified against current official SLA text |
| Single instance | **≥ 99.9%** (most families; 99.95% memory-optimized) | **99.5%** instance-level | Varies by disk type ⚠️ unverified |
| Credit if missed (top tier) | 10% → 25% → 100% as uptime falls | 10% → 30% → 100% | See official SLA |
| Claim deadline | 60 days | End of the second billing cycle after the incident | See official SLA |

**What the nines mean in a 30-day-ish month:**

| SLA | Allowed downtime / month | / year |
|---|---|---|
| 99.5% | ~3.7 hours | ~44 hours |
| 99.9% | ~44 minutes | ~8.8 hours |
| 99.95% | ~22 minutes | ~4.4 hours |
| 99.99% | ~4.4 minutes | ~53 minutes |

**Two traps:**

- **An SLA is a refund policy, not an availability guarantee.** A 10% credit on a $50 VM doesn't cover a missed mission.
- **Chained services multiply.** An app needing a 99.95% service *and* a 99.99% service is at best ~99.94% — lower than either. Redundancy is what pushes the number up.

---

## Text diagram

```
                        GLOBAL (IAM, Google VPC network, global LB, Entra ID)
   ┌───────────────────────────────────────────────────────────────────────────┐
   │   REGION us-central1                         REGION us-east4              │
   │  ┌──────────┬──────────┬──────────┐         ┌──────────┬──────────┐ ...   │
   │  │ zone -a  │ zone -b  │ zone -c  │         │ zone -a  │ zone -b  │       │
   │  │  VM ■    │  VM ■    │          │         │  VM ■    │          │       │
   │  │  disk ▭  │  disk ▭  │          │         │          │          │       │
   │  └──────────┴──────────┴──────────┘         └──────────┴──────────┘       │
   │   ◄── regional resource spans zones ──►        ▲                          │
   │                 └────── private backbone ──────┘  (multi-region / DR)     │
   └───────────────────────────────────────────────────────────────────────────┘
             ▲ edge PoPs / CDN near users (module 12)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Zones per region | 3+ (in 3+ data centers) | Multiple AZs, each 1+ data centers | 3+ in AZ-enabled regions | Not every Azure region has zones; check before designing |
| Zone identity across accounts | Same name everywhere | Names may differ per account in older Regions; AZ IDs are consistent | Logical zone numbers per subscription | AWS AZ IDs are the cross-account truth |
| Network scope | **Global** VPC | Regional VPC | Regional VNet | Biggest design difference; module 10 |
| Metro/5G edge compute | — (CDN/edge PoPs) | Local Zones, Wavelength Zones | — (edge PoPs) | AWS has the most branded edge-compute options |
| Region pairing | No | No | Yes (many regions) | Azure pairs inform recovery order, not your DR design |
| Multi-zone compute SLA | ≥ 99.99% | 99.99% | 99.99% ⚠️ verify | Similar headline; read the conditions |
| Single-instance compute SLA | ≥ 99.9% | 99.5% | Varies ⚠️ verify | Google's single-VM promise is higher than AWS's |
| Government regions | Assured Workloads over US commercial regions | AWS GovCloud (US-East, US-West) | Azure Government (separate instance) | Google's model is controls on shared regions; AWS/Azure use separate environments |

## Administer and monitor it

- **List what exists:** `gcloud compute regions list` / `zones list`; `aws ec2 describe-regions` / `describe-availability-zones`; `az account list-locations`.
- **Restrict where things can be created** (module 20): Google org policy resource-location constraints, AWS SCPs using the requested-region condition, Azure Policy "Allowed locations."
- **Provider health:** Google Cloud Service Health, AWS Health Dashboard, Azure Service Health. Subscribe so outages reach you before customers do.
- **Watch every region, not just yours:** audit logging and threat detection should cover regions you don't use (module 18).

## Security angle

- **Location is a control.** Data-residency rules (and some contracts) dictate where data may sit. Enforce with policy, not memory.
- **Unused regions are blind spots.** If you only monitor `us-east-1`, an attacker in `ap-southeast-2` is invisible.
- **Single-zone designs are availability risks** — and availability is the "A" in CIA.
- **Shared responsibility:** the provider runs zones and regions and publishes SLAs. **Choosing** a multi-zone design, configuring replication, testing failover, and restricting regions are the **customer's** job.

## Threat intel angle

- **T1535 Unused/Unsupported Cloud Regions** — adversaries launch resources (often crypto-miners) in regions the victim never uses, betting no one is looking. Detection: alert on any API activity in non-approved regions; better, block them with policy.
- **Outage-themed phishing** — real provider outages generate lures ("action required: migrate your workloads"). Track provider status pages so you can recognize fakes.
- **Physical-layer reporting** — subsea cable cuts and regional power events show up in open-source reporting; resilience analysis for a mission customer can draw on it.

## Public sector notes (preview — modules 26–27 go deep)

- **AWS GovCloud (US):** isolated AWS Regions (US-West and US-East) for sensitive government workloads. AWS states they're administered by U.S. citizens, support FedRAMP High and DoD IL4/IL5, and help with ITAR/EAR obligations.
- **Azure Government:** a physically isolated instance of Azure for eligible government customers. Note: Microsoft's mandatory-MFA enforcement (module 00) currently applies to public Azure only.
- **Google Cloud Assured Workloads:** applies control packages (data residency, personnel access, service restrictions) to folders in Google's commercial infrastructure. US packages include FedRAMP Moderate/High, IL2/IL4/IL5, CJIS, ITAR, and IRS 1075; several were renamed in 2025 (e.g., "Data Boundary for ITAR").
- **Sovereign clouds:** Azure notes some regions belong to sovereign geographies with limited services. Expect this vocabulary in international and allied conversations.

**The interview-ready point:** AWS and Azure answer "government" mainly with separate environments; Google answers mainly with policy-enforced boundaries on its commercial regions (plus Google Distributed Cloud for disconnected needs, module 28). Each approach has trade-offs in feature parity, cost, and authorization scope.

## Key takeaways

- Region = metro with several sites; zone = one site and one failure domain; edge = small sites near users.
- Every resource is zonal, regional, multi-regional, or global. Know which, and you know what failure takes it down.
- Google's VPC is global; AWS VPCs and Azure VNets are regional.
- RTO = how long down; RPO = how much data lost. Cold/warm/hot trade cost for recovery speed.
- SLAs are refund policies. Read the conditions; multiply chained SLAs; design redundancy for the real target.
- Monitor and restrict **all** regions — ATT&CK T1535 lives in the ones you ignore.
- Government: GovCloud and Azure Government are separate environments; Google uses Assured Workloads on commercial regions.

## Sources

- [Google Cloud — Geography and regions](https://docs.cloud.google.com/docs/geography-and-regions)
- [Google Cloud — Compute Engine SLA](https://cloud.google.com/compute/sla)
- [Google Cloud — Disaster recovery planning guide](https://docs.cloud.google.com/architecture/dr-scenarios-planning-guide)
- [Google Cloud — Assured Workloads overview](https://docs.cloud.google.com/assured-workloads/docs/overview)
- [AWS — Regions and Availability Zones](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions-availability-zones.html)
- [AWS — AZ IDs](https://docs.aws.amazon.com/global-infrastructure/latest/regions/az-ids.html)
- [AWS — EC2 Regions and Zones (naming, Local and Wavelength Zones)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- [AWS — Amazon Compute SLA](https://aws.amazon.com/compute/sla/)
- [AWS — What is AWS GovCloud (US)?](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/whatis.html)
- [Microsoft — Azure regions overview](https://learn.microsoft.com/en-us/azure/reliability/regions-overview)
- [Microsoft — Azure region pairs and nonpaired regions](https://learn.microsoft.com/en-us/azure/reliability/regions-paired)
- [Microsoft — Azure Government documentation](https://learn.microsoft.com/en-us/azure/azure-government/)
- [Microsoft Q&A — SLA for Virtual Machines (Microsoft staff answer, 2022; secondary source)](https://learn.microsoft.com/en-us/answers/questions/1114758/sla-for-virtual-machines)
- [MITRE ATT&CK — T1535 Unused/Unsupported Cloud Regions](https://attack.mitre.org/techniques/T1535/)

Verified: 2026-10-23
