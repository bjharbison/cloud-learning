# 13 Lab — Build HA VPN with BGP between a "cloud" VPC and a simulated "on-prem" VPC, then fail a tunnel

**Cost:** about **$0.25–$0.40 of Free Trial credits** for one hour; $0 out of pocket while credits last. What bills: **four HA VPN tunnels at $0.05/tunnel-hour** (`us-central1`) = $0.20/hour; the four gateway IPs aren't charged while tunnels use them; one e2-micro is covered by the free tier and the second costs about a cent an hour; test traffic between the gateways is a few KB. **Set a 60-minute timer and run Cleanup when it goes off** — four forgotten tunnels cost about $146/month. A real VPN to your homelab, or any lab on AWS/Azure, would cost more and need a public endpoint you'd have to secure, so Parts B and C are **whiteboard exercises** instead. · **Time:** 75–90 min (Part A) + 30 min (Parts B–C) · **Clouds:** GCP (required, hands-on); AWS and Azure (design on paper)

## Goal

1. Create two custom VPCs: `lab13-cloud` (10.13.0.0/24) and `lab13-onprem` (192.168.13.0/24 — a homelab-style range standing in for an agency data center).
2. Connect them with **HA VPN**: two gateways, two **Cloud Routers** with private ASNs, four IPsec tunnels, four BGP sessions.
3. Watch BGP learn routes, ping across the tunnels, then **break a tunnel pair** and confirm traffic keeps flowing.
4. On paper: design the same hybrid connection for AWS and Azure, with a dedicated circuit, encryption, and TIC 3.0 in mind.

## Prerequisites

- Modules 00–12 done; budget alerts active; you understand CIDR planning and routes (module 10).

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1; ZONE=us-central1-a
gcloud services enable compute.googleapis.com iap.googleapis.com
SECRET1=$(openssl rand -base64 24); SECRET2=$(openssl rand -base64 24)
echo "secrets generated (not printed)"
```

Each tunnel *pair* (one tunnel on each gateway) shares a pre-shared key. Generating them randomly — never typing "password123" — is the first VPN hardening habit.

---

## Part A — Google Cloud (CLI, with console checkpoints)

### A1. Two networks, two VMs, safe firewall rules

```bash
gcloud compute networks create lab13-cloud --subnet-mode=custom --bgp-routing-mode=regional
gcloud compute networks subnets create lab13-cloud-sn --network=lab13-cloud --region=$REGION --range=10.13.0.0/24
gcloud compute networks create lab13-onprem --subnet-mode=custom --bgp-routing-mode=regional
gcloud compute networks subnets create lab13-onprem-sn --network=lab13-onprem --region=$REGION --range=192.168.13.0/24

# IAP SSH only (never 0.0.0.0/0), plus ICMP from the other side's range
gcloud compute firewall-rules create lab13-cloud-iap --network=lab13-cloud --allow=tcp:22 --source-ranges=35.235.240.0/20
gcloud compute firewall-rules create lab13-cloud-icmp --network=lab13-cloud --allow=icmp --source-ranges=192.168.13.0/24
gcloud compute firewall-rules create lab13-onprem-iap --network=lab13-onprem --allow=tcp:22 --source-ranges=35.235.240.0/20
gcloud compute firewall-rules create lab13-onprem-icmp --network=lab13-onprem --allow=icmp --source-ranges=10.13.0.0/24

for side in cloud onprem; do
  gcloud compute instances create lab13-$side-vm --zone=$ZONE --machine-type=e2-micro \
    --subnet=lab13-$side-sn --no-address --no-service-account --no-scopes \
    --image-family=debian-12 --image-project=debian-cloud \
    --boot-disk-type=pd-standard --boot-disk-size=10GB --shielded-secure-boot \
    --max-run-duration=2h --instance-termination-action=DELETE --labels=lab=13
done
ONPREM_IP=$(gcloud compute instances describe lab13-onprem-vm --zone=$ZONE --format="value(networkInterfaces[0].networkIP)"); echo $ONPREM_IP
```

Notice the VMs have **no service account** (they don't need cloud permissions) and **no external IP**. The ICMP rule allows only the peer range — not "everything from on-prem."

Try the ping now:

```bash
gcloud compute ssh lab13-cloud-vm --zone=$ZONE --tunnel-through-iap --command="ping -c 3 -W 2 $ONPREM_IP"
```

**What you should see:** 100% packet loss. Two VPCs with no connection have no route to each other.

### A2. HA VPN gateways and Cloud Routers

```bash
gcloud compute vpn-gateways create lab13-gw-cloud  --network=lab13-cloud  --region=$REGION --stack-type=IPV4_ONLY
gcloud compute vpn-gateways create lab13-gw-onprem --network=lab13-onprem --region=$REGION --stack-type=IPV4_ONLY

