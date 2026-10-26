# 13 Interview Prep — Hybrid and multi-cloud connectivity

## Likely questions

### Q1. "How would you connect an agency's data center to Google Cloud?"

**Answer outline:**
- Discovery first: bandwidth, latency needs, data sensitivity, encryption policy, timeline, existing carriers/colos, CIDR overlap, TIC 3.0 posture.
- Fast start: HA VPN (two interfaces, BGP via Cloud Router, 99.99% SLA when configured correctly).
- Steady state: Dedicated or Partner Interconnect in a 99.99% topology (two metros, four connections for Dedicated); MACsec or HA VPN over Interconnect if traffic must be encrypted.
- Land it in a hub (Network Connectivity Center or the Shared VPC host project), with hierarchical firewall policy treating on-prem as its own zone.

**Strong signal:** asking about CIDR overlap and encryption requirements before naming a product.
**Avoid:** "Interconnect is private, so it's secure."

### Q2. "VPN or Interconnect — how do you decide?"

**Answer outline:**
- Bandwidth and predictability: VPN ~1–3 Gbps per tunnel over the internet; Interconnect up to many 100/400G circuits with stable latency.
- Time and cost: VPN in minutes at a low hourly rate; Interconnect needs a colo or partner and weeks of lead time, but egress pricing can be better at volume.
- Security: VPN is encrypted by design; Interconnect isn't by default.
- Often both: Interconnect primary, VPN backup.

### Q3. "How do the three clouds compare for hybrid connectivity?"

**Answer outline:**
- VPN: Google HA VPN; AWS Site-to-Site VPN (two tunnels per connection; 5 Gbps tunnels via Transit Gateway); Azure VPN Gateway AZ SKUs.
- Circuits: Dedicated/Partner Interconnect; Direct Connect (dedicated or hosted); ExpressRoute (provider or Direct).
- Hubs: NCC (global); Transit Gateway (regional) / Cloud WAN; Virtual WAN.
- Same truths everywhere: BGP, redundancy for SLAs, no default encryption on circuits.

### Q4. "What's TIC 3.0 and how does it affect a cloud architecture?"

**Answer outline:**
- CISA program; TIC 3.0 and OMB M-19-26 moved from forced routing through TIC access points to security capabilities applied by policy enforcement points near the data.
- Use cases: Traditional TIC, Branch Office, Remote User, Cloud.
- In design terms: be able to show which security capabilities (inspection, logging, identity) apply on each path — hybrid link, internet egress, remote users.

**Strong signal:** "TIC 3.0 is about capabilities and enforcement points, not a specific box."

### Q5. "What are the security risks of hybrid links?"

**Answer outline:**
- The on-prem VPN appliance as initial access (T1190/T1133; CISA ED 24-01 and ED 25-03).
- Route leaks/over-advertisement; flat trust between on-prem and cloud.
- Unencrypted circuits; weak IPsec settings.
- Detection: alerts on new tunnels/attachments, BGP changes, new peer IPs; flow logs on the hybrid subnets.

## 60-second executive explanation

"Our data center and the cloud need a reliable, private connection. We can start within days using encrypted tunnels over the internet — that's like a secure phone line over the public network. For the long term, we lease dedicated circuits straight into the provider's network, which give us steadier performance and more capacity. Those circuits aren't encrypted automatically, so we add encryption where our policies require it. We build two of everything so a single failure doesn't stop the mission, and we treat the link as a controlled border crossing: we decide what can cross, and we watch it. The provider runs its side; the configuration, the encryption choices, and our own equipment are our responsibility."

## Whiteboard prompt

Draw an agency DC connected to Google Cloud with two Dedicated Interconnects in two metros (99.99%), HA VPN over Interconnect for encryption, an HA VPN backup over the internet, Cloud Routers with private ASNs, and a Network Connectivity Center hub (star topology) with prod Shared VPC as center and nonprod/partner as edges. Mark where TIC 3.0 policy enforcement points sit and where logs come from. Then redraw it for AWS (Direct Connect gateway → Transit Gateway) and Azure (ExpressRoute → hub VNet or Virtual WAN).

## What you can honestly claim

- **After reading + quiz:** "I've studied hybrid connectivity on Google Cloud, AWS, and Azure — HA VPN, Cloud Interconnect, Direct Connect, ExpressRoute, hub-and-spoke designs, and TIC 3.0 considerations — and can discuss design trade-offs and SLA topologies."
- **After completing the lab:** "In a personal lab I configured Google Cloud HA VPN between two VPCs with Cloud Router BGP sessions, verified dynamic route exchange, and tested failover by removing a tunnel pair." Add "and designed equivalent AWS and Azure hybrid architectures on paper" if you did Parts B–C — but say "designed," not "built."
- **Still requires (cert / production experience / clearance):** provisioning or operating physical interconnects, carrier coordination, on-prem router configuration in production, TIC 3.0 implementation for an agency, and connectivity in classified environments. Don't claim "implemented Interconnect" or "hybrid network engineering experience" from this lab. Your homelab VPN/BGP work (if real) is legitimately claimable as homelab experience — label it that way.
