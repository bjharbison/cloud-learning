# 10 — Virtual networks: VPC/VNet, subnets, CIDR, routes, and how cloud SDN differs from on-prem

> **In one sentence:** you'll be able to plan a cloud network's address space, explain why Google's global VPC changes multi-region design, and connect networks with Shared VPC and peering — translating everything you built in OPNsense into cloud terms.

**Prereqs:** modules 00–09 (modules 01 and 05 used custom VPCs; module 02 previewed the global VPC; module 03 for projects and organizations) · **Time:** ~3.5 hours incl. lab · **Phase:** 3

## Learning objectives

- Map your OPNsense/VLAN homelab onto **VPCs**, **subnets**, and **routes** — and name what *doesn't* carry over.
- Plan **CIDR** ranges for a multi-environment, multi-region design without collisions.
- Explain Google Cloud's **global VPC** versus **regional** AWS VPCs and Azure VNets.
- Read a VPC **route table**: subnet routes, the default route, static and dynamic routes.
- Choose between **Shared VPC**, **VPC Network Peering**, and hub-and-spoke (**Network Connectivity Center**, **Transit Gateway**, **Virtual WAN**).

## Why this matters for the target roles

- **Customer engineer / architect:** networking is in the Google Public Sector CE posting's preferred qualifications. Every landing zone starts with an IP plan and a network topology, and bad CIDR choices are expensive to undo.
- **Cloud security:** network design decides blast radius and choke points. Module 11's controls sit on top of what you build here.
- **CTI:** lateral movement in the cloud follows routes and peerings. Reading a topology tells you where an intruder can go next.

---

## Concepts

### From OPNsense VLANs to a VPC

**Plain version:** a **VPC** (Virtual Private Cloud; Azure calls it a **VNet**, virtual network) is a private network you define entirely by API. You choose IP ranges, carve them into **subnets**, and the provider routes between them.

