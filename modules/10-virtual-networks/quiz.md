# 10 Quiz — Virtual networks

1. What's the scope of a VPC network and of a subnet on Google Cloud, AWS, and Azure?
<details><summary>Answer</summary>

Google: VPC global, subnets regional. AWS: VPC regional, each subnet in one Availability Zone. Azure: VNet regional, subnets regional and span the region's zones.
</details>

2. Name three things from your OPNsense/VLAN homelab that don't carry over to a cloud VPC.
<details><summary>Answer</summary>

Layer 2 constructs (VLAN tags, trunks, spanning tree); broadcast and multicast (so VRRP/keepalived and broadcast discovery don't work — Google's VPC is unicast-only); running your own DHCP server or relying on ARP between neighbors (the platform answers ARP and provides DHCP/DNS). The "router" is distributed SDN (Andromeda on Google), not an appliance.
</details>

3. How many usable addresses does a `/24` subnet give you on each cloud, and why?
<details><summary>Answer</summary>

Google: 252 (4 reserved — network, gateway, second-to-last, broadcast). AWS: 251 (5 reserved — network, VPC router, DNS, future use, broadcast). Azure: 251 (5 reserved — first four and last).
</details>

4. Spot the misconfiguration: "We use each project's `default` network for quick prototypes; nothing sensitive runs there."
<details><summary>Answer</summary>

The default network is auto mode with pre-populated firewall rules including `default-allow-ssh` and `default-allow-rdp` from `0.0.0.0/0`. Any prototype VM with an external IP is exposed to internet scanning and brute force, and prototypes often hold real credentials. Use custom-mode networks; enforce `compute.skipDefaultNetworkCreation` (and consider `compute.vmExternalIpAccess`) by org policy.
</details>

5. On Google Cloud, a VM has no external IP and the VPC has the default `0.0.0.0/0` route. Can it reach the internet?
<details><summary>Answer</summary>

No. The default route alone isn't enough; the VM needs an external IP or a Cloud NAT gateway. (It can still reach Google APIs privately if Private Google Access is enabled — module 11.)
</details>

6. Network A peers with B, and B peers with C. Can A reach C? What are your options if it must?
<details><summary>Answer</summary>

No — peering is non-transitive on Google, AWS, and Azure. Options: peer A and C directly; use a hub (Network Connectivity Center / Transit Gateway / Virtual WAN); or route through an appliance in a hub network where supported.
</details>

7. Why can't two auto-mode Google VPC networks be peered?
<details><summary>Answer</summary>

Auto-mode networks draw subnets from the same predefined ranges in `10.128.0.0/9`, so they overlap — and peered networks can't have overlapping subnet ranges.
</details>

8. Scenario: an agency has 40 application teams, a central network/security office, and wants consistent firewalls and one path to on-prem. Recommend a Google Cloud network design.
<details><summary>Answer</summary>

Shared VPC: a host project (owned by the central team, likely per environment — prod and nonprod) with custom-mode subnets per region; service projects per app team attached to it, with `compute.networkUser` granted on specific subnets only. Central team keeps network and security admin roles; hybrid connectivity (Cloud Router + VPN/Interconnect, module 13) lives in the host project. Firewall policy centrally (module 11). Billing stays per service project.
</details>

9. Can you shrink a Google subnet's primary range? Expand it? What can block an expansion?
<details><summary>Answer</summary>

Shrink: no. Expand: yes, in place, even with VMs running. It's blocked if the new, larger range would overlap another subnet in the network or in a peered network (or other connected ranges).
</details>

10. In AWS, what makes a subnet "public"?
<details><summary>Answer</summary>

Its route table has a `0.0.0.0/0` route to an internet gateway (and instances need public IPs to use it). A private subnet has no such route; outbound access, if needed, goes through a NAT gateway — which bills hourly and per GB.
</details>

11. What's changing about outbound internet access for new Azure VNets?
<details><summary>Answer</summary>

For API versions released after March 31, 2026, subnets in new VNets default to private (`defaultOutboundAccess = false`): VMs get no implicit outbound internet and need an explicit method such as a NAT gateway, a public IP, a load balancer with outbound rules, or a firewall/NVA. Existing VNets aren't changed.
</details>

12. Give two cloud network changes you'd alert on as possible adversary activity, with an ATT&CK reference.
<details><summary>Answer</summary>

New peerings or VPN tunnels to unknown networks, and new routes (especially `0.0.0.0/0` or appliance next hops) — network boundary bridging (T1599) or infrastructure modification (T1578). Also firewall changes opening ingress (T1562.007, module 11) and subnets created in unexpected regions.
</details>
