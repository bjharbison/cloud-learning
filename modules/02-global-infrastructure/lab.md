# 02 Lab — Map the terrain: regions, zones, and resource scope

**Cost:** $0 expected. Two **e2-micro** VMs run for under an hour in `us-central1` with 10 GB standard disks. Google's free tier counts e2-micro eligibility **by hours, not by instance** (one VM's worth per month ≈ 730 hours), so two VMs for an hour uses about 2 of those hours. No external IPs. One empty regional Cloud Storage bucket (5 GB-month free in US regions). AWS and Azure parts are read-only. · **Time:** 60 min · **Clouds:** GCP (required), AWS and Azure (read-only)

## Goal

1. See each cloud's regions and zones from the CLI, including AWS AZ IDs.
2. Create zonal, regional, and global resources and identify each one's scope.
3. Simulate a zone failure and see what survives.
4. Do the SLA math yourself.

## Prerequisites

- Modules 00–01 done. Budget alert active.
- `gcloud config list` shows your lab project. If you deleted the module 00 project, create a new one and link billing (module 00, A3).

---

## Part A — Google Cloud

### A1. Explore regions and zones (CLI)

```bash
gcloud compute regions list --format="table(name,status)"
gcloud compute zones list --filter="region:us-central1" --format="table(name,status)"
gcloud compute regions describe us-central1 --format="yaml(name,zones)"
```

Console equivalent: **Compute Engine → VM instances → Create instance** and open the Region and Zone dropdowns (then cancel).

Count the zones in `us-central1`. Then check the Google Cloud locations page from the README sources for a region with fewer data centers.

### A2. Create resources at three scopes

