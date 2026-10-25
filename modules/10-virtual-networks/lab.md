# 10 Lab — Build a global VPC, peer it, and prove peering isn't transitive

**Cost:** $0 expected on Google Cloud. VPC networks, subnets, routes, and peerings have no charge. Three **e2-micro** VMs in `us-central1` and `us-east1` (both free-tier regions) with 10 GB standard disks, **no external IPs**, and a **1-hour self-delete timer** — the free tier pools e2-micro hours across instances, so ~3 VM-hours is well inside it. A few pings between regions are bytes of inter-region traffic ($0.02/GiB in North America) — rounds to $0.00. AWS (optional): a VPC, subnets, route table, and internet gateway with **no instances** — no charge. Azure (optional): two VNets and a peering with no VMs — no charge for the VNets; peering bills only per GB transferred, and nothing is transferred. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Inspect the `default` network and say what's wrong with it.
2. Plan CIDRs, then build a **custom-mode** VPC with subnets in **two regions**.
3. Ping across regions by internal IP — no peering, no VPN: the **global VPC**.
4. **Peer** a second VPC, then a third, and show from the route tables that peering is **not transitive**.
5. **Expand** a subnet.
6. (Optional) The same building blocks on AWS (regional VPC, per-AZ subnets, internet gateway) and Azure (regional VNet, peering, private-by-default subnets).

## Prerequisites

- Modules 00–09 done; budget alerts active.
- `gcloud config list` shows your main lab project (not the module 09 sandbox).

```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud services enable compute.googleapis.com iap.googleapis.com
```

## Your CIDR plan (write it down first)

| Network | Purpose | Subnet | Region | Range |
|---|---|---|---|---|
| `lab10-a` | "prod" | `a-central` | us-central1 | `10.10.1.0/24` |
| | | `a-east` | us-east1 | `10.10.2.0/24` |
| `lab10-b` | "shared services" | `b-central` | us-central1 | `10.20.1.0/24` |
| `lab10-c` | "partner" | `c-central` | us-central1 | `10.30.1.0/24` |

