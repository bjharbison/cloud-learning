# 13 — Hybrid and multi-cloud connectivity: VPN, Interconnect/Direct Connect/ExpressRoute, hub-and-spoke

> **In one sentence:** you'll be able to explain how an agency data center connects privately to Google Cloud, AWS, and Azure — IPsec VPN versus dedicated circuits, BGP, redundancy for a 99.99% SLA, encryption on "private" links, and hub-and-spoke designs — and why TIC 3.0 shapes those choices.

**Prereqs:** modules 00–12 (module 10 for CIDR planning, routes, and hubs; module 11 for firewalls) · **Time:** ~3.5 hours incl. lab · **Phase:** 3

## Learning objectives

- Compare **site-to-site IPsec VPN** and **dedicated/partner interconnects** on cost, bandwidth, latency, and security.
- Explain **BGP** in a hybrid design and what **Cloud Router** does.
- Design **HA VPN** and **Interconnect** topologies that qualify for 99.99% SLAs.
- Correct the myth that private circuits are encrypted — and name the fixes (**MACsec**, **IPsec over the circuit**).
- Compare hub-and-spoke on each cloud: **Network Connectivity Center**, **Transit Gateway / Cloud WAN**, **Virtual WAN**.
- Explain why agencies care: **TIC 3.0**, predictable private paths, and the VPN-appliance threat.

## Why this matters for the target roles

- **Customer engineer / architect:** "how do we connect our data center?" is in the first meeting of nearly every agency engagement. Hybrid connectivity is named in the Google Public Sector CE posting's preferred qualifications.
- **Cloud security:** the hybrid link joins two trust zones. Routes, firewall rules, and VPN configuration on both ends are **always the customer's**.
- **CTI:** edge VPN appliances have been among the most exploited devices of the last few years — CISA has issued emergency directives about them.

---

## Concepts

### The two families of hybrid links

| | **Site-to-site IPsec VPN** | **Dedicated / partner interconnect** |
|---|---|---|
| Path | Encrypted tunnels across the public internet | A physical or partner-provided circuit into the provider's edge |
| Setup time | Minutes | Weeks (colocation, cross-connects, a carrier) |
| Bandwidth | ~1–3 Gbps per tunnel; add tunnels | 50 Mbps up to multiple 100/400 Gbps circuits |
| Latency/jitter | Varies with the internet | Predictable |
| Encryption | **Yes, by design** | **No, by default** — add MACsec or IPsec |
| Cost | Low hourly per tunnel + egress | Port/attachment fees + often cheaper egress at volume |

**Homelab bridge:** you've likely run WireGuard or an OPNsense IPsec tunnel to a VPS. That's a site-to-site VPN. An interconnect is the enterprise version of renting a dedicated fiber pair instead of riding your ISP.

### BGP and Cloud Router

**Plain version:** **BGP** (Border Gateway Protocol) lets two routers tell each other which networks they can reach, and update automatically when a link fails. Static routes are fine for one tunnel; anything redundant uses BGP.