gcloud compute routers create lab13-cr-cloud  --network=lab13-cloud  --region=$REGION --asn=65013
gcloud compute routers create lab13-cr-onprem --network=lab13-onprem --region=$REGION --asn=65113

gcloud compute vpn-gateways describe lab13-gw-cloud --region=$REGION --format="yaml(vpnInterfaces)"
```

**What you should see:** two interfaces (`id: 0` and `id: 1`), each with its own external IP. Two interfaces on two separate IP pools are what makes the gateway "HA."

### A3. Four tunnels (the billing starts here)

Interface 0 ↔ interface 0 and interface 1 ↔ interface 1 — that pairing is required for the 99.99% SLA between two Google gateways.

```bash
gcloud compute vpn-tunnels create lab13-t0-cloud --region=$REGION --vpn-gateway=lab13-gw-cloud --interface=0 \
  --peer-gcp-gateway=lab13-gw-onprem --ike-version=2 --shared-secret="$SECRET1" --router=lab13-cr-cloud
gcloud compute vpn-tunnels create lab13-t1-cloud --region=$REGION --vpn-gateway=lab13-gw-cloud --interface=1 \
  --peer-gcp-gateway=lab13-gw-onprem --ike-version=2 --shared-secret="$SECRET2" --router=lab13-cr-cloud
gcloud compute vpn-tunnels create lab13-t0-onprem --region=$REGION --vpn-gateway=lab13-gw-onprem --interface=0 \
  --peer-gcp-gateway=lab13-gw-cloud --ike-version=2 --shared-secret="$SECRET1" --router=lab13-cr-onprem
gcloud compute vpn-tunnels create lab13-t1-onprem --region=$REGION --vpn-gateway=lab13-gw-onprem --interface=1 \
  --peer-gcp-gateway=lab13-gw-cloud --ike-version=2 --shared-secret="$SECRET2" --router=lab13-cr-onprem
```

### A4. BGP sessions on link-local /30s

Each tunnel gets a router interface and a BGP peer. The two ends of a tunnel use the two usable addresses of the same `/30` from `169.254.0.0/16`.

```bash
# Tunnel pair 0: 169.254.0.1 (cloud) <-> 169.254.0.2 (onprem)
gcloud compute routers add-interface lab13-cr-cloud --region=$REGION --interface-name=if-t0 \
  --ip-address=169.254.0.1 --mask-length=30 --vpn-tunnel=lab13-t0-cloud
gcloud compute routers add-bgp-peer lab13-cr-cloud --region=$REGION --peer-name=peer-t0 \
  --interface=if-t0 --peer-ip-address=169.254.0.2 --peer-asn=65113
gcloud compute routers add-interface lab13-cr-onprem --region=$REGION --interface-name=if-t0 \
  --ip-address=169.254.0.2 --mask-length=30 --vpn-tunnel=lab13-t0-onprem
gcloud compute routers add-bgp-peer lab13-cr-onprem --region=$REGION --peer-name=peer-t0 \
  --interface=if-t0 --peer-ip-address=169.254.0.1 --peer-asn=65013

# Tunnel pair 1: 169.254.1.1 (cloud) <-> 169.254.1.2 (onprem)
gcloud compute routers add-interface lab13-cr-cloud --region=$REGION --interface-name=if-t1 \
  --ip-address=169.254.1.1 --mask-length=30 --vpn-tunnel=lab13-t1-cloud
gcloud compute routers add-bgp-peer lab13-cr-cloud --region=$REGION --peer-name=peer-t1 \
  --interface=if-t1 --peer-ip-address=169.254.1.2 --peer-asn=65113
gcloud compute routers add-interface lab13-cr-onprem --region=$REGION --interface-name=if-t1 \
  --ip-address=169.254.1.2 --mask-length=30 --vpn-tunnel=lab13-t1-onprem
gcloud compute routers add-bgp-peer lab13-cr-onprem --region=$REGION --peer-name=peer-t1 \
  --interface=if-t1 --peer-ip-address=169.254.1.1 --peer-asn=65013
