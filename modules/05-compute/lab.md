# 05 Lab — A self-healing, autoscaling fleet you can only reach through identity

**Cost:** $0 expected on Google Cloud. Every VM is an **e2-micro** in `us-central1` with a 10 GB **standard** persistent disk and **no external IP**. Google's free tier counts e2-micro **hours pooled across all your e2-micro VMs** (about one VM-month), so 2–3 small VMs for about an hour use a few of those hours; disks stay well under 30 GB-month. Don't use Spot for this lab — the free tier covers **non-preemptible** e2-micro only. AWS (optional): a `t3.micro` (free-plan eligible) for under an hour plus a public IPv4 address, drawn from your plan credits — expect cents. Azure (optional): a free-account B-series VM plus a small Standard HDD managed disk (⚠️ may cost a few cents while it exists — the free account's disk allowance wasn't verified this run); **Bastion Developer is free**. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional parallels)

## Goal

1. Turn on **OS Login** and reach VMs only through **IAP** — no open SSH.
2. Launch a VM with **no service account** and see what that does to the metadata server.
3. Build an **instance template** and a **regional managed instance group** across two zones.
4. Watch the group **self-heal**, then **autoscale** under load.
5. (Optional) Do the same "no open ports" access with **Session Manager** and **Azure Bastion**.

## Prerequisites

- Modules 00–04 done; budget alerts active.
- `gcloud config list` shows your lab project; Compute Engine API enabled.
- Remember module 01: you never use the `default` network for labs.

```bash
gcloud config list
PROJECT_ID=$(gcloud config get-value project)
gcloud services enable compute.googleapis.com iap.googleapis.com
```

---

## Part A — Google Cloud

### A1. Network with IAP-only SSH (CLI)

Same pattern as module 01 — a private network where port 22 is reachable only from IAP's forwarding range.

```bash
gcloud compute networks create lab05-net --subnet-mode=custom
gcloud compute networks subnets create lab05-subnet \
  --network=lab05-net --region=us-central1 --range=10.50.0.0/24
gcloud compute firewall-rules create lab05-allow-iap-ssh \
  --network=lab05-net --direction=INGRESS \
  --allow=tcp:22 --source-ranges=35.235.240.0/20
```

> Why not `0.0.0.0/0`? Internet scanners find open port 22 in minutes and start brute-forcing. A single weak credential becomes a breach, and none of it goes through your Google identity or MFA. IAP checks who you are first.

### A2. Turn on OS Login for the project (console, then CLI)

Console: **Compute Engine → Metadata → Edit → Add item** → key `enable-oslogin`, value `TRUE` → Save.

CLI (either, not both):

```bash
gcloud compute project-info add-metadata --metadata=enable-oslogin=TRUE
gcloud compute project-info describe --format="value(commonInstanceMetadata.items)" | tr ';' '\n' | grep -i oslogin
```

Now SSH access is governed by IAM: `roles/compute.osLogin` (log in) or `roles/compute.osAdminLogin` (log in with sudo). As project Owner you already have admin login. In a real org you'd grant these to groups, per VM or per project.

### A3. Look at an image family (CLI)

```bash
gcloud compute images describe-from-family debian-12 --project=debian-cloud \
  --format="yaml(name,family,creationTimestamp,guestOsFeatures)"
```

**Notice:** the family resolves to a specific, dated image. Templates that reference the family pick up new builds; templates that pin an image name don't. Look for `UEFI_COMPATIBLE` and `SEV_CAPABLE`-style entries under `guestOsFeatures` — that's the image telling you which Shielded/Confidential features it supports.

### A4. A VM with no cloud identity — and a self-destruct timer (CLI)

```bash
gcloud compute instances create lab05-solo \
  --zone=us-central1-a --machine-type=e2-micro \
  --subnet=lab05-subnet --no-address \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=pd-standard --boot-disk-size=10GB \
  --no-service-account --no-scopes \
  --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
  --max-run-duration=1h --instance-termination-action=DELETE \
  --labels=lab=05
```

`--max-run-duration=1h` with `DELETE` means this VM deletes itself an hour after it starts — a safety net if you forget cleanup.

Console equivalent: **Create instance** → e2-micro → boot disk Debian 12, Standard PD 10 GB → **Security → Shielded VM**: all three on → **Identity and API access → Service account: No service account** → **Networking**: `lab05-net`, external IPv4 **None** → **Advanced → VM provisioning model → Set a time limit for the VM** → 1 hour, on termination **Delete**.

