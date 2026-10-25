# 10 Interview Prep — Virtual networks

## Likely questions

### Q1. "How is Google Cloud's VPC different from AWS and Azure?"

**Answer outline:**
- Google VPC networks — with their routes and firewall rules — are global; subnets are regional. VMs in different regions talk over internal IPs on Google's backbone with no peering or VPN.
- AWS VPCs are regional with subnets per AZ; Azure VNets are regional with subnets spanning zones. Multi-region on either means multiple networks plus peering or a hub (Transit Gateway, Virtual WAN).
- Benefit: simpler multi-region routing and one place for policy. Trade-off: a bigger single network you must segment deliberately — subnets, firewall policy, Shared VPC per environment.

**Strong signal:** naming the trade-off, not just the feature.
**Avoid:** "Google's is better."

### Q2. "Walk me through how you'd plan IP addressing for a new agency cloud environment."

**Answer outline:**
- Inventory every range that might ever connect: on-prem, partner agencies, other clouds, VPN pools.
- Allocate a non-overlapping supernet; carve per environment and region; reserve space for GKE secondary ranges and future clouds.
- Custom-mode networks only; no default network (org policy).
- Expansion: Google subnets can grow in place but never shrink; AWS adds secondary CIDRs; Azure adds address spaces — plan headroom anyway.

**Strong signal:** "overlap is what kills hybrid connectivity later."

### Q3. "When would you use Shared VPC versus VPC Network Peering?"

**Answer outline:**
- Shared VPC: one organization, central network team, many app projects deploying into centrally owned subnets — consistent policy, least privilege (`networkUser` per subnet), billing per service project.
- Peering: connecting separately administered networks (another org, a partner, a vendor) — private, low-latency, but non-transitive, no overlap, firewalls not shared.
- Beyond a handful of networks or with on-prem in the mix: Network Connectivity Center as a hub.
- AWS analogs: VPC sharing via AWS RAM; peering; Transit Gateway. Azure: hub-and-spoke peering; Virtual WAN.

### Q4. "What's different about cloud networking compared with on-prem?"

**Answer outline:**
- Everything is API-defined and logged; no appliances to rack.
- No Layer 2: no broadcast/multicast, no VLAN tags; ARP and DHCP are provided by the platform.
- Routing and firewalling are distributed (Google's Andromeda), not funneled through a box — so "put a firewall in the middle" requires explicit routing to an appliance.
- Internet egress is explicit (external IP or NAT), and Azure is moving new VNets to private-by-default.

**Strong signal:** a concrete example — "VRRP doesn't work, so HA moves to a load balancer."

### Q5. "How would an attacker abuse cloud networking, and how would you see it?"

**Answer outline:**
- Add peerings, routes, or VPN tunnels to bridge into a network they control (T1599); open firewall paths (T1562.007); scan internally from a foothold (T1046).
- Telemetry: Admin Activity logs for network, route, and peering changes; VPC Flow Logs (opt-in, sampled); firewall rules logging.
- Prevention: restrict who holds network admin; org policies on external IPs and default networks; review peerings.

## 60-second executive explanation

"Before anything runs in the cloud, we draw its private network — the equivalent of the agency's internal network, but defined in software. We decide which address ranges belong to which programs and environments, and we plan them so they never collide with our data centers or partners, because collisions are what turn a simple connection into a months-long project later. On Google Cloud, one private network can span the whole country, so systems in different regions talk privately without extra tunnels. A central network team owns that network; mission teams plug into it but can't rewire it. Every change to it is logged, which lets us see — and alert on — anyone trying to connect it somewhere it shouldn't go."

## Whiteboard prompt

Draw an agency's Google Cloud network: an org with a `Network` folder holding `net-host-prod` and `net-host-nonprod` Shared VPC host projects. In prod, a global VPC with subnets in `us-east4` and `us-central1` (write the CIDRs), service projects for two programs attached with subnet-level `networkUser`, a Cloud Router to on-prem (`172.16.0.0/12`), and a peering to a partner. Then show why the partner can't reach on-prem through you, and what you'd need if the business wanted it to.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud virtual networking on Google Cloud, AWS, and Azure — VPC/VNet scope, subnets and CIDR planning, routing, Shared VPC, peering, and hub-and-spoke designs — and how they differ from on-prem networking."
- **After completing the lab:** "In a personal lab I designed a non-overlapping address plan, built custom-mode Google Cloud VPC networks spanning two regions, verified cross-region internal connectivity, configured VPC Network Peering and demonstrated it is non-transitive using route tables, and expanded a subnet in place." Add the AWS and Azure sentences only if you did those parts. Your homelab VLAN/OPNsense work is separately claimable as homelab experience — keep the two distinct.
- **Still requires (cert / production experience / clearance):** designing or operating production cloud networks, Shared VPC at organizational scale, hybrid connectivity to agency networks, or TIC-compliant architectures. Don't claim "cloud network engineer." The Associate Cloud Engineer and, later, the Professional Cloud Network Engineer exam (⚠️ not checked this run) are claimable milestones.