- **Google Cloud Router** is a managed BGP speaker in a VPC region. It learns on-prem prefixes and programs them as **dynamic routes** (module 10's route table), and advertises your subnets back. It doesn't forward packets — it only exchanges routes. **HA VPN requires it.**
- You pick a private **ASN** (autonomous system number) for each side: 64512–65534 or 4200000000–4294967294. Google's side can't be changed later.
- Each BGP session uses a link-local `/30` from `169.254.0.0/16`.
- AWS: route propagation on a virtual private gateway or Transit Gateway. Azure: VPN/ExpressRoute gateways speak BGP; **Azure Route Server** lets network virtual appliances (NVAs) exchange routes with a VNet.

**Bridge:** if you've run OSPF or BGP between OPNsense and another router (FRR plugin), you've done this. The cloud just hides the router behind an API.

### Google Cloud VPN

- **HA VPN** — a regional gateway with **two interfaces**, each with its own external IP. Dynamic (BGP) routing only. **99.99% SLA** when both interfaces have tunnels (and, for VPC-to-VPC, both gateways sit in the same region, interface 0 to 0 and 1 to 1). One interface alone gets **no SLA**.
- **Classic VPN** — single interface, 99.9% SLA, static routing. Its **BGP option was deprecated August 1, 2025**: no new dynamic Classic tunnels. Use HA VPN for anything new.
- **Throughput:** each tunnel handles up to 250,000 packets per second — roughly 1–3 Gbps depending on packet size. Need more? Add tunnels and let BGP spread traffic.
- **IKE:** IKEv1 and IKEv2, pre-shared keys. Use IKEv2 (required for IPv6 and for choosing ciphers).
- **Price:** $0.05 per tunnel-hour in `us-central1` (higher in some regions), plus egress. Gateway IPs used by tunnels aren't charged separately.

### Google Cloud Interconnect

| Option | What it is | Capacity |
|---|---|---|
| **Dedicated Interconnect** | Your router cross-connected to Google in a colocation facility | 10, 100, or 400 Gbps circuits (400G GA March 2026), up to 8 per connection |
| **Partner Interconnect** | A service provider carries you to Google | 50 Mbps – 50 Gbps per VLAN attachment |
| **Cross-Cloud Interconnect** | Google-provisioned links between Google and **AWS, Azure, OCI, or Alibaba Cloud** | 10/100 Gbps; 400 Gbps GA since March 2026 ⚠️ (check per-cloud availability) |

- **VLAN attachments** connect a circuit to a Cloud Router in your VPC.
- **SLA topologies:** **99.9%** = two connections in one metro, different edge availability domains. **99.99%** = four connections, two in each of two metros. Redundancy is the customer's design choice.
- **Encryption:** Google states Cloud Interconnect **doesn't encrypt by default**. Options: **MACsec** (Layer 2, protects only the hop from your router to Google's edge router) or **HA VPN over Cloud Interconnect** (IPsec across the circuit; must be chosen when the VLAN attachment is created). Google recommends layering IPsec or TLS on top of MACsec.

**Multi-cloud news worth knowing:** AWS and Google announced a jointly engineered link in December 2025 — AWS calls it **AWS Interconnect – multicloud**; Google calls it **Partner Cross-Cloud Interconnect for AWS**. AWS declared it GA on April 14, 2026; on Google's side the VPC Network Peering path went GA that day and the Network Connectivity Center path went GA on September 29, 2026. It provisions in minutes at 1–100 Gbps, and uses MACsec between the providers' edge routers. It's built on an open API specification other clouds are expected to adopt.

### AWS

- **Site-to-Site VPN** — every connection has **two tunnels** (to different AWS endpoints). Terminates on a **virtual private gateway** (one VPC) or a **Transit Gateway** (many). $0.05 per connection-hour. Standard tunnels top out at **1.25 Gbps**; **5 Gbps large-bandwidth tunnels** (since November 2025) require Transit Gateway or Cloud WAN. **Accelerated VPN** rides Global Accelerator (Transit Gateway only).
- **Direct Connect** — dedicated **1, 10, 100, or 400 Gbps** ports; **hosted connections** 50 Mbps–25 Gbps through partners. **Virtual interfaces:** private (VPCs), public (AWS public endpoints), transit (Transit Gateway via a **Direct Connect gateway**). **Not encrypted by default** — use **MACsec** (10/100/400G dedicated) or VPN over Direct Connect. The **Resiliency Toolkit** models Maximum (99.99%), High (99.9%), and Dev/Test.
- **Hubs:** **Transit Gateway** (regional hub; $0.05 per attachment-hour + per-GB processing) and **Cloud WAN** (a managed global WAN with segments that behave like VRFs).

### Azure