SSH in through IAP, as your OS Login identity:

```bash
gcloud compute ssh lab05-solo --zone=us-central1-a --tunnel-through-iap
```

On the VM:

```bash
id                                    # your OS Login user, e.g. name_example_com
sudo -n true && echo "sudo works"     # because Owner implies OS Admin Login
curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/ ; echo
curl -s -o /dev/null -w "%{http_code}\n" \
  http://metadata.google.internal/computeMetadata/v1/instance/   # no header
exit
```

**What you should see:**

- The username is derived from your Google identity, not a key someone pasted into metadata.
- The service-accounts listing is **empty** (or has no usable account) — there are no cloud credentials on this box to steal.
- The request **without** the `Metadata-Flavor` header should be rejected (a `403` status) — a small SSRF speed bump, because naive SSRF can't add custom headers. ⚠️ The exact status code wasn't re-verified against Google's docs this run; note what you actually get.

Compare: on a VM with the default service account, the same `curl` returns an account, and `.../default/token` would hand back an access token. That token is what T1552.005 is about.

### A5. Instance template and a regional MIG (console, then CLI)

Console: **Compute Engine → Instance templates → Create** → name `lab05-tmpl`, **Location: Regional, us-central1** → same settings as A4 **except** leave out the time limit (a MIG would just recreate deleted VMs). Then **Instance groups → Create instance group → New managed instance group (stateless)** → name `lab05-mig`, template `lab05-tmpl`, **Location: Multiple zones** → `us-central1-a`, `us-central1-b` → autoscaling **Off** for now, size **2**.

CLI (either, not both):

```bash
gcloud compute instance-templates create lab05-tmpl \
  --instance-template-region=us-central1 \
  --machine-type=e2-micro \
  --region=us-central1 --subnet=lab05-subnet --no-address \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=pd-standard --boot-disk-size=10GB \
  --no-service-account --no-scopes \
  --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
  --labels=lab=05

gcloud compute instance-groups managed create lab05-mig \
  --region=us-central1 --zones=us-central1-a,us-central1-b \
  --template=projects/$PROJECT_ID/regions/us-central1/instanceTemplates/lab05-tmpl \
  --size=2

gcloud compute instance-groups managed list-instances lab05-mig --region=us-central1
```

**Notice:** two VMs, one in each zone, with generated names like `lab05-mig-xxxx`.

### A6. Self-healing (CLI)

Delete one of the group's VMs *behind its back*:

```bash
VICTIM=$(gcloud compute instance-groups managed list-instances lab05-mig \
  --region=us-central1 --format="value(name)" --limit=1)
VZONE=$(gcloud compute instance-groups managed list-instances lab05-mig \
  --region=us-central1 --format="value(zone.basename())" --limit=1)
gcloud compute instances delete $VICTIM --zone=$VZONE --quiet

watch -n 10 gcloud compute instance-groups managed list-instances lab05-mig --region=us-central1
```

Press `Ctrl+C` when you've seen it. **What you should see:** the group notices it's below target size and creates a replacement (often reusing the name). That's desired-state management — the same idea Kubernetes uses in module 06.

### A7. Autoscaling under load (CLI)

```bash
gcloud compute instance-groups managed set-autoscaling lab05-mig \
  --region=us-central1 \
  --min-num-replicas=1 --max-num-replicas=3 \
  --target-cpu-utilization=0.6 --cool-down-period=90
```

Note the **max**: 3. That's your cost ceiling (module 04).

Generate CPU load on one VM for 10 minutes:

```bash
VM=$(gcloud compute instance-groups managed list-instances lab05-mig \
  --region=us-central1 --format="value(name)" --limit=1)
ZONE=$(gcloud compute instance-groups managed list-instances lab05-mig \
  --region=us-central1 --format="value(zone.basename())" --limit=1)
gcloud compute ssh $VM --zone=$ZONE --tunnel-through-iap \
  --command="nohup timeout 600 sh -c 'for i in 1 2; do (while :; do :; done) & done; wait' >/dev/null 2>&1 &"
```

Watch for 10–15 minutes:

```bash
watch -n 30 gcloud compute instance-groups managed list-instances lab05-mig --region=us-central1
```

Console view: **Instance groups → lab05-mig → Monitoring** (CPU and group size).