| Your homelab | Google Cloud | AWS | Azure |
|---|---|---|---|
| The whole routed LAN behind OPNsense | **VPC network** (global) | **VPC** (regional) | **VNet** (regional) |
| A VLAN with its own subnet (e.g., IoT 10.0.30.0/24) | **Subnet** (regional) | **Subnet** (one Availability Zone) | **Subnet** (regional, spans zones) |
| OPNsense as inter-VLAN router | Implicit VPC routing — no router VM | Implicit VPC router (the subnet's `.1`) | System routes |
| OPNsense WAN + NAT | Default route + external IP or **Cloud NAT** | **Internet gateway** + **NAT gateway** | Public IP / **NAT Gateway** |
| Per-interface firewall rules | VPC firewall rules / policies (module 11) | Security groups + NACLs (module 11) | NSGs (module 11) |
| Static routes / OSPF/BGP to another site | Static routes / **Cloud Router** (BGP) | Route tables / Transit Gateway | UDRs / Route Server ⚠️ / Virtual WAN |
| DHCP server and DNS on OPNsense | Provider DHCP + internal DNS (you don't run them) | Same (the `.2` address is AWS DNS) | Same |

**What doesn't carry over — the important part:**

- **No Layer 2.** Google's VPC supports unicast only: no broadcast, no multicast. There are no VLAN tags, no trunk ports, no spanning tree. Anything that depends on broadcast or multicast — VRRP/keepalived failover, some discovery protocols, Wake-on-LAN — needs a cloud-native replacement (usually a load balancer, module 12).
- **ARP is answered by the platform**, not by neighbors. You can't ARP-spoof your way between VMs in the same subnet the way you might on a flat home VLAN.
- **The "router" isn't a box.** Google's network virtualization stack, **Andromeda**, programs forwarding, firewalls, and routing across hosts and fabric. There's no single appliance to log into, patch, or bottleneck.
- **Addresses are reserved.** Google keeps 4 addresses in each subnet's primary range (network, gateway `.1`, second-to-last, broadcast). AWS and Azure each reserve 5 (`.0`–`.3` and the last). A `/24` gives you 252 or 251 usable, not 254.

**Bridge:** think of the VPC as OPNsense's routing and firewall tables lifted out of the appliance and enforced in every host's virtual NIC. The policy is the same idea; the enforcement point is everywhere.

### Google's global VPC vs regional VPCs and VNets

Module 02 previewed this; here's why it matters.

- **Google Cloud:** a VPC network, its routes, and its firewall rules are **global**. Subnets are **regional**. A VM in `us-central1` reaches a VM in `us-east1` on the same VPC by internal IP — no peering, no gateway, no VPN — over Google's backbone.
- **AWS:** a VPC lives in one **region**; each subnet lives in one **Availability Zone**, so zone-redundant designs need a subnet per AZ. Multi-region means multiple VPCs connected by peering or Transit Gateway.
- **Azure:** a VNet lives in one region; subnets **span all zones** in that region, so one subnet can hold zone-redundant resources. Multi-region means multiple VNets connected by (global) peering or Virtual WAN.

**Design consequence:** on Google, "one network for the whole agency, segmented by subnets and firewall policy" is natural. On AWS/Azure, multi-region networks are always a set of regional networks plus connectivity. Neither is better; the CE skill is explaining the trade-off — simpler global routing versus a larger single blast radius you must segment deliberately (module 11).

### Auto mode, custom mode, and the default network

- **Auto mode** VPCs get one subnet per region automatically, from predefined ranges inside `10.128.0.0/9`. **Custom mode** starts empty; you choose regions and ranges. You can convert auto → custom, never back. Google recommends **custom mode for production**. Auto-mode networks can't peer with each other (their ranges collide).
- **The `default` network:** new projects get an auto-mode network called `default` (unless an org policy prevents it), with pre-populated firewall rules — including the one module 01 warned you about, allowing SSH from anywhere. Production landing zones prevent it with the `compute.skipDefaultNetworkCreation` org policy (Google's security foundations blueprint enforces it; module 20 covers org policies).
- **AWS** gives every region a **default VPC** (`172.31.0.0/16`) with public subnets in each AZ — instances there get public IPs by default. **Azure** has no default VNet; you create one.

### CIDR planning — do it once, do it right

**Plain version:** pick non-overlapping private ranges for every network you will *ever* want to connect: each environment, each region, on-prem, partners, and the other clouds.

Rules that apply on all three clouds:

1. Use **RFC 1918** space (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). Google also allows `100.64.0.0/10` and some other special ranges; AWS VPC CIDRs must be `/16`–`/28`.
2. **Peered or VPN-connected networks can't overlap.** Overlap is the number-one reason "just connect it" turns into a re-IP project.
3. **Leave room to grow.** Google lets you **expand** a subnet's primary range (never shrink it); AWS lets you add secondary CIDRs to a VPC but not resize existing blocks; Azure lets you add address spaces.
4. **GKE eats addresses.** Pods and Services use secondary ranges (module 06); plan them big.

**A simple agency plan (example only):**

```
10.0.0.0/8 — agency cloud supernet (on-prem uses 172.16.0.0/12 — no overlap)
 ├─ 10.10.0.0/16  prod   ├─ 10.10.0.0/20  us-east4 workloads
 │                       ├─ 10.10.16.0/20 us-central1 workloads
 │                       └─ 10.10.64.0/18 GKE pods (secondary)
 ├─ 10.20.0.0/16  nonprod (same pattern)
 ├─ 10.30.0.0/16  shared services (DNS, AD, tooling)
 └─ 10.100.0.0/14 reserved: AWS / Azure / future
```

**Bridge to your homelab:** you already learned this the hard way if your homelab VPN ever collided with a hotel Wi-Fi's `192.168.1.0/24`. Cloud just raises the stakes.

### Routes

Every VPC has a route table, mostly written for you.

| Route | What it does | Google Cloud | AWS | Azure |
|---|---|---|---|---|
| **Subnet / local routes** | Reach every subnet in the network | Created per subnet, automatically | `local` route for the VPC CIDR | System routes for the VNet space |
| **Default route** | Everything else → internet | `0.0.0.0/0` → default internet gateway (removable) | You add `0.0.0.0/0` → internet gateway (that's what makes a subnet "public") | System route to the internet |
| **Static / custom** | Send traffic to an appliance, VPN, or load balancer | Static routes (optionally by network tag) | Route table entries | **User-defined routes (UDRs)** |
| **Dynamic** | Learned via BGP from on-prem or other networks | **Cloud Router** | Transit Gateway / VPN / Direct Connect propagation | Gateways / Route Server ⚠️ |
| **Peering** | Imported from a peered network | Peering routes | Peering routes you add manually | Peering system routes |

**Key subtlety (Google):** the default route alone doesn't give internet access. A VM also needs an external IP or **Cloud NAT** — which is why your lab VMs with `--no-address` have been unreachable from, and unable to reach, the internet. **Azure** is moving the same direction: for the API versions released after March 31, 2026, subnets in *new* VNets are **private by default** (no implicit outbound internet) and need a NAT gateway or other explicit method.

### Connecting networks: Shared VPC, peering, and hubs

| Need | Google Cloud | AWS | Azure |
|---|---|---|---|
| Many teams/projects, one centrally run network | **Shared VPC**: a **host project** owns the network; **service projects** deploy into its subnets. Requires an organization. | **VPC sharing**: owner account shares subnets with participant accounts in the same AWS Organization | Hub VNet + spoke VNets (peering) ⚠️ no direct "shared VNet" equivalent |
| Connect two separate networks privately | **VPC Network Peering** — any projects or orgs; **not transitive**; no overlap; firewall rules not shared | **VPC peering** — not transitive; no overlapping primary CIDRs; inter-region supported | **VNet peering** (incl. global) — not transitive by default |
| Many networks plus on-prem through a hub | **Network Connectivity Center** (VPC and hybrid spokes) | **Transit Gateway** (or Cloud WAN) | **Virtual WAN** |

**Shared VPC is the Google answer for agencies.** A central network team (Shared VPC Admin, `compute.xpnAdmin`) owns subnets, routes, and firewalls in the host project; app teams get `compute.networkUser` on specific subnets and can launch VMs there but can't change the network. Billing for resources stays with each service project (module 04 chargeback still works).

**Bridge to your intel background:** Shared VPC is a common communications infrastructure run by one office, with each program allowed onto specific circuits. Peering is a bilateral MOU between two programs — and like an MOU, it doesn't extend to anyone else either party has an agreement with (non-transitive).

> **Shared responsibility:** the provider runs the SDN, the physical network, and the backbone. **Your address plan, subnets, routes, peerings, which networks connect to which, and what's exposed to the internet are always the customer's.** A bad route or an unintended peering is a customer misconfiguration, not a provider failure.

---

## Text diagram — Shared VPC on a global network

```
 Org: agency.gov
 └─ Folder: Network ── Host project net-host-prod
        VPC "prod-vpc" (GLOBAL, custom mode)
        ├─ subnet app-use4   10.10.0.0/20   us-east4     ── networkUser → svc project "case-mgmt"
        ├─ subnet app-usc1   10.10.16.0/20  us-central1  ── networkUser → svc project "analytics"
        ├─ routes: subnet routes · 0.0.0.0/0 → default gateway (egress via Cloud NAT only)
        ├─ Cloud Router (BGP) ──► VPN / Interconnect to on-prem 172.16.0.0/12 (module 13)
        └─ peering ◄──► partner-vpc 10.200.0.0/16   (non-transitive: partner can't reach on-prem through us)

 VM in us-east4 ──── internal IP, Google backbone ────► VM in us-central1   (no peering, no VPN needed)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Network scope | **Global** VPC; regional subnets | Regional VPC; subnet per **AZ** | Regional VNet; subnets **span zones** | Biggest design difference |
| Default network | `default` auto-mode VPC with permissive firewall rules | Default VPC per region, public subnets | None | Disable or delete defaults in production |
| Address limits | Subnets `/29` minimum; primary range expandable | VPC and subnet CIDRs `/16`–`/28`; add secondary CIDRs | Add address spaces to a VNet | |
| Reserved IPs per subnet | 4 | 5 | 5 | |
| Internet egress | External IP or Cloud NAT (+ default route) | Internet gateway (public) / NAT gateway (private) | Public IP / NAT Gateway; new VNets private by default after Mar 31, 2026 API versions | |
| Central multi-team network | Shared VPC | VPC sharing (AWS RAM) | Hub-and-spoke | |
| Peering | VPC Network Peering (non-transitive) | VPC peering (non-transitive) | VNet peering (non-transitive) | Same rule everywhere |
| Hub | Network Connectivity Center | Transit Gateway / Cloud WAN | Virtual WAN | |
| Dynamic routing | Cloud Router (BGP) | TGW / VGW route propagation | Gateways / Route Server ⚠️ | Module 13 |
| Flow telemetry | VPC Flow Logs (opt-in, sampled) | VPC Flow Logs | VNet flow logs (NSG flow logs retire Sep 30, 2027) | Module 11/18 |
| Cost of the network itself | No charge for networks/subnets; pay data transfer (same-zone internal free; cross-zone $0.01/GiB; NA inter-region $0.02/GiB) | No charge for the VPC; pay NAT gateways, public IPv4 ($0.005/hr each), cross-AZ transfer | VNets free (50 always-free per the free-services page) ⚠️ peering per-GB charges not verified | AWS public IPv4 charge started Feb 2024 |

## Administer and monitor it

- **Inventory and topology:** `gcloud compute networks list`, `... subnets list`, `... routes list`; AWS `describe-vpcs`, `describe-route-tables`; Azure `az network vnet list`. Google's **Network Topology** and **Connectivity Tests** (Network Intelligence Center) visualize and test paths ⚠️ (names not re-verified this run).
- **IP management:** track allocations centrally (a spreadsheet becomes an IPAM tool at scale — AWS IPAM, Google internal ranges ⚠️).
- **Logs:** network, subnet, route, and peering changes are Admin Activity / management events (module 18). **VPC Flow Logs** are opt-in, sampled, and billed; they don't record ingress packets denied by firewall rules (firewall rules logging covers that, module 11).
- **Quotas:** routes, peerings per network, subnets — they bite in large Shared VPCs (module 04).

## Security angle

1. **Using the default network** with its permissive firewall rules (module 01) — or AWS default VPC public subnets.
2. **Flat networks**: one huge subnet with "allow internal" rules, so one compromised VM reaches everything.
3. **Unreviewed peerings**: a peering to a partner or vendor network that imports routes you didn't intend.
4. **Overlapping ranges** forcing NAT hacks that obscure attribution in logs.
5. **Unplanned internet egress**: every VM with an external IP, so exfiltration and C2 have a direct path (module 11 covers egress control).
6. **Too many people with network admin**: in Shared VPC, keep `compute.networkAdmin` and `compute.securityAdmin` with the central team.

## Threat intel angle

- **T1578 Modify Cloud Compute Infrastructure** and **T1562.007 Impair Defenses: Disable or Modify Cloud Firewall** (module 11) — the closest ATT&CK fits for an adversary adding a route, peering, or VPN that joins a segment to one they control. (**T1599 Network Boundary Bridging** describes the same idea on routers and firewalls; ATT&CK scopes it to network devices, so treat it as an analogy, not a cloud mapping.)
- **T1046 Network Service Discovery** — scanning internal ranges after gaining a foothold; flat networks make it rewarding.
- **T1021 Remote Services** — lateral movement over SSH/RDP between VMs, which internal firewall rules and segmentation limit.

**Detection ideas:** alert on new peerings, new routes with `0.0.0.0/0` or appliance next hops, new VPN tunnels, subnet creations in unexpected regions, and changes to a host project's network by anyone outside the network team.

**Bridge to your targeting background:** the network diagram is a target system analysis — nodes (subnets, appliances), links (routes, peerings), and critical nodes whose compromise opens everything (the host project, the hub). Defenders should map their own network the way an adversary would.

## Public sector notes

- **Shared VPC fits agency org structures**: a central network/security office owns the network; mission programs deploy into it. It also centralizes the evidence an assessor will ask for (modules 26–27).
- **Coordinate IP space with on-prem networks and partner agencies early** — overlap with legacy ranges is a common blocker for hybrid connectivity (module 13) and TIC-style egress designs ⚠️ (TIC specifics are module 17/27 territory).
- **Region choice inside a global VPC** still matters for data residency and authorization: a subnet in an unauthorized region is easy to create unless org policy restricts locations (module 03).

## Key takeaways

- A VPC/VNet is your OPNsense routed LAN, defined by API — but with no Layer 2, no broadcast/multicast, and platform-answered ARP.
- Google's VPC is **global** (regional subnets); AWS VPCs and Azure VNets are **regional**. AWS subnets live in one AZ; Azure subnets span zones.
- Plan CIDRs once, for everything you might ever connect. Overlap blocks peering and VPN.
- Routes: subnet routes are automatic; the default route needs an external IP or NAT to matter on Google; new Azure VNets are moving to private-by-default.
- Shared VPC (centrally owned network, many service projects) is the Google pattern for agencies; peering is non-transitive on all three clouds; hubs (NCC, Transit Gateway, Virtual WAN) scale beyond a few networks.
- Address plans, routes, peerings, and internet exposure are **always the customer's**.

## Sources

- [Google Cloud — VPC networks](https://docs.cloud.google.com/vpc/docs/vpc)
- [Google Cloud — Subnets](https://docs.cloud.google.com/vpc/docs/subnets)
- [Google Cloud — Routes](https://docs.cloud.google.com/vpc/docs/routes)
- [Google Cloud — VPC Network Peering](https://docs.cloud.google.com/vpc/docs/vpc-peering)
- [Google Cloud — Shared VPC](https://docs.cloud.google.com/vpc/docs/shared-vpc)
- [Google Cloud — Network Connectivity Center overview](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview)
- [Google Cloud — VPC Flow Logs](https://docs.cloud.google.com/vpc/docs/flow-logs)
- [Google Cloud — Network pricing](https://cloud.google.com/vpc/network-pricing)
- [Google Cloud Architecture Center — Preventative controls (org policy constraints)](https://docs.cloud.google.com/architecture/blueprints/security-foundations/preventative-controls)
- [Google Cloud — Best practices and reference architectures for VPC design](https://docs.cloud.google.com/architecture/best-practices-vpc-design)
- [Google Cloud Blog — Enter the Andromeda zone](https://cloud.google.com/blog/products/gcp/enter-andromeda-zone-google-cloud-platforms-latest-networking-stack)
- [Google Cloud — `gcloud compute networks subnets expand-ip-range`](https://docs.cloud.google.com/sdk/gcloud/reference/compute/networks/subnets/expand-ip-range)
- [AWS — What is Amazon VPC? (pricing note)](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
- [AWS — VPC CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html) and [Subnet CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html)
- [AWS — Share your VPC subnets with other accounts](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-sharing.html)
- [AWS Whitepaper — VPC peering](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/vpc-peering.html)
- [AWS — Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/)
- [Microsoft — Compare AWS and Azure networking options](https://learn.microsoft.com/en-us/azure/architecture/aws-professional/networking)
- [Microsoft — Private IP addresses in Azure (reserved addresses)](https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/private-ip-addresses)
- [Microsoft — Default outbound access in Azure](https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/default-outbound-access)
- [Microsoft — Explore free Azure services](https://azure.microsoft.com/en-gb/pricing/free-services)
- [Microsoft — NSG flow logs overview (retirement; VNet flow logs replacement)](https://learn.microsoft.com/en-us/azure/network-watcher/nsg-flow-logs-overview)
- [MITRE ATT&CK — T1578](https://attack.mitre.org/techniques/T1578/), [T1599](https://attack.mitre.org/techniques/T1599/), [T1046](https://attack.mitre.org/techniques/T1046/), [T1021](https://attack.mitre.org/techniques/T1021/)

Verified: 2026-10-25
