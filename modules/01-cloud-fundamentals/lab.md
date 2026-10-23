# 01 Lab — Look under the hood: a VM, a container, and the responsibility line

**Cost:** $0 expected. The VM is an **e2-micro** in `us-central1` with a 10 GB **standard** persistent disk — inside Google Cloud's always-free limits (1 non-preemptible e2-micro/month in us-west1, us-central1, or us-east1; 30 GB-month standard PD). It has **no external IP**, which avoids both internet exposure and external-IP charges. The AWS and Azure parts are read-only API calls. · **Time:** 60–75 min · **Clouds:** GCP (required), AWS and Azure (read-only parallels)

## Goal

1. Prove to yourself where the VM boundary and the container boundary sit.
2. Reach a VM over SSH **without** opening port 22 to the internet.
3. Identify which pieces of today's setup were *your* responsibility.

## Prerequisites

- Module 00 complete: lab project with billing linked, budget alert set, `gcloud` config `lab` active.
- Cloud Shell open in the Google Cloud console.

```bash
gcloud config list            # confirm the right project before creating anything
gcloud services enable compute.googleapis.com
```

---

## Part A — Google Cloud

### A1. Containers share a kernel (Cloud Shell, no cost)

Cloud Shell includes Docker. Run:

```bash
uname -r                                    # Cloud Shell's kernel
docker run --rm alpine uname -r             # container's kernel
docker run --rm alpine cat /etc/os-release  # container's userland
cat /etc/os-release                         # Cloud Shell's userland
```

**What you should see:** the kernel version is **identical** in both; the OS name differs (Alpine vs Debian/Ubuntu). The container brought its own libraries, not its own kernel. Same thing as `uname -r` inside an LXC container on your Proxmox host.

### A2. Build a private network for the VM (CLI)

> You'll meet VPCs properly in module 10. For now, treat this as a private VLAN that you control.

**Why not use the `default` network?** Many projects get a `default` network whose firewall includes a rule allowing SSH (tcp:22) from **`0.0.0.0/0` — the entire internet**. Internet-wide scanners find open port 22 within minutes and start password and key attacks; a single weak credential or SSH bug becomes a breach. We'll use a network where SSH is reachable **only** through Google's Identity-Aware Proxy (IAP), which checks your Google identity and IAM role before passing traffic.

```bash
gcloud compute networks create lab01-net --subnet-mode=custom

gcloud compute networks subnets create lab01-subnet \
  --network=lab01-net --region=us-central1 --range=10.10.0.0/24

# Allow SSH ONLY from Google's IAP TCP-forwarding range, not the internet
gcloud compute firewall-rules create lab01-allow-iap-ssh \
  --network=lab01-net --direction=INGRESS \
  --allow=tcp:22 --source-ranges=35.235.240.0/20
```

`35.235.240.0/20` is the documented source range for IAP TCP forwarding. You'll find the same rule logic in console: **VPC network → Firewall**.

### A3. Create the VM (console, then CLI)

Console: **Compute Engine → VM instances → Create instance** → name `lab01-vm`, region `us-central1`, zone `us-central1-a`, machine type **e2-micro**, boot disk **Debian 12, Standard persistent disk, 10 GB**, Networking → network `lab01-net`, subnet `lab01-subnet`, **External IPv4 address: None**. Check the estimated monthly cost shown on the right and confirm it reflects the free tier.

CLI (use either, not both):

```bash
gcloud compute instances create lab01-vm \
  --zone=us-central1-a --machine-type=e2-micro \
  --subnet=lab01-subnet --no-address \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=pd-standard --boot-disk-size=10GB \
  --shielded-secure-boot \
  --labels=lab=01
```

### A4. SSH through IAP and look at the hardware

```bash
gcloud compute ssh lab01-vm --zone=us-central1-a --tunnel-through-iap
```