- **VPN Gateway** — new gateways use the **AZ SKUs** (VpnGw1AZ–VpnGw5AZ, 650 Mbps to 10 Gbps aggregate) or the **Basic** SKU (no BGP, no active-active; Microsoft says not for production). Non-AZ VpnGw1–5 SKUs had a September 30, 2026 retirement date ⚠️ (retirement completion not confirmed). Active-active and BGP on all but Basic.
- **ExpressRoute** — a circuit with **two links to two Microsoft edge routers** and dual BGP sessions, 50 Mbps–10 Gbps; **ExpressRoute Direct** gives dual 10/100/400 Gbps ports. **Private peering** reaches VNets; **Microsoft peering** reaches Microsoft 365 and Azure public services. SKUs: **Local** (data transfer included), **Standard**, **Premium** (global reach across geopolitical regions, more routes). **Global Reach** links your own sites over Microsoft's backbone. **FastPath** bypasses the gateway for high throughput. **Not encrypted by default** — MACsec on Direct, or IPsec over private peering.
- **Hubs:** **hub-and-spoke VNets** (Microsoft's reference architecture) or **Virtual WAN** (Basic = site-to-site VPN only; Standard adds ExpressRoute, point-to-site, transit, Azure Firewall).

### Hub-and-spoke, briefly

Module 10 introduced hubs. In hybrid designs the hub is where the on-prem link lands, so every spoke reaches on-prem — and on-prem reaches every spoke — through one inspected point.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Hub | **Network Connectivity Center** (global hub) | **Transit Gateway** (regional) / **Cloud WAN** (global) | **Virtual WAN** hub / hub VNet |
| Hybrid spokes | HA VPN tunnels, VLAN attachments, Router appliance VMs | VPN and Direct Connect gateway attachments | VPN, ExpressRoute, point-to-site |
| Using the cloud as your WAN | NCC **site-to-site data transfer** | Cloud WAN / TGW peering | Global Reach / Virtual WAN |

NCC topologies: **mesh** (default), **star** (center and edge groups), and **hybrid inspection**. A hub's topology is fixed at creation.

**Bridge to your intel background:** a hub is the communications center every circuit runs through. Convenient, auditable — and the single node an adversary most wants. Treat the hub project/account/subscription as high-value terrain.

### Why agencies care: TIC 3.0 and private paths

- **TIC 3.0** (CISA's Trusted Internet Connections program) replaced TIC 2.0's "route everything through a few physical TIC access points" model. **OMB M-19-26** dropped the requirement to backhaul traffic through those access points when an alternative exists. TIC 3.0 places security capabilities near the data using **trust zones** and **policy enforcement points**. Its use cases: **Traditional TIC, Branch Office, Remote User, Cloud**.
- **What it means for design:** agencies can reach cloud services directly — but they must show which security capabilities apply on each path. A private interconnect with defined inspection points is easy to explain to an assessor; ad hoc internet paths are not.
- **Government regions:** AWS GovCloud requires VPN over Direct Connect for export-controlled data; Azure Government has its own ExpressRoute locations and circuits can't cross clouds; Google's Assured Workloads IL4 package lists Cloud VPN, Cloud Interconnect (with HA VPN), Cloud Router, and NCC (modules 26–27 go deeper).
- **FIPS:** Google's FedRAMP/DoD networking guide says customers must use only FIPS 140-2-compliant ciphers with Cloud VPN — a customer configuration choice, not an automatic property.

> **Shared responsibility — say it plainly:** the provider runs its edge routers, gateways, and backbone. **The VPN configuration (peers, keys, ciphers), BGP advertisements, routes, firewall rules on both ends, encryption on interconnects, redundancy design, and the on-prem device are always the customer's.**

---

## Text diagram — an agency hybrid design on Google Cloud

```
 Agency DC (172.16.0.0/12) ── TIC-aligned security stack (PEP)
   ├─ Router A ══ Dedicated Interconnect, metro 1 (MACsec + HA VPN over Interconnect) ═╗
   ├─ Router B ══ Dedicated Interconnect, metro 2 (                ″                ) ═╣  99.99%
   └─ HA VPN backup over internet (2 tunnels, BGP, lower priority) ─────────────────────╢
                                                                                         ║
 Google Cloud: NCC hub (star) ◄── hybrid spokes (VLAN attachments, VPN tunnels)          ║
   ├─ Cloud Router (ASN 64514) learns 172.16.0.0/12; advertises 10.10.0.0/16 ◄══════════╝
   ├─ Shared VPC "prod" (center) ── hierarchical FW policy: only agency ranges inbound
   └─ edge spokes: nonprod VPC, partner VPC (no route to on-prem)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Site-to-site VPN | **HA VPN** (2 interfaces, BGP, 99.99%) | Site-to-Site VPN (2 tunnels per connection) | VPN Gateway (AZ SKUs, active-active) | Google needs Cloud Router for HA VPN |
| VPN price (US) | $0.05/tunnel-hour | $0.05/connection-hour | Per gateway-hour by SKU ⚠️ | An AWS connection includes 2 tunnels |
| Dedicated circuit | Dedicated Interconnect (10/100/400G) | Direct Connect (1/10/100/400G) | ExpressRoute Direct (10/100/400G) | |
| Partner circuit | Partner Interconnect (50 Mbps–50 Gbps) | Hosted connections (50 Mbps–25 Gbps) | ExpressRoute via provider (50 Mbps–10 Gbps) | |
| Encryption on circuits | Off by default; MACsec or HA VPN over Interconnect | Off by default; MACsec or VPN over DX | Off by default; MACsec (Direct) or IPsec | Same myth to bust everywhere |
| Dynamic routing | Cloud Router | VGW / TGW BGP | Gateways; Route Server for NVAs | |
| Hub | Network Connectivity Center (global) | Transit Gateway (regional) / Cloud WAN | Virtual WAN / hub VNet | |
| Direct cloud-to-cloud | Cross-Cloud Interconnect; Partner CCI for AWS | AWS Interconnect – multicloud | (via Google CCI or partners) | Google–AWS link GA Apr 2026 |

## Administer and monitor it

- **Tunnel and BGP state:** `gcloud compute vpn-tunnels describe` (status `ESTABLISHED`), `gcloud compute routers get-status` (BGP sessions and learned routes); AWS `describe-vpn-connections` tunnel telemetry; Azure connection status and BGP peer status.
- **Alert on:** tunnel down, BGP session flaps, unexpected learned prefixes, route count near limits.
- **Logs:** gateway, tunnel, router, and attachment changes are Admin Activity / CloudTrail / Activity Log events (module 18). VPC Flow Logs show what actually crosses the link.
- **Capacity:** watch per-tunnel packet rates and interconnect utilization; add tunnels or circuits before you hit the ceiling.

## Security angle

1. **Over-advertising routes.** On-prem advertises `0.0.0.0/0` or a huge supernet and suddenly cloud egress hairpins through the data center — or the reverse, exposing every cloud subnet to the whole enterprise.
2. **"It's a private line, so it's encrypted."** It isn't. Add MACsec or IPsec where policy requires.
3. **Weak IPsec settings** — IKEv1, short or reused pre-shared keys, non-FIPS ciphers where FIPS is required.
4. **Flat trust:** the hybrid link treated as "inside," with allow-all firewall rules from on-prem ranges. Treat on-prem as its own zone.
5. **Single tunnel or single circuit** — no SLA, and an outage becomes a mission impact.
6. **Unpatched on-prem VPN appliances** — the device on your end is your attack surface (next section).

## Threat intel angle

- **T1133 External Remote Services** and **T1190 Exploit Public-Facing Application** — VPN appliances are prime initial-access targets. CISA **ED 24-01** (January 19, 2024) ordered agencies to mitigate Ivanti Connect Secure / Policy Secure vulnerabilities; **ED 25-03** (September 25, 2025) addressed Cisco ASA/Firepower compromise tied to the **ArcaneDoor** campaign (ATT&CK C0046), including firmware-level persistence.
- **T1599 Network Boundary Bridging** — adversaries on a compromised edge device alter routing or filtering to reach networks they shouldn't. A hybrid link turns that into cloud access.
- **T1572 Protocol Tunneling** — C2 or exfiltration hidden inside allowed tunnels.
- **T1557 Adversary-in-the-Middle** and **T1040 Network Sniffing** — why "unencrypted private circuit" matters for high-value traffic.
- NSA and CISA's **"Selecting and Hardening Standards-based Remote Access VPN Solutions"** (September 2021) remains a good public reference for appliance hardening.

**Detection ideas:** new VPN tunnels or peer gateways created outside change control; BGP learning new prefixes (especially default routes); tunnels terminating on unexpected peer IPs; traffic from on-prem ranges to sensitive subnets it never touched before.

**Bridge to your OT background:** this is the IT/OT DMZ problem again. The conduit between zones is where you concentrate monitoring, and the boundary device is the thing adversaries live on.

## Public sector notes

- **TIC 3.0** changes the question from "does traffic go through a TIC access point?" to "which security capabilities apply on this path, and where is the enforcement point?" Have that answer ready for every hybrid design.
- **Lead times:** dedicated circuits take weeks to months; agencies often start on HA VPN and migrate to Interconnect. Plan CIDRs first (module 10) — overlap blocks everything.
- **Classified and disconnected environments** use entirely different connectivity models (module 28).

## Key takeaways

- VPN = encrypted, fast to set up, internet path, ~1–3 Gbps per tunnel. Interconnect = private, predictable, high bandwidth, **unencrypted by default**.
- BGP (Cloud Router on Google) makes redundant links work; HA VPN's 99.99% SLA needs both interfaces used.
- 99.99% interconnect designs need redundant circuits across metros on every cloud.
- Hubs: NCC, Transit Gateway/Cloud WAN, Virtual WAN — the hub is high-value terrain.
- TIC 3.0 lets agencies connect directly to cloud if they can show the security capabilities on each path.
- VPN configuration, routing, encryption choices, and the on-prem device are **always the customer's**.

## Sources

- [Google Cloud — Cloud VPN overview](https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/overview), [HA VPN topologies](https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/topologies), [Classic VPN deprecation](https://docs.cloud.google.com/network-connectivity/docs/vpn/deprecations/classic-vpn-deprecation), [Supported IKE ciphers](https://docs.cloud.google.com/network-connectivity/docs/vpn/concepts/supported-ike-ciphers), [Create HA VPN gateways to connect VPC networks](https://docs.cloud.google.com/network-connectivity/docs/vpn/how-to/creating-ha-vpn2)
- [Google Cloud — Network Connectivity pricing](https://cloud.google.com/network-connectivity/pricing)
- [Google Cloud — Cloud Interconnect overview](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/overview), [Dedicated Interconnect](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/dedicated-overview), [Cross-Cloud Interconnect](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/cci-overview), [MACsec](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/macsec-overview), [HA VPN over Cloud Interconnect](https://docs.cloud.google.com/network-connectivity/docs/interconnect/concepts/ha-vpn-interconnect), [release notes](https://docs.cloud.google.com/network-connectivity/docs/interconnect/release-notes)
- [Google Cloud — Network Connectivity Center overview](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview) and [topologies](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/connectivity-topologies)
- [Google Cloud blog — AWS and Google Cloud collaborate on multicloud networking](https://cloud.google.com/blog/products/networking/aws-and-google-cloud-collaborate-on-multicloud-networking/)
- [Google Cloud — Configure networks for FedRAMP and DoD](https://docs.cloud.google.com/architecture/configure-networks-fedramp-dod-google-cloud) and [Assured Workloads IL4 package](https://docs.cloud.google.com/assured-workloads/docs/control-packages/il4)
- [AWS — Site-to-Site VPN](https://docs.aws.amazon.com/vpn/latest/s2svpn/VPC_VPN.html), [VPN pricing](https://aws.amazon.com/vpn/pricing/), [5 Gbps tunnels announcement](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-site-to-site-vpn-5-gbps-bandwidth-tunnels/), [Accelerated VPN](https://docs.aws.amazon.com/vpn/latest/s2svpn/accelerated-vpn.html)
- [AWS — Direct Connect dedicated connections](https://docs.aws.amazon.com/directconnect/latest/UserGuide/dedicated_connection.html), [connection options](https://docs.aws.amazon.com/directconnect/latest/UserGuide/connection_options.html), [virtual interfaces](https://docs.aws.amazon.com/directconnect/latest/UserGuide/WorkingWithVirtualInterfaces.html), [encryption in transit](https://docs.aws.amazon.com/directconnect/latest/UserGuide/encryption-in-transit.html), [MACsec](https://docs.aws.amazon.com/directconnect/latest/UserGuide/MACsec.html), [Resiliency Toolkit](https://docs.aws.amazon.com/directconnect/latest/UserGuide/resiliency_toolkit.html)
- [AWS — Transit Gateway pricing](https://aws.amazon.com/transit-gateway/pricing/), [Cloud WAN](https://docs.aws.amazon.com/network-manager/latest/cloudwan/what-is-cloudwan.html), [AWS Interconnect – multicloud GA](https://aws.amazon.com/about-aws/whats-new/2026/04/aws-announces-ga-AWS-interconnect-multicloud/), [Direct Connect in GovCloud](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-dc.html)
- [Microsoft — VPN Gateway SKUs](https://learn.microsoft.com/en-us/azure/vpn-gateway/about-gateway-skus) and [What's new](https://learn.microsoft.com/en-us/azure/vpn-gateway/whats-new)
- [Microsoft — ExpressRoute introduction](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-introduction), [ExpressRoute Direct](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-erdirect-about), [FastPath](https://learn.microsoft.com/en-us/azure/expressroute/about-fastpath), [locations and providers](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-locations-providers), [hybrid connectivity design guide](https://learn.microsoft.com/en-us/azure/networking/design-guide/hybrid-connectivity)
- [Microsoft — Virtual WAN](https://learn.microsoft.com/en-us/azure/virtual-wan/virtual-wan-about), [hub-spoke reference architecture](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke), [Route Server](https://learn.microsoft.com/en-us/azure/route-server/overview)
- [CISA — TIC 3.0 core guidance](https://www.cisa.gov/resources-tools/resources/trusted-internet-connections-tic-30-core-guidance-documents), [TIC program](https://www.cisa.gov/resources-tools/programs/trusted-internet-connections-tic), [TIC FAQ](https://www.cisa.gov/tic-faq)
- [CISA — ED 24-01 (Ivanti)](https://www.cisa.gov/news-events/alerts/2024/01/19/cisa-issues-emergency-directive-ivanti-vulnerabilities), [ED 25-03 (Cisco)](https://www.cisa.gov/news-events/directives/ed-25-03-identify-and-mitigate-potential-compromise-cisco-devices), [NSA/CISA VPN hardening guidance](https://www.cisa.gov/news-events/alerts/2021/09/28/cisa-and-nsa-release-guidance-selecting-and-hardening-vpns)
- [MITRE ATT&CK — T1133](https://attack.mitre.org/techniques/T1133/), [T1190](https://attack.mitre.org/techniques/T1190/), [T1599](https://attack.mitre.org/techniques/T1599/), [T1572](https://attack.mitre.org/techniques/T1572/), [T1557](https://attack.mitre.org/techniques/T1557/), [T1040](https://attack.mitre.org/techniques/T1040/), [C0046 ArcaneDoor](https://attack.mitre.org/campaigns/C0046/)

Verified: 2026-10-26