```

### A5. Watch it come up (CLI, then console)

```bash
sleep 60
gcloud compute vpn-tunnels list --filter="name~lab13" --format="table(name,status,detailedStatus)"
gcloud compute routers get-status lab13-cr-cloud --region=$REGION \
  --format="yaml(result.bgpPeerStatus[].name,result.bgpPeerStatus[].status,result.bgpPeerStatus[].numLearnedRoutes,result.bestRoutes[].destRange,result.bestRoutes[].nextHopIp)"
```

**What you should see:** all four tunnels `ESTABLISHED`; both BGP peers `UP` with `numLearnedRoutes: 1`; and in `bestRoutes`, **`192.168.13.0/24`** reachable via `169.254.0.2` **and** `169.254.1.2` — two equal paths. You never typed a static route: BGP advertised each VPC's subnet to the other side. ⚠️ If peers show `DOWN`, wait another minute; if still down, check that each `/30` pair and ASN matches exactly.

Console checkpoint: **Network Connectivity → VPN** shows the gateways, tunnels, and BGP status; **Hybrid Connectivity → Cloud Routers → lab13-cr-cloud** shows learned routes.

Now the ping:

```bash
gcloud compute ssh lab13-cloud-vm --zone=$ZONE --tunnel-through-iap --command="ping -c 5 $ONPREM_IP"
```

**What you should see:** replies. Encrypted IPsec across two gateways, routes learned by BGP, firewall rules allowing only the peer range.

### A6. Fail a tunnel pair — does the SLA design work?

Delete the interface-0 tunnels on both sides (simulating a link or gateway-interface failure), and ping continuously while you do it.

```bash
gcloud compute ssh lab13-cloud-vm --zone=$ZONE --tunnel-through-iap \
  --command="ping -c 90 -i 1 $ONPREM_IP | tail -3" &
sleep 10
gcloud compute vpn-tunnels delete lab13-t0-cloud lab13-t0-onprem --region=$REGION --quiet
wait
gcloud compute routers get-status lab13-cr-cloud --region=$REGION \
  --format="yaml(result.bgpPeerStatus[].name,result.bgpPeerStatus[].status,result.bestRoutes[].nextHopIp)"
```

**What you should see:** the ping summary shows little or no loss (a few dropped packets at most while BGP withdraws the dead path); `peer-t0` is down; the only remaining next hop for `192.168.13.0/24` is `169.254.1.2`. That's why HA VPN needs **both** interfaces in use — and why a single-tunnel design has no SLA.

(You'll delete the rest in Cleanup. The `if-t0`/`peer-t0` router config left behind is harmless and goes away with the routers.)

### A7. Read the audit trail

```bash
gcloud logging read 'protoPayload.methodName:"vpnTunnels" AND protoPayload.methodName:("insert" OR "delete")' \
  --limit=8 --freshness=2h \
  --format="table(timestamp,protoPayload.methodName,protoPayload.resourceName,protoPayload.authenticationInfo.principalEmail)"