No ranges overlap, so any pair *could* be peered. (Your homelab is probably `192.168.x.x` or `10.0.x.x` — if you ever VPN it in, check it doesn't collide.)

---

## Part A — Google Cloud

### A1. Look at the `default` network (console, then CLI) — read only

Console: **VPC network → VPC networks** — is there a network named `default`? Click it → **Subnets** (one per region, all in `10.128.0.0/9`) → **Firewalls**.

```bash
gcloud compute networks list
gcloud compute firewall-rules list --filter="network:default" \
  --format="table(name,sourceRanges.list(),allowed[].map().firewall_rule().list())"
```

**What you should see (if it exists):** an **AUTO** subnet-mode network and rules like `default-allow-ssh` and `default-allow-rdp` with source `0.0.0.0/0` — SSH and RDP open to the whole internet for any VM that gets an external IP. That's why every lab since module 01 has used a custom network. In an organization, the `compute.skipDefaultNetworkCreation` org policy stops it from being created. (If your project has no `default` network, note that — someone or something already removed it.)

You *may* delete it in your personal lab project if nothing uses it: `gcloud compute networks list --filter=name=default` → check no VMs are on it → delete its firewall rules, then the network. Optional; not required.

### A2. Build a custom-mode, two-region VPC (console, then CLI)

Console: **VPC network → Create VPC network** → name `lab10-a` → **Subnet creation mode: Custom** → add subnet `a-central`, region `us-central1`, range `10.10.1.0/24` → **Add subnet** `a-east`, `us-east1`, `10.10.2.0/24` → **Dynamic routing mode: Regional** → Create.

CLI (either, not both):

```bash
gcloud compute networks create lab10-a --subnet-mode=custom
gcloud compute networks subnets create a-central --network=lab10-a --region=us-central1 --range=10.10.1.0/24
gcloud compute networks subnets create a-east    --network=lab10-a --region=us-east1    --range=10.10.2.0/24
```

Now the other two networks (CLI only — you know the console flow now):

```bash
gcloud compute networks create lab10-b --subnet-mode=custom
gcloud compute networks subnets create b-central --network=lab10-b --region=us-central1 --range=10.20.1.0/24
gcloud compute networks create lab10-c --subnet-mode=custom
gcloud compute networks subnets create c-central --network=lab10-c --region=us-central1 --range=10.30.1.0/24

gcloud compute networks subnets list --filter="network~lab10" \
  --format="table(name,region.basename(),ipCidrRange,network.basename())"
```

**Notice:** one network, `lab10-a`, holds subnets in **two regions**. On AWS or Azure those would have to be two separate VPCs/VNets.

### A3. Firewall rules: IAP SSH and internal ping only (CLI)

New networks deny all ingress by default (implied rule). Open only what the lab needs — module 11 goes deep on this.

```bash
for N in a b c; do
  gcloud compute firewall-rules create lab10-$N-allow-iap-ssh --network=lab10-$N \
    --direction=INGRESS --allow=tcp:22 --source-ranges=35.235.240.0/20
  gcloud compute firewall-rules create lab10-$N-allow-icmp-internal --network=lab10-$N \
    --direction=INGRESS --allow=icmp --source-ranges=10.0.0.0/8
done
```

> SSH only from IAP's range, never `0.0.0.0/0` — same reason as modules 01 and 05: open port 22 gets found and brute-forced within minutes, and it bypasses your Google identity and MFA.

### A4. Three VMs, no external IPs, self-deleting (CLI)

```bash
COMMON="--machine-type=e2-micro --no-address --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=pd-standard --boot-disk-size=10GB --no-service-account --no-scopes \
  --shielded-secure-boot --max-run-duration=1h --instance-termination-action=DELETE --labels=lab=10"

gcloud compute instances create vm-a-central --zone=us-central1-a --subnet=a-central $COMMON
gcloud compute instances create vm-a-east    --zone=us-east1-b    --subnet=a-east    $COMMON
gcloud compute instances create vm-b-central --zone=us-central1-a --subnet=b-central $COMMON

gcloud compute instances list --filter="labels.lab=10" \
  --format="table(name,zone.basename(),networkInterfaces[0].networkIP,networkInterfaces[0].accessConfigs[0].natIP)"
```

**Notice:** the last column (external IP) is empty for all three. The 1-hour timer deletes them even if you forget — so work through A5–A7 in one sitting, or re-create them.

### A5. The global VPC: ping across regions (CLI)

```bash
EAST_IP=$(gcloud compute instances describe vm-a-east --zone=us-east1-b --format="value(networkInterfaces[0].networkIP)")
B_IP=$(gcloud compute instances describe vm-b-central --zone=us-central1-a --format="value(networkInterfaces[0].networkIP)")

gcloud compute ssh vm-a-central --zone=us-central1-a --tunnel-through-iap \
  --command="ping -c 3 $EAST_IP; echo '--- now lab10-b:'; ping -c 3 -W 2 $B_IP || echo 'no route to lab10-b (expected)'"
```

**What you should see:**

- `vm-a-central` (Iowa) pings `vm-a-east` (South Carolina) on its **internal** `10.10.2.x` address. No peering, no VPN, no gateway — one global network.
- The ping to `vm-b-central` fails: different VPC, no connection.

### A6. Peer A↔B, then B↔C — and read the route tables (CLI)

Peering must be created **from both sides** before it's active.

```bash
gcloud compute networks peerings create a-to-b --network=lab10-a --peer-network=lab10-b
gcloud compute networks peerings create b-to-a --network=lab10-b --peer-network=lab10-a
gcloud compute networks peerings create b-to-c --network=lab10-b --peer-network=lab10-c
gcloud compute networks peerings create c-to-b --network=lab10-c --peer-network=lab10-b

gcloud compute networks peerings list --format="table(name,network.basename(),peerNetwork.basename(),state)"
```

Wait for every peering to show `ACTIVE`, then ping A → B again:

```bash
gcloud compute ssh vm-a-central --zone=us-central1-a --tunnel-through-iap --command="ping -c 3 $B_IP"
```

**What you should see:** it works now. Peering exchanged subnet routes, and `lab10-b`'s firewall rule allows ICMP from `10.0.0.0/8`. (Firewall rules are **not** shared across a peering — each side still controls its own ingress.)

Now the proof of non-transitivity. Look at which routes each network knows:

```bash
for N in lab10-a lab10-b lab10-c; do
  echo "== $N =="
  gcloud compute routes list --filter="network:$N" \
    --format="table(name,destRange,nextHopNetwork.basename(),nextHopPeering,nextHopGateway.basename())"
done
# Routes each network imports over its peerings:
gcloud compute networks peerings list-routes a-to-b --network=lab10-a --region=us-central1 --direction=INCOMING
gcloud compute networks peerings list-routes c-to-b --network=lab10-c --region=us-central1 --direction=INCOMING
```

Console view: **VPC network → Routes → Effective routes** → pick a network and region. ⚠️ Column names in gcloud output can vary by version; the console view is the easiest to read.

**What you should see:**

- `lab10-a` learns `10.20.1.0/24` (from B) but **not** `10.30.1.0/24` (C).
- `lab10-c` learns `10.20.1.0/24` (from B) but **not** `10.10.x.x` (A).
- `lab10-b` learns both.

B is in the middle, yet A and C can't reach each other through it. That's non-transitive peering — on all three clouds. To make A and C talk you'd peer them directly, or use a hub (Network Connectivity Center).

### A7. Expand a subnet (CLI)

`a-central` is a `/24`. Grow it to a `/23`:

```bash
gcloud compute networks subnets expand-ip-range a-central --region=us-central1 --prefix-length=23
gcloud compute networks subnets describe a-central --region=us-central1 --format="value(ipCidrRange)"   # 10.10.0.0/23
```

**Notice:** the range grew to `10.10.0.0/23` without touching the running VM. Try to shrink it back to `/24` and gcloud refuses — expansion is one-way. (It also must not overlap anything in the network *or its peers* — which is why the CIDR plan mattered.)

---

## Part B — AWS (optional): a regional VPC with per-AZ subnets, no instances

CloudShell, `us-east-1`, as `labadmin`.

```bash
VPC=$(aws ec2 create-vpc --cidr-block 10.40.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=lab,Value=10},{Key=Name,Value=lab10-vpc}]' \
  --query Vpc.VpcId --output text)
SUB1=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.40.1.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=lab,Value=10}]' --query Subnet.SubnetId --output text)
SUB2=$(aws ec2 create-subnet --vpc-id $VPC --cidr-block 10.40.2.0/24 --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=lab,Value=10}]' --query Subnet.SubnetId --output text)

aws ec2 describe-subnets --subnet-ids $SUB1 $SUB2 \
  --query "Subnets[].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock,Free:AvailableIpAddressCount}" --output table
```

**What you should see:** each subnet is pinned to **one AZ**, and a `/24` shows **251** free addresses (5 reserved).

Make `SUB1` a "public" subnet — in AWS that just means its route table sends `0.0.0.0/0` to an internet gateway:

```bash
IGW=$(aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=lab,Value=10}]' \
  --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC
RT=$(aws ec2 create-route-table --vpc-id $VPC --tag-specifications 'ResourceType=route-table,Tags=[{Key=lab,Value=10}]' \
  --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id $RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
ASSOC=$(aws ec2 associate-route-table --route-table-id $RT --subnet-id $SUB1 --query AssociationId --output text)
aws ec2 describe-route-tables --route-table-ids $RT --query "RouteTables[0].Routes" --output table
```

**What you should see:** a `local` route for `10.40.0.0/16` (automatic) and your `0.0.0.0/0 → igw-…`. `SUB2` still uses the main route table with only `local` — a private subnet. No NAT gateway here: those bill hourly (about $0.045/hour in the example region on AWS's pricing page) plus per GB.

## Part C — Azure (optional): regional VNets, peering, private subnets

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab10 --location eastus --tags lab=10
az network vnet create -g rg-lab10 -n lab10-vnet1 --address-prefixes 10.50.0.0/16 \
  --subnet-name app --subnet-prefixes 10.50.1.0/24 --tags lab=10
az network vnet create -g rg-lab10 -n lab10-vnet2 --address-prefixes 10.60.0.0/16 \
  --subnet-name app --subnet-prefixes 10.60.1.0/24 --tags lab=10

az network vnet subnet show -g rg-lab10 --vnet-name lab10-vnet1 -n app \
  --query "{prefix:addressPrefix, defaultOutboundAccess:defaultOutboundAccess}"

az network vnet peering create -g rg-lab10 -n v1-to-v2 --vnet-name lab10-vnet1 --remote-vnet lab10-vnet2 --allow-vnet-access
az network vnet peering create -g rg-lab10 -n v2-to-v1 --vnet-name lab10-vnet2 --remote-vnet lab10-vnet1 --allow-vnet-access
az network vnet peering list -g rg-lab10 --vnet-name lab10-vnet1 --query "[].{name:name,state:peeringState}" -o table
```

**What you should see:** both peerings `Connected`. Look at `defaultOutboundAccess`: `false` means a **private subnet** (no implicit internet egress); `null` means the older implicit-outbound behavior, depending on the API version your CLI used. Either way, Microsoft's direction is explicit outbound (NAT gateway). Note also there's no AZ on the subnet — Azure subnets span the region's zones.

---

## Verify it worked

| Check | Expected |
|---|---|
| `default` network rules | `0.0.0.0/0` on SSH/RDP (if the network exists) |
| `lab10-a` subnets | `us-central1` and `us-east1` in one network |
| Ping `vm-a-central` → `vm-a-east` | Works over internal IP, no peering |
| Ping A → B before peering / after | Fails / works |
| Routes in `lab10-a` and `lab10-c` | Each sees B's range, neither sees the other's |
| `a-central` after expand | `10.10.0.0/23` |
| (B) AWS subnets | One AZ each; 251 free IPs per `/24`; public RT has `0.0.0.0/0 → igw` |
| (C) Azure peering | `Connected` both ways |

## What to notice (reflection questions)

1. Two regions, one network, internal IPs, no VPN. What does that simplify for a multi-region agency app — and what does it make *more* important to segment?
2. B could reach A and C, but A and C couldn't reach each other. Why might a security architect *want* peering to be non-transitive?
3. You expanded a subnet with a VM running in it. What would have blocked the expansion if `lab10-b` had used `10.10.0.0/24`?
4. Map today's build to your OPNsense lab: which pieces had a direct equivalent, and which (broadcast, VRRP, your DHCP server) don't exist here?
5. Write a plain-English detection for an attacker adding a peering to a network they control (T1578).

## Cleanup

**Google Cloud** — VMs first, then peerings, firewall rules, subnets, networks:

```bash
gcloud compute instances delete vm-a-central vm-b-central --zone=us-central1-a --quiet 2>/dev/null || true
gcloud compute instances delete vm-a-east --zone=us-east1-b --quiet 2>/dev/null || true

gcloud compute networks peerings delete a-to-b --network=lab10-a --quiet
gcloud compute networks peerings delete b-to-a --network=lab10-b --quiet
gcloud compute networks peerings delete b-to-c --network=lab10-b --quiet
gcloud compute networks peerings delete c-to-b --network=lab10-c --quiet

for N in a b c; do
  gcloud compute firewall-rules delete lab10-$N-allow-iap-ssh lab10-$N-allow-icmp-internal --quiet
done
gcloud compute networks subnets delete a-central b-central c-central --region=us-central1 --quiet
gcloud compute networks subnets delete a-east --region=us-east1 --quiet
gcloud compute networks delete lab10-a lab10-b lab10-c --quiet
```

Confirm:

```bash
gcloud compute instances list --filter="labels.lab=10"            # Listed 0 items
gcloud compute disks list --filter="labels.lab=10"                # Listed 0 items
gcloud compute networks list --filter="name~lab10"                # Listed 0 items
gcloud compute firewall-rules list --filter="name~lab10"          # Listed 0 items
```

**AWS** — reverse order:

```bash
aws ec2 disassociate-route-table --association-id $ASSOC
aws ec2 delete-route-table --route-table-id $RT
aws ec2 detach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC
aws ec2 delete-internet-gateway --internet-gateway-id $IGW
aws ec2 delete-subnet --subnet-id $SUB1
aws ec2 delete-subnet --subnet-id $SUB2
aws ec2 delete-vpc --vpc-id $VPC
aws ec2 describe-vpcs --filters Name=tag:lab,Values=10 --query "Vpcs[].VpcId" --output text   # expect empty
```

If CloudShell restarted, find the IDs with `describe-vpcs`, `describe-subnets`, `describe-route-tables`, and `describe-internet-gateways` filtered by `Name=tag:lab,Values=10`.

**Azure**

```bash
az group delete --name rg-lab10 --yes
az group list --query "[?name=='rg-lab10']" -o table      # expect empty
```

**Final check — nothing billable remains:** no `lab10` VMs, disks, networks, or firewall rules on Google; no `lab=10` VPC on AWS; no `rg-lab10` on Azure. Tomorrow, check Google **Billing → Reports** filtered by `lab=10`: expect $0.00.

## Write-up prompt

> On [date] I planned a non-overlapping CIDR scheme and built custom-mode Google Cloud VPC networks, including one network with subnets in two regions, and verified VMs in different regions communicated over internal IPs without peering or VPN. I configured VPC Network Peering between three networks and used route tables to demonstrate that peering is non-transitive, kept firewall rules restricted to IAP SSH and internal ICMP, and expanded a subnet's primary range in place. I also reviewed the default network's permissive firewall rules. [Optional: I built an AWS VPC with per-AZ subnets and a public route table to an internet gateway, and peered two Azure VNets and inspected private-subnet defaults.] I deleted all resources afterward.