**What you should see:** the group first scales *down* toward 1 (it was idle), then *up* as CPU stays above target, never past 3. ⚠️ e2-micro is a shared-core type with bursting, so CPU-based scaling on it can be slower or less dramatic than on standard types. If you don't see a scale-out within 15 minutes, that's fine — the key observations are the min/max bounds and the self-healing in A6.

---

## Part B — AWS (optional): Session Manager, no inbound ports

Sign in as `labadmin`, Region `us-east-1`, CloudShell.

### B1. An instance role that allows Systems Manager (CLI)

```bash
aws iam create-role --role-name lab05-ssm-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name lab05-ssm-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam create-instance-profile --instance-profile-name lab05-ssm-profile
aws iam add-role-to-instance-profile --instance-profile-name lab05-ssm-profile --role-name lab05-ssm-role
```

That policy lets the instance talk to Systems Manager — nothing else. It's the "least privilege identity" from the README.

### B2. A security group with zero inbound rules (CLI)

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query "Vpcs[0].VpcId" --output text)
SG_ID=$(aws ec2 create-security-group --group-name lab05-no-inbound \
  --description "lab05: no inbound rules" --vpc-id $VPC_ID --query GroupId --output text)
aws ec2 describe-security-groups --group-ids $SG_ID --query "SecurityGroups[0].IpPermissions"   # expect []
```

### B3. Launch with IMDSv2 required (CLI, then console)

```bash
sleep 30   # IAM changes take time to propagate; if the next command fails with an IAM/role error, wait 30 s and rerun it
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --instance-type t3.micro \
  --iam-instance-profile Name=lab05-ssm-profile \
  --security-group-ids $SG_ID \
  --metadata-options HttpTokens=required,HttpEndpoint=enabled \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=lab,Value=05},{Key=Name,Value=lab05-ssm}]' \
  --query "Instances[0].InstanceId" --output text)
echo $INSTANCE_ID
```

The default VPC gives it a public IPv4 address so the SSM Agent can reach Systems Manager **outbound**; with no inbound rules, nothing can initiate a connection to it. (Production would use private subnets with VPC endpoints instead — those cost money.)

Wait 2–3 minutes, then: **EC2 → Instances → lab05-ssm → Connect → Session Manager → Connect.** In the browser shell:

```bash
whoami
curl -s -o /dev/null -w "%{http_code}\n" http://169.254.169.254/latest/meta-data/     # expect 401: no token
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/info; echo
```

**What you should see:** the tokenless request is refused — that's IMDSv2 blocking the simple SSRF pattern. With a token, you see the instance profile. Then check **Systems Manager → Session Manager → Session history**: your session is recorded.

## Part C — Azure (optional): Bastion Developer, no public IP

Azure Cloud Shell (Bash). Bastion Developer is free but only in certain regions; this uses **Central US**.

### C1. A VM with no public IP and no NSG rule (CLI)

```bash
az group create --name rg-lab05 --location centralus --tags lab=05
az vm create --resource-group rg-lab05 --name lab05-vm \
  --image Ubuntu2204 --size Standard_B1s \
  --public-ip-address "" --nsg-rule NONE \
  --authentication-type password --admin-username labuser \
  --admin-password '<generate-in-password-manager>' \
  --storage-sku Standard_LRS --tags lab=05
