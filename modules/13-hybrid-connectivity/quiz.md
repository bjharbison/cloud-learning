# 13 Quiz — Hybrid and multi-cloud connectivity

1. Compare site-to-site IPsec VPN and a dedicated interconnect on path, bandwidth, setup time, and encryption.
<details><summary>Answer</summary>

VPN: encrypted tunnels over the internet, roughly 1–3 Gbps per Google tunnel (1.25 Gbps standard per AWS tunnel), minutes to set up, encrypted by design. Interconnect: private circuit into the provider's edge, 50 Mbps to multiple 100/400 Gbps, weeks to provision, predictable latency, **not encrypted by default**.
</details>

2. What does Google Cloud Router do, and does it forward packets?
<details><summary>Answer</summary>

It's a managed BGP speaker: it exchanges routes with peers (on-prem routers, other Cloud Routers) and programs learned prefixes into the VPC as dynamic routes. It does not forward data traffic. HA VPN and Interconnect VLAN attachments require it.
</details>

3. What's required for Google HA VPN's 99.99% SLA?
<details><summary>Answer</summary>

Tunnels on both HA VPN gateway interfaces (with BGP). Between two Google Cloud HA VPN gateways, both must be in the same region with interface 0 ↔ 0 and 1 ↔ 1. A single interface gets no SLA.
</details>

4. True or false: "We use Direct Connect / ExpressRoute / Cloud Interconnect, so our traffic is encrypted." Explain.
<details><summary>Answer</summary>

False on all three. Private circuits aren't encrypted by default. Options: MACsec (Layer 2, hop between your router and the provider's edge) or IPsec over the circuit (HA VPN over Cloud Interconnect, VPN over Direct Connect, IPsec over ExpressRoute private peering). AWS GovCloud requires VPN over Direct Connect for export-controlled data.
</details>

5. What topology gives a 99.99% SLA for Google Dedicated Interconnect?
<details><summary>Answer</summary>

Four connections: two in each of two metropolitan areas, in different edge availability domains. Two connections in one metro gives 99.9%.
</details>

6. Match the hub: Google, AWS (regional and global), Azure.
<details><summary>Answer</summary>

Google: Network Connectivity Center (global hub; VPC and hybrid spokes). AWS: Transit Gateway (regional) and Cloud WAN (global). Azure: Virtual WAN, or a customer-built hub VNet.
</details>

7. What changed from TIC 2.0 to TIC 3.0, and why does it matter for cloud connectivity?
<details><summary>Answer</summary>

TIC 2.0 forced agency traffic through a small number of physical TIC access points. TIC 3.0 (with OMB M-19-26) allows alternatives, placing security capabilities near the data through trust zones and policy enforcement points, with use cases including Cloud. Agencies can connect to cloud more directly if they can show which capabilities protect each path.
</details>

8. Spot the misconfiguration: the on-prem router advertises `0.0.0.0/0` over the VPN to the cloud.
<details><summary>Answer</summary>

Cloud workloads may now send all internet-bound traffic to the data center (or the VPN), changing egress paths, costs, and inspection unexpectedly — and routes can be accepted without review. Advertise only the prefixes needed, filter learned routes, and treat route changes as security events.
</details>

9. Which AWS Site-to-Site VPN option provides 5 Gbps tunnels, and what does it require?
<details><summary>Answer</summary>

Large-bandwidth tunnels (announced November 2025), available only on Transit Gateway or Cloud WAN attachments — not a virtual private gateway.
</details>

10. Which CISA emergency directives targeted VPN/edge appliances in 2024 and 2025, and which ATT&CK techniques describe the initial access?
<details><summary>Answer</summary>

ED 24-01 (Jan 2024, Ivanti Connect Secure/Policy Secure) and ED 25-03 (Sept 2025, Cisco ASA/Firepower, linked to ArcaneDoor). T1190 Exploit Public-Facing Application and T1133 External Remote Services.
</details>

11. What is Cross-Cloud Interconnect, and what changed with AWS in 2026?
<details><summary>Answer</summary>

Google-provisioned dedicated links between Google Cloud and AWS, Azure, OCI, or Alibaba Cloud. In April 2026 the jointly engineered Google–AWS service (AWS Interconnect – multicloud / Partner Cross-Cloud Interconnect for AWS) reached GA: minutes to provision, 1–100 Gbps, MACsec between provider edges.
</details>

12. An agency wants to start hybrid connectivity next month but a Dedicated Interconnect will take a quarter. What do you recommend?
<details><summary>Answer</summary>

Start with HA VPN (both interfaces, BGP, FIPS-compliant IKEv2 ciphers) sized with enough tunnels; plan non-overlapping CIDRs now; then add Interconnect (redundant per the SLA topology, with MACsec or HA VPN over Interconnect if policy requires encryption) and keep the VPN as a lower-priority backup.
</details>