```

**What you should see:** Admin Activity entries for each tunnel you created and deleted, with your identity. A new tunnel created by someone unexpected is exactly the detection idea from the README. ⚠️ Method names may appear as `v1.compute.vpnTunnels.insert` or `beta.…`; the filter matches either.

---

## Part B — AWS (whiteboard, no resources)

Draw this on paper or a whiteboard app. Then answer the questions.

*Scenario:* the same agency data center (172.16.0.0/12) must reach three AWS VPCs (prod, nonprod, shared services) in `us-east-1`.

1. Put a **Transit Gateway** in a central networking account; attach the three VPCs.
2. Add **Direct Connect**: two dedicated connections at two locations (Maximum resiliency model, 99.99%) → **Direct Connect gateway** → **transit virtual interface** → Transit Gateway.
3. Add **encryption**: MACsec on the dedicated ports, or a Site-to-Site VPN over the Direct Connect (needed in GovCloud for export-controlled data).
4. Add a **Site-to-Site VPN backup** over the internet to the same Transit Gateway (two tunnels per connection).
5. Use Transit Gateway **route tables** so nonprod can't reach prod, and only shared services can reach on-prem management ranges.

Questions: Which attachment types bill hourly? Where would the "policy enforcement point" sit for TIC 3.0? What would an adversary on a compromised on-prem VPN appliance be able to reach in your design?

## Part C — Azure (whiteboard, no resources)

*Scenario:* same agency, now with a hub-and-spoke in `East US`.

1. A **hub VNet** with an **ExpressRoute gateway** (zone-redundant SKU) and **Azure Firewall**; spokes peered to the hub with "use remote gateway."
2. **ExpressRoute** circuit, private peering, with a second circuit at a different peering location for resilience; MACsec if you use ExpressRoute Direct, or IPsec over private peering.
3. A **VPN Gateway** (AZ SKU, active-active, BGP) as backup.
4. **UDRs** forcing spoke-to-on-prem traffic through Azure Firewall.
5. Alternative: the same design as a **Virtual WAN Standard** hub.

Questions: What does ExpressRoute **Premium** add, and would this agency need it? Why can't this circuit reach Azure Government regions? Where are the logs for "who changed a route"?

---

## Verify it worked

| Check | Expected |
|---|---|
| Ping before VPN | 100% loss |
| Tunnels | 4 × `ESTABLISHED` |
| BGP | 2 peers `UP`; `192.168.13.0/24` learned via 169.254.0.2 and 169.254.1.2 |
| Ping after VPN | Replies |
| After deleting pair 0 | Ping continues with little or no loss; one next hop remains |
| Audit logs | Insert and delete events for `vpnTunnels` with your identity |
| Parts B–C | Two diagrams with redundancy, encryption, and segmentation marked |

## What to notice (reflection questions)

1. You never wrote a route. What would happen if the "on-prem" side advertised `0.0.0.0/0` instead of its subnet?
2. What exactly does the 99.99% SLA depend on, and which part of that design is the customer's job?
3. The IPsec tunnels crossed the internet between Google gateway IPs. On a Dedicated Interconnect, what would protect the traffic, and what wouldn't?
4. The ICMP rule allowed only the peer range. In an agency design, why treat on-prem as its own trust zone rather than "inside"?
5. Write a detection, in plain English, for T1599-style tampering in this project.

## Cleanup

Delete in this order (tunnels → routers → gateways → VMs/firewalls → networks):

```bash
gcloud compute vpn-tunnels delete lab13-t1-cloud lab13-t1-onprem --region=$REGION --quiet
gcloud compute vpn-tunnels delete lab13-t0-cloud lab13-t0-onprem --region=$REGION --quiet 2>/dev/null || echo "pair 0 already deleted"
gcloud compute routers delete lab13-cr-cloud lab13-cr-onprem --region=$REGION --quiet
gcloud compute vpn-gateways delete lab13-gw-cloud lab13-gw-onprem --region=$REGION --quiet
gcloud compute instances delete lab13-cloud-vm lab13-onprem-vm --zone=$ZONE --quiet 2>/dev/null || echo "VMs already self-deleted"
gcloud compute firewall-rules delete lab13-cloud-iap lab13-cloud-icmp lab13-onprem-iap lab13-onprem-icmp --quiet
gcloud compute networks subnets delete lab13-cloud-sn lab13-onprem-sn --region=$REGION --quiet
gcloud compute networks delete lab13-cloud lab13-onprem --quiet
unset SECRET1 SECRET2
```

Confirm:

```bash
gcloud compute vpn-tunnels list --filter="name~lab13"        # Listed 0 items
gcloud compute vpn-gateways list --filter="name~lab13"       # Listed 0 items
gcloud compute routers list --filter="name~lab13"            # Listed 0 items
gcloud compute instances list --filter="labels.lab=13"       # Listed 0 items
gcloud compute disks list --filter="labels.lab=13"           # Listed 0 items
gcloud compute networks list --filter="name~lab13"           # Listed 0 items
gcloud compute addresses list --filter="name~lab13"          # Listed 0 items
```

**AWS / Azure:** nothing was created.

**Final check — nothing billable remains:** no `lab13` tunnels, gateways, routers, VMs, disks, or networks. Tomorrow, open **Billing → Reports**, filter by **Networking** (Cloud VPN SKUs): expect roughly $0.20–$0.30 for today and nothing after.

## Write-up prompt

> On [date] I built a Google Cloud HA VPN between two custom VPCs, one simulating an on-premises network: two HA VPN gateways, two Cloud Routers with private ASNs, four IKEv2 tunnels using randomly generated pre-shared keys, and four BGP sessions on link-local /30s. I verified that BGP learned each side's subnet over two equal paths, confirmed connectivity with firewall rules limited to the peer range, then deleted one tunnel pair and observed traffic continue over the surviving path. I reviewed the Admin Activity audit entries for tunnel changes. I also designed equivalent hybrid architectures on paper for AWS (Transit Gateway, redundant Direct Connect with MACsec, VPN backup) and Azure (hub VNet with ExpressRoute, VPN backup, and Azure Firewall). I deleted all resources afterward.
