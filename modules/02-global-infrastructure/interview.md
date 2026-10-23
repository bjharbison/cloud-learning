# 02 Interview Prep — Global infrastructure

## Likely questions

### Q1. "A customer asks: what happens if one of your data centers goes down?"

**Answer outline:**
- Clarify scope first: one zone, one region, or the provider's control plane?
- Zone loss: a multi-zone (regional) design keeps running; a single-VM design doesn't. That's the customer's architecture choice.
- Region loss: needs a multi-region design sized to RTO/RPO.
- Back it with SLA numbers *and* the caveat that SLAs are credits, not guarantees.

**Strong signal:** turning it around into a discovery question — "What's your RTO and RPO for this mission?"
**Avoid:** "Google never goes down."

### Q2. "Explain RTO and RPO to a program manager."

**Answer outline:**
- RTO: how long until we're back. RPO: how much recent work we might redo.
- Cold/warm/hot as a cost-vs-speed dial.
- Tie to their COOP plan — they already think this way.

### Q3. "How is Google Cloud's global network different from AWS or Azure?"

**Answer outline:**
- Google VPC is a global resource; subnets are regional; inter-region traffic stays on Google's backbone with internal IPs.
- AWS VPCs / Azure VNets are regional; multi-region needs peering or transit hubs.
- Benefit: simpler multi-region design. Consideration: a single network's blast radius → segment with projects, firewall policy, and Shared VPC (modules 10–11).

**Strong signal:** naming both the benefit and the governance consideration.

### Q4. "How do you read a cloud SLA? What would you warn a customer about?"

**Answer outline:**
- What's covered, under what deployment (multi-zone vs single instance).
- Uptime formula, downtime definition, exclusions, claim deadline.
- Remedy is a percentage credit on that service's bill.
- Composite availability: chained dependencies multiply down; redundancy multiplies up.

**Strong signal:** quoting a real number correctly (e.g., Compute Engine ≥ 99.99% multi-zone, ≥ 99.9% single instance) with "as of my last check."

### Q5. "How do government customers handle region choice?"

**Answer outline:**
- Data residency and authorization scope drive it.
- AWS GovCloud and Azure Government: separate environments. Google: Assured Workloads controls on commercial regions; GDC for disconnected.
- Preview-level answer; offer to go deeper on FedRAMP/IL specifics after verifying current authorizations (module 26).

**Avoid:** quoting impact levels or authorizations from memory.

## 60-second executive explanation

"Cloud providers build in layers. A zone is one data center campus; a region is a cluster of zones in the same metro; and the provider links regions with its own private network. If we run in one zone, a power or cooling failure there takes us down. If we spread across zones, we survive that, usually for little extra cost. Surviving the loss of a whole region costs more, because we're running a second copy far away. So the real question for you is: how long can this mission be offline, and how much data can we afford to lose? Those two answers — recovery time and recovery point — tell us how much resilience to buy. The provider's uptime promise helps, but it's a refund policy, not a guarantee; the resilience comes from how we design it."

## Whiteboard prompt

Draw two regions with three zones each. Place a stateless web tier, a database, and object storage for a mission app that needs RTO 15 minutes / RPO 5 minutes. Label each component zonal/regional/global, and show what happens when zone A in region 1 fails, then when all of region 1 fails.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud global infrastructure — regions, zones, resource scope, RTO/RPO, and SLAs — across Google Cloud, AWS, and Azure, and can discuss resilience trade-offs."
- **After completing the lab:** "In a personal Google Cloud lab, I deployed resources at zonal, regional, and global scope, stopped one of two VMs in different zones to observe zone-scoped failure, and mapped AZ IDs and region pairs on AWS and Azure."
- **Still requires (cert / production experience / clearance):** designing and testing production DR, signing up to an RTO/RPO for a real system, and architecting in GovCloud, Azure Government, or Assured Workloads environments. Don't claim "designed highly available architectures" from this lab; the Professional Cloud Architect exam tests this at a claimable level.