(When a VM has no external IP, `gcloud compute ssh` uses IAP automatically; the flag just makes it explicit. As project Owner you already hold the needed IAP role. In a real org you'd grant `roles/iap.tunnelResourceAccessor` only to the people who need it.)

On the VM:

```bash
systemd-detect-virt                      # expect: kvm
cat /sys/class/dmi/id/product_name       # expect: Google Compute Engine
lscpu | grep -i -E 'hypervisor|model name'
uname -r                                 # a DIFFERENT kernel from Cloud Shell's
sudo dmesg | grep -i 'secure boot'      # expect a line saying Secure Boot is enabled
exit
```

Back in Cloud Shell, confirm Shielded VM settings from the API:

```bash
gcloud compute instances describe lab01-vm --zone=us-central1-a \
  --format="yaml(shieldedInstanceConfig)"
```

**What you should see:** `kvm` — Google's KVM-based hypervisor — and a kernel that belongs to this VM alone. Compare with A1: a container borrows its host's kernel; a VM boots its own.

---

## Part B — AWS (read-only, $0)

In AWS CloudShell:

```bash
aws ec2 describe-instance-types \
  --instance-types t3.micro t2.micro m5.large m4.large \
  --query "InstanceTypes[].{Type:InstanceType,Hypervisor:Hypervisor}" --output table
```

**What you should see:** newer types report `nitro`; some older generations report `xen`. That's AWS's hypervisor transition visible through the API. Bonus: open the Nitro components whitepaper linked in the README and find the line about the Nitro Hypervisor having no shell or interactive access.

## Part C — Azure (read-only, $0)

In Azure Cloud Shell (ephemeral, Bash):

```bash
az vm list-skus --location eastus --size Standard_B1s \
  --query "[0].capabilities[?name=='HyperVGenerations']" -o table
```

**What you should see:** `V1,V2` (or similar) — the "generation" of Hyper-V VM the size supports. The hypervisor's name leaks into the API. If the query returns nothing, try another size such as `Standard_D2s_v5`.

---

## Verify it worked

- `docker run --rm alpine uname -r` matched Cloud Shell's kernel.
- `systemd-detect-virt` on the VM returned `kvm`.
- `gcloud compute instances describe lab01-vm --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs)"` returns **empty** (no external IP).
- `gcloud compute firewall-rules list --filter="network:lab01-net"` shows only the IAP rule.

## What to notice (reflection questions)

1. List everything you configured today. Which items would be the customer's job even if this were PaaS? (Hint: the firewall rule, who can SSH, and the IAM role behind IAP.)
2. What would an attacker need to reach `lab01-vm` now, compared with a VM on the `default` network with an external IP?
3. Why is a container a weaker tenant boundary than a VM? Answer in one sentence using the word "kernel."
4. AWS still reports some `xen` types. Why might a customer care which hypervisor their workload runs on?

## Cleanup

Delete in dependency order (VM → firewall rule → subnet → network):

```bash
gcloud compute instances delete lab01-vm --zone=us-central1-a --quiet
gcloud compute firewall-rules delete lab01-allow-iap-ssh --quiet
gcloud compute networks subnets delete lab01-subnet --region=us-central1 --quiet
gcloud compute networks delete lab01-net --quiet
docker image rm alpine 2>/dev/null   # Cloud Shell housekeeping only
```

The boot disk is deleted with the VM by default. **Confirm nothing billable remains:**

```bash
gcloud compute instances list
gcloud compute disks list
gcloud compute addresses list
gcloud compute networks list        # lab01-net should be gone
```

All four should show nothing from this lab. Parts B and C created nothing.

Final check: **Billing → Reports**, filter by label `lab=01` tomorrow (billing data lags) — expect $0.00.

## Write-up prompt

> On [date] I deployed a Compute Engine e2-micro VM on a custom VPC with no external IP and reached it over SSH only through Identity-Aware Proxy, using a firewall rule limited to IAP's source range. I confirmed the VM runs on Google's KVM-based hypervisor with its own kernel, while a Docker container in Cloud Shell shared its host's kernel. I identified the firewall rule, IAM access, and SSH path as customer responsibilities under the shared responsibility model, and deleted all resources afterward.