**Global — a VPC network** (module 10 covers networks; here it's just an example of a global resource):

```bash
gcloud compute networks create lab02-net --subnet-mode=custom
gcloud compute networks subnets create lab02-central \
  --network=lab02-net --region=us-central1 --range=10.20.0.0/24
```

No firewall rules are created, so nothing can reach these VMs. That's fine — we won't log in.

**Zonal — two VMs in different zones:**

```bash
for Z in a b; do
  gcloud compute instances create lab02-vm-$Z \
    --zone=us-central1-$Z --machine-type=e2-micro \
    --subnet=lab02-central --no-address \
    --image-family=debian-12 --image-project=debian-cloud \
    --boot-disk-type=pd-standard --boot-disk-size=10GB \
    --labels=lab=02
done
gcloud compute instances list --format="table(name,zone.basename(),status)"
```

**Regional — a Cloud Storage bucket:**

```bash
BUCKET=lab02-$(gcloud config get-value project)-$RANDOM
gcloud storage buckets create gs://$BUCKET --location=us-central1 \
  --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets describe gs://$BUCKET --format="yaml(location,location_type)"
```

### A3. Identify scope from the API

```bash
gcloud compute instances describe lab02-vm-a --zone=us-central1-a --format="value(zone)"
gcloud compute networks subnets describe lab02-central --region=us-central1 --format="value(region)"
gcloud compute networks describe lab02-net --format="value(selfLink)"
```

Look at the URLs: the VM's path contains `/zones/`, the subnet's contains `/regions/`, and the network's contains `/global/`. **The resource path tells you its failure domain.**

### A4. Simulate a zone failure

```bash
gcloud compute instances stop lab02-vm-a --zone=us-central1-a
gcloud compute instances list --format="table(name,zone.basename(),status)"
```

`lab02-vm-a` is `TERMINATED` (stopped); `lab02-vm-b` keeps running. In a real design, a load balancer (module 12) or regional managed instance group (module 05) would send traffic to the survivor automatically. The bucket and network didn't notice.

---

## Part B — AWS (read-only, $0)

In AWS CloudShell:

```bash
# Regions, including ones not enabled for your account
aws ec2 describe-regions --all-regions \
  --query "Regions[].{Region:RegionName,OptIn:OptInStatus}" --output table

# AZ names vs AZ IDs in your current Region
aws ec2 describe-availability-zones \
  --query "AvailabilityZones[].{Name:ZoneName,ID:ZoneId,Type:ZoneType}" --output table

# Same, in us-east-1
aws ec2 describe-availability-zones --region us-east-1 \
  --query "AvailabilityZones[].{Name:ZoneName,ID:ZoneId}" --output table
```

**Notice:** `ZoneName` (e.g., `us-east-1a`) vs `ZoneId` (e.g., `use1-az1`). If your account predates November 2025, compare with a friend's account: the names may map to different IDs in some older Regions. Also notice which Regions are `not-opted-in` — those are disabled until you opt in, which reduces T1535 exposure.

## Part C — Azure (read-only, $0)

In Azure Cloud Shell (ephemeral, Bash):

```bash
az account list-locations --query "[?metadata.regionType=='Physical'].{Name:name, Geo:metadata.geographyGroup, Pair:metadata.pairedRegion[0].name}" -o table

# Which zones does a small VM size offer in East US for this subscription?
az vm list-skus --location eastus --size Standard_B1s \
  --query "[0].locationInfo[0].zones" -o tsv
```

**Notice:** the paired-region column (some newer regions show none) and that zones come back as logical numbers `1 2 3`.

---

## Part D — SLA math (no cloud needed)

In any shell with Python:

```bash
python3 - <<'EOF'
mins = 30.4375 * 24 * 60
for sla in (99.5, 99.9, 99.95, 99.99):
    print(f"{sla}% -> {mins*(1-sla/100):.1f} min/month")
chain = 0.9995 * 0.9999
print(f"99.95% service x 99.99% service = {chain*100:.3f}%")
pair = 1 - (1-0.999)**2
print(f"two independent 99.9% copies (either works) = {pair*100:.4f}%")
EOF
```

Then answer: which is better for availability — chaining two services, or running two redundant copies? (And why is "independent" a big assumption?)

---

## Verify it worked

- You can name the three scopes and point to the `/zones/`, `/regions/`, `/global/` paths.
- With `lab02-vm-a` stopped, `lab02-vm-b` showed `RUNNING`.
- You found at least one AWS AZ name/ID pair and one Azure region with no pair.

## What to notice (reflection questions)

1. A mission app must survive a full zone outage with < 5 minutes downtime and < 1 minute data loss. State the RTO/RPO and pick cold, warm, or hot.
2. Your two VMs were in different zones but the same region. What failure would still take both down?
3. Why does a global VPC simplify multi-region designs on Google Cloud — and what's the risk of one network spanning everything? (Think blast radius.)
4. Write a detection rule in plain English for T1535 in your environment.

## Cleanup

```bash
gcloud compute instances delete lab02-vm-a --zone=us-central1-a --quiet
gcloud compute instances delete lab02-vm-b --zone=us-central1-b --quiet
gcloud storage buckets delete gs://$BUCKET
gcloud compute networks subnets delete lab02-central --region=us-central1 --quiet
gcloud compute networks delete lab02-net --quiet
```

If your Cloud Shell session restarted and `$BUCKET` is empty, find it with `gcloud storage ls` (look for `gs://lab02-…`).

**Confirm nothing billable remains:**

```bash
gcloud compute instances list
gcloud compute disks list
gcloud storage ls
gcloud compute networks list
```

No `lab02` resources should appear. Parts B–D created nothing. Check **Billing → Reports** tomorrow filtered by label `lab=02`: expect $0.00.

## Write-up prompt

> On [date] I mapped regions and zones on Google Cloud, AWS, and Azure from the CLI, including AWS AZ name-to-ID mappings and Azure region pairs. On Google Cloud I created zonal (VMs in two zones), regional (Cloud Storage bucket), and global (VPC network) resources, identified each one's scope from its API path, and simulated a zone failure by stopping one VM while the other kept running. I calculated allowed downtime for common SLAs and the effect of chaining versus redundancy, then deleted all resources.