az vm show -g rg-lab05 -n lab05-vm --query "securityProfile" -o json   # expect TrustedLaunch
```

If `Standard_B1s` isn't available to your subscription in that region, run `az vm list-skus --location centralus --size Standard_B --output table` and pick `Standard_B2ats_v2` (also free for 12 months). A password is used only because Bastion Developer is portal-only and Cloud Shell's ephemeral mode would lose a generated SSH key; production uses keys or Entra ID login.

### C2. Connect through Bastion Developer (console)

**Virtual machines → lab05-vm → Connect → Bastion** → **Deploy Bastion Developer** (no subnet or public IP needed) → enter `labuser` and the password → **Connect**. A browser SSH session opens. Run `ip -4 addr` and note the VM has only a private address.

---

## Verify it worked

| Check | Expected |
|---|---|
| `gcloud compute firewall-rules list --filter="network:lab05-net"` | Only `lab05-allow-iap-ssh` with source `35.235.240.0/20` |
| `gcloud compute instances list --filter="labels.lab=05" --format="table(name,zone.basename(),networkInterfaces[0].accessConfigs[0].natIP)"` | No external IPs |
| `gcloud compute instances describe <a MIG VM> --zone=<zone> --format="value(serviceAccounts)"` | Empty |
| MIG after A6 | Back to target size |
| AWS SG | `IpPermissions: []` and a Session Manager history entry |
| Azure VM | No public IP; `securityType: TrustedLaunch` |

## What to notice (reflection questions)

1. You removed the service account from these VMs. What breaks if a real app on them needs to read a Cloud Storage bucket, and what's the right fix? (Hint: a dedicated service account with one role, not the default.)
2. With OS Login, how do you revoke Brian's SSH access to 500 VMs at once? How would you do it with metadata SSH keys?
3. Session Manager needed **no** inbound rule; IAP needed one (from IAP's range). Which is the smaller attack surface, and what does Session Manager depend on instead?
4. The autoscaler's max was 3. Map that number to the module 04 conversation about appropriations.
5. In ATT&CK terms, which technique did each of today's controls make harder? (T1552.005, T1098.004, T1021.004 Remote Services: SSH, T1578.002)

## Cleanup

**Google Cloud** — group first (it owns its VMs), then template, then network:

```bash
gcloud compute instance-groups managed delete lab05-mig --region=us-central1 --quiet
gcloud compute instance-templates delete lab05-tmpl --region=us-central1 --quiet
gcloud compute instances delete lab05-solo --zone=us-central1-a --quiet 2>/dev/null \
  || echo "lab05-solo already self-deleted"
gcloud compute firewall-rules delete lab05-allow-iap-ssh --quiet
gcloud compute networks subnets delete lab05-subnet --region=us-central1 --quiet
gcloud compute networks delete lab05-net --quiet
```

Leave `enable-oslogin=TRUE` in project metadata — it's a good default. (To remove it: `gcloud compute project-info remove-metadata --keys=enable-oslogin`.)

Confirm:

```bash
gcloud compute instances list --filter="labels.lab=05"        # Listed 0 items
gcloud compute instance-groups managed list                   # no lab05-mig
gcloud compute instance-templates list                        # no lab05-tmpl
gcloud compute disks list --filter="labels.lab=05"            # Listed 0 items
gcloud compute networks list                                  # no lab05-net
```

**AWS**

```bash
aws ec2 terminate-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID
aws ec2 delete-security-group --group-id $SG_ID
aws iam remove-role-from-instance-profile --instance-profile-name lab05-ssm-profile --role-name lab05-ssm-role
aws iam delete-instance-profile --instance-profile-name lab05-ssm-profile
aws iam detach-role-policy --role-name lab05-ssm-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam delete-role --role-name lab05-ssm-role
aws ec2 describe-instances --filters Name=tag:lab,Values=05 Name=instance-state-name,Values=pending,running,stopped \
  --query "Reservations[].Instances[].InstanceId" --output text      # expect empty
aws ec2 describe-volumes --filters Name=tag:lab,Values=05 --query "Volumes[].VolumeId" --output text   # expect empty
```

If your CloudShell session restarted, find the instance with the `describe-instances` command above and the group with `aws ec2 describe-security-groups --filters Name=group-name,Values=lab05-no-inbound`.

**Azure** — the resource group holds the VM, disk, NIC, VNet, and the Bastion Developer resource:

```bash
az group delete --name rg-lab05 --yes
az group list --query "[?name=='rg-lab05']" -o table     # expect empty
az group list -o table                                    # note any NetworkWatcherRG; it's free, leave it
```

**Final check — nothing billable remains:** no `lab05` VMs, disks, templates, groups, or networks on Google; no running `lab=05` instances or volumes on AWS; no `rg-lab05` on Azure. Tomorrow, check Google **Billing → Reports** filtered by `lab=05`: expect $0.00.

## Write-up prompt

> On [date] I built a regional managed instance group on Google Cloud from a Shielded VM instance template (e2-micro, no external IP, no attached service account) spread across two zones, enforced OS Login, and administered the VMs only through IAP TCP forwarding with a firewall rule restricted to IAP's range. I observed the group recreate a deleted VM and configured CPU-based autoscaling with explicit minimum and maximum sizes. I verified the metadata server exposed no credentials on VMs without a service account. [Optional: On AWS I reached an EC2 instance with zero inbound security-group rules through Session Manager and confirmed IMDSv2 was required; on Azure I connected to a VM with no public IP through Azure Bastion Developer.] I deleted all resources afterward.
