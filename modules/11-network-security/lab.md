# 11 Lab — Lock it down: firewall policy, private API access, egress deny, and a VPC Service Controls dry run

**Cost:** $0 expected on Google Cloud. One **e2-micro** VM in `us-central1` (free tier), 10 GB standard disk, no external IP, 2-hour self-delete timer. A global network firewall policy using only **Essentials** rules (IP/port/protocol) — no charge. A tiny Standard bucket inside the free tier. Firewall Rules Logging on two rules for under an hour produces a few hundred log entries — inside Cloud Logging's free allotment (⚠️ network-telemetry pricing for firewall logs not re-verified this run; expect $0.00). VPC Service Controls has no separate charge. **Do not** use FQDN, geolocation, or threat-intelligence matches in this lab (Cloud NGFW Standard bills per GiB). AWS (optional): a security group, an unattached NACL, and an S3 gateway endpoint — all free. Azure (optional): an NSG and an ASG — free. · **Time:** 90–120 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Replace classic VPC firewall rules with a **network firewall policy**: IAP SSH in, nothing else.
2. Watch an internal-only VM **fail** to reach Cloud Storage, then succeed after enabling **Private Google Access**.
3. Add **deny-all egress**, see API access break, and restore it with a narrow allow to `private.googleapis.com`.
4. Read **firewall logs** for allowed and denied traffic.
5. (Optional, needs an organization) Put the project in a **VPC Service Controls dry-run perimeter** and find the violation your own Cloud Shell request creates.
6. (Optional) AWS security group vs NACL defaults and a gateway endpoint; Azure NSG defaults.

## Prerequisites

- Modules 00–10 done; budget alerts active.
- `gcloud config list` shows your main lab project.

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
REGION=us-central1; ZONE=us-central1-a
B=lab11-$PROJECT_ID-$RANDOM
gcloud services enable compute.googleapis.com iap.googleapis.com storage.googleapis.com
echo "$B" # note it down
```

---

## Part A — Google Cloud

### A1. Network, bucket, and a least-privilege identity (CLI)

```bash
gcloud compute networks create lab11-net --subnet-mode=custom
gcloud compute networks subnets create lab11-subnet --network=lab11-net \
  --region=$REGION --range=10.11.0.0/24          # Private Google Access OFF for now

gcloud storage buckets create gs://$B --location=$REGION --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=11
echo "classified-ish lab data" > hello.txt && gcloud storage cp hello.txt gs://$B/

gcloud iam service-accounts create lab11-reader --display-name="lab11 bucket reader"
SA=lab11-reader@$PROJECT_ID.iam.gserviceaccount.com
sleep 30   # new service accounts take a moment to propagate; if the next command errors, wait and rerun it
gcloud storage buckets add-iam-policy-binding gs://$B --member=serviceAccount:$SA --role=roles/storage.objectViewer
```

The VM will run as `lab11-reader`, which can read **one bucket** and nothing else.

### A2. A network firewall policy instead of VPC rules (console, then CLI)

Console: **Network Security → Cloud NGFW → Firewall policies → Create firewall policy** → name `lab11-policy`, **Deployment scope: Global** → add rule: priority `100`, **Ingress**, **Allow**, source IPv4 `35.235.240.0/20`, protocol TCP `22`, **Logs: On** → **Associate** with `lab11-net` → Create.

CLI (either, not both):

```bash
gcloud compute network-firewall-policies create lab11-policy --global \
  --description="lab11: IAP SSH only"

gcloud compute network-firewall-policies rules create 100 \
  --firewall-policy=lab11-policy --global-firewall-policy \
  --direction=INGRESS --action=allow \
  --src-ip-ranges=35.235.240.0/20 --layer4-configs=tcp:22 \
  --enable-logging --description="SSH from IAP only"

gcloud compute network-firewall-policies associations create \
  --firewall-policy=lab11-policy --network=lab11-net \
  --name=lab11-assoc --global-firewall-policy
```

> No `0.0.0.0/0` on port 22 — the same rule you've followed since module 01. IAP checks your Google identity first, so the only ingress path is an authenticated, logged one.

### A3. An internal-only VM (CLI)

```bash
gcloud compute instances create lab11-vm --zone=$ZONE --machine-type=e2-micro \
  --subnet=lab11-subnet --no-address \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-type=pd-standard --boot-disk-size=10GB \
  --service-account=$SA --scopes=cloud-platform \
  --shielded-secure-boot \
  --max-run-duration=2h --instance-termination-action=DELETE \
  --labels=lab=11
```

Write a tiny helper script **in Cloud Shell**, then copy it to the VM. It fetches the object using the VM's own identity from the metadata server (always reachable, regardless of firewall rules):

```bash
cat > fetch.sh <<'EOF'
#!/bin/bash
# usage: ./fetch.sh              -> normal DNS for storage.googleapis.com
#        ./fetch.sh 199.36.153.8 -> force the private.googleapis.com VIP
TOKEN=$(curl -s -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
RES=()
[ -n "$1" ] && RES=(--resolve "storage.googleapis.com:443:$1")
curl -s -m 15 "${RES[@]}" -H "Authorization: Bearer $TOKEN" \
  "https://storage.googleapis.com/storage/v1/b/BUCKET/o/hello.txt?alt=media" || echo "FAILED / timed out"
echo
EOF
sed -i "s/BUCKET/$B/" fetch.sh && chmod +x fetch.sh && grep storage/v1 fetch.sh

gcloud compute scp fetch.sh lab11-vm:~/ --zone=$ZONE --tunnel-through-iap
```

The `grep` should show your real bucket name in the URL. The script asks the metadata server for a short-lived token for `lab11-reader`, then calls the Cloud Storage JSON API with it. (If `scp` complains, SSH in and recreate the file with a text editor.)

### A4. No route to the API → enable Private Google Access (CLI)

```bash
gcloud compute ssh lab11-vm --zone=$ZONE --tunnel-through-iap --command="~/fetch.sh"
```

**What you should see:** `FAILED / timed out`. The VM has valid credentials and the IAM grant, but no external IP and no NAT — Cloud Storage's public endpoint is unreachable.

```bash
gcloud compute networks subnets update lab11-subnet --region=$REGION --enable-private-ip-google-access
sleep 30
gcloud compute ssh lab11-vm --zone=$ZONE --tunnel-through-iap --command="~/fetch.sh"
```

**What you should see:** `classified-ish lab data`. Private Google Access let an internal-only VM reach Google APIs over Google's network — still no internet access for anything else.

### A5. Deny all egress, then allow only the private API VIP (CLI)

```bash
gcloud compute network-firewall-policies rules create 1000 \
  --firewall-policy=lab11-policy --global-firewall-policy \
  --direction=EGRESS --action=deny \
  --dest-ip-ranges=0.0.0.0/0 --layer4-configs=all \
  --enable-logging --description="default deny egress"
sleep 30
gcloud compute ssh lab11-vm --zone=$ZONE --tunnel-through-iap --command="~/fetch.sh"
```

**What you should see:** `FAILED / timed out` again. Egress rules apply to Private Google Access traffic too — the VM was sending to Google's public API addresses, and you just denied all egress. (SSH still works: the firewall is stateful, so replies to your allowed inbound IAP connection flow back.)

Now allow only HTTPS to `private.googleapis.com` (199.36.153.8/30):

```bash
gcloud compute network-firewall-policies rules create 900 \
  --firewall-policy=lab11-policy --global-firewall-policy \
  --direction=EGRESS --action=allow \
  --dest-ip-ranges=199.36.153.8/30 --layer4-configs=tcp:443 \
  --description="Google APIs via private.googleapis.com only"
sleep 30
gcloud compute ssh lab11-vm --zone=$ZONE --tunnel-through-iap --command="~/fetch.sh; echo '--- via private VIP:'; ~/fetch.sh 199.36.153.8"
```

**What you should see:** the first call (normal DNS → public Google IPs) still fails; the second, forced to `199.36.153.8`, succeeds. In production you'd make that automatic with a private Cloud DNS zone mapping `*.googleapis.com` to the VIP (a zone costs a little, so the lab uses `curl --resolve`). With VPC Service Controls you'd use `restricted.googleapis.com` (199.36.153.4/30) instead, which serves only perimeter-supported APIs.

**This is a real egress architecture:** no public IPs, deny-by-default egress, one narrow exception for Google APIs. Malware on this VM can't call home over the internet.

### A6. Read the firewall logs (console, then CLI)

Console: **Logging → Logs Explorer**:

```
logName="projects/PROJECT_ID/logs/compute.googleapis.com%2Ffirewall"
```

CLI:

```bash
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/compute.googleapis.com%2Ffirewall\"" \
  --limit=15 --freshness=1h \
  --format="table(timestamp,jsonPayload.disposition,jsonPayload.connection.src_ip,jsonPayload.connection.dest_ip,jsonPayload.connection.dest_port)"
```

**What you should see:** `ALLOWED` entries from `35.235.x.x` (IAP) to the VM on port 22, and `DENIED` entries from `10.11.0.x` to Google public IPs on 443 — the egress your rule blocked. ⚠️ Field names in firewall log records can vary slightly between VPC rules and policy rules; expand an entry in the console if the table columns come up empty.

Also check what's effectively applied to the network:

```bash
gcloud compute networks get-effective-firewalls lab11-net --format=yaml | head -60
```

### A7. (Optional — needs an organization) VPC Service Controls in dry run

Skip this if your lab project shows **No organization** (module 03). Dry run **logs but never blocks**, so it can't lock you out.

```bash
ORG_ID=$(gcloud projects get-ancestors $PROJECT_ID --format="value(id,type)" | awk '$2=="organization"{print $1}')
echo "org: $ORG_ID"     # empty → stop here
ME=$(gcloud config get-value account)
gcloud organizations add-iam-policy-binding $ORG_ID \
  --member=user:$ME --role=roles/accesscontextmanager.policyAdmin

gcloud access-context-manager policies list --organization=$ORG_ID
```

If that lists a policy, use its ID. If it's empty, create one (and remember you created it, for cleanup):

```bash
gcloud access-context-manager policies create --organization=$ORG_ID --title="lab11 access policy"
POLICY=$(gcloud access-context-manager policies list --organization=$ORG_ID --format="value(name)" | head -1)
```

Create a **dry-run-only** perimeter around this project, restricting Cloud Storage:

```bash
gcloud access-context-manager perimeters dry-run create lab11_perimeter --policy=$POLICY \
  --perimeter-title="lab11 perimeter" --perimeter-type=regular \
  --perimeter-resources=projects/$PROJECT_NUMBER \
  --perimeter-restricted-services=storage.googleapis.com
```

Wait a few minutes for propagation, then — from **Cloud Shell**, which is outside the perimeter — read the bucket:

```bash
sleep 300
gcloud storage cat gs://$B/hello.txt          # succeeds — dry run never blocks
sleep 60
gcloud logging read 'log_id("cloudaudit.googleapis.com/policy") AND protoPayload.metadata.dryRun=true' \
  --limit=5 --freshness=1h \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName,protoPayload.metadata.violationReason)"
```

**What you should see:** the read worked, but a **Policy Denied** audit entry marked `dryRun: true` recorded that, under enforcement, your request from outside the perimeter would have been refused — even though your identity has Owner. That's the stolen-credential scenario, caught at the API layer. ⚠️ If no entry appears, wait a few more minutes and retry; perimeter propagation and log delivery can lag.

*Don't run this in the lab:* `gcloud access-context-manager perimeters dry-run enforce lab11_perimeter --policy=$POLICY` would turn the dry run into enforcement and block your own Cloud Shell access to the bucket.

---

## Part B — AWS (optional): security group vs NACL defaults, and a gateway endpoint

CloudShell, `us-east-1`, as `labadmin`. Uses the default VPC but attaches nothing to running instances.

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query "Vpcs[0].VpcId" --output text)
echo $VPC_ID    # if this prints None, you deleted the default VPC: run 'aws ec2 create-default-vpc' (free) or skip Part B

SG=$(aws ec2 create-security-group --group-name lab11-sg --description "lab11" --vpc-id $VPC_ID --query GroupId --output text)
aws ec2 describe-security-groups --group-ids $SG --query "SecurityGroups[0].{In:IpPermissions,Out:IpPermissionsEgress}"
aws ec2 revoke-security-group-egress --group-id $SG --ip-permissions '[{"IpProtocol":"-1","IpRanges":[{"CidrIp":"0.0.0.0/0"}]}]'

NACL=$(aws ec2 create-network-acl --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=network-acl,Tags=[{Key=lab,Value=11}]' --query NetworkAcl.NetworkAclId --output text)
aws ec2 describe-network-acls --network-acl-ids $NACL --query "NetworkAcls[0].Entries" --output table

RTB=$(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC_ID Name=association.main,Values=true --query "RouteTables[0].RouteTableId" --output text)
VPCE=$(aws ec2 create-vpc-endpoint --vpc-id $VPC_ID --vpc-endpoint-type Gateway \
  --service-name com.amazonaws.us-east-1.s3 --route-table-ids $RTB --query VpcEndpoint.VpcEndpointId --output text)
aws ec2 describe-route-tables --route-table-ids $RTB --query "RouteTables[0].Routes[?GatewayId=='$VPCE']"
aws ec2 describe-vpc-endpoints --vpc-endpoint-ids $VPCE --query "VpcEndpoints[0].PolicyDocument" --output text
```

**What you should see:**

- The new security group has **no inbound** rules and **allow-all outbound** — you then revoked the outbound rule to create a deny-by-default egress SG.
- The custom NACL has only the `*` (rule 32767) **deny** entries in both directions — custom NACLs deny everything until you add rules, and they're stateless.
- The gateway endpoint added a route to an S3 **prefix list** (`pl-…`), and its default endpoint policy allows full access. In a data-perimeter design you'd replace that policy to allow only your organization's buckets (`aws:ResourceOrgID`).

## Part C — Azure (optional): NSG defaults and an ASG

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab11 --location eastus --tags lab=11
az network nsg create -g rg-lab11 -n lab11-nsg --tags lab=11
az network nsg rule list -g rg-lab11 --nsg-name lab11-nsg --include-default \
  --query "[].{name:name,prio:priority,dir:direction,access:access,dest:destinationAddressPrefix}" -o table

az network asg create -g rg-lab11 -n lab11-web --tags lab=11
az network nsg rule create -g rg-lab11 --nsg-name lab11-nsg -n deny-internet-out \
  --priority 4000 --direction Outbound --access Deny --protocol '*' \
  --source-address-prefixes VirtualNetwork --destination-address-prefixes Internet --destination-port-ranges '*'
az network nsg rule list -g rg-lab11 --nsg-name lab11-nsg --include-default -o table
```

**What you should see:** the six default rules, including **`AllowInternetOutBound`** at 65001 — Azure allows outbound internet by default. Your custom `deny-internet-out` at priority 4000 is evaluated first and overrides it. The ASG exists to be referenced in rules (e.g., "allow 443 to `lab11-web`") instead of IPs.

---

## Verify it worked

| Check | Expected |
|---|---|
| Firewall policy rules | 100 allow IAP SSH; 900 allow 199.36.153.8/30:443; 1000 deny all egress |
| `fetch.sh` before PGA | Fails / times out |
| After PGA | Returns the object |
| After egress deny | Fails; succeeds only via `199.36.153.8` |
| Firewall logs | ALLOWED from IAP on 22; DENIED to Google public IPs on 443 |
| (A7) Policy Denied log | `dryRun: true`, your principal, a `violationReason` |
| (B) AWS | SG: no inbound, egress revoked; NACL: `*` deny; S3 prefix-list route |
| (C) Azure | `AllowInternetOutBound` default overridden by priority 4000 deny |

## What to notice (reflection questions)

1. The VM had valid credentials and an IAM grant, yet couldn't read the bucket until you fixed the *network*. Then you broke it again with egress. Which layer would an attacker on this VM have to defeat to exfiltrate to the internet?
2. Why did SSH keep working after you denied all egress?
3. Private Google Access let the VM reach *any* bucket its identity could access — including one in an attacker's project if IAM allowed it. What closes that gap? (Hint: A7.)
4. Compare egress defaults: Google implied allow, AWS SG allow-all outbound, Azure `AllowInternetOutBound`. What does that tell you about where customers' egress risk comes from?
5. Write a plain-English detection for T1562.007 in this project and one for T1537 using VPC-SC logs.

## Cleanup

**Google Cloud**

```bash
gcloud compute instances delete lab11-vm --zone=$ZONE --quiet 2>/dev/null || echo "VM already self-deleted"
gcloud compute network-firewall-policies associations delete --firewall-policy=lab11-policy \
  --name=lab11-assoc --global-firewall-policy
gcloud compute network-firewall-policies delete lab11-policy --global --quiet
gcloud compute networks subnets delete lab11-subnet --region=$REGION --quiet
gcloud compute networks delete lab11-net --quiet
gcloud storage rm --recursive gs://$B
gcloud iam service-accounts delete $SA --quiet
rm -f hello.txt fetch.sh
```

If you did **A7**:

```bash
gcloud access-context-manager perimeters delete lab11_perimeter --policy=$POLICY --quiet
# ONLY if you created the access policy in this lab and nothing else uses it:
# gcloud access-context-manager policies delete $POLICY --quiet
gcloud organizations remove-iam-policy-binding $ORG_ID \
  --member=user:$ME --role=roles/accesscontextmanager.policyAdmin
```

Confirm:

```bash
gcloud compute instances list --filter="labels.lab=11"                       # Listed 0 items
gcloud compute disks list --filter="labels.lab=11"                           # Listed 0 items
gcloud compute network-firewall-policies list --global 2>/dev/null | grep lab11 || echo "no lab11 policy"
gcloud compute networks list --filter="name=lab11-net"                       # Listed 0 items
gcloud storage ls | grep lab11 || echo "no lab11 buckets"
gcloud iam service-accounts list --filter="email:lab11-reader"               # Listed 0 items
```

**AWS**

```bash
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids $VPCE
aws ec2 delete-network-acl --network-acl-id $NACL
aws ec2 delete-security-group --group-id $SG
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC_ID --query "VpcEndpoints[].VpcEndpointId" --output text   # expect empty (unless you had others)
aws ec2 describe-security-groups --filters Name=group-name,Values=lab11-sg --query "SecurityGroups[].GroupId" --output text  # expect empty
```

If CloudShell restarted, find them with `describe-security-groups --filters Name=group-name,Values=lab11-sg`, `describe-network-acls --filters Name=tag:lab,Values=11`, and `describe-vpc-endpoints`.

**Azure**

```bash
az group delete --name rg-lab11 --yes
az group list --query "[?name=='rg-lab11']" -o table      # expect empty
```

**Final check — nothing billable remains:** no `lab11` VM, disk, firewall policy, network, bucket, or service account on Google (and no perimeter or extra org role if you did A7); no `lab11-sg`, NACL, or gateway endpoint on AWS; no `rg-lab11` on Azure. Tomorrow, check Google **Billing → Reports** filtered by `lab=11` and by Networking: expect $0.00.

## Write-up prompt

> On [date] I secured an internal-only Google Cloud VM with a global network firewall policy that allowed only IAP-sourced SSH, demonstrated that the VM could not reach Cloud Storage until Private Google Access was enabled on its subnet, and then implemented deny-by-default egress with a single allow rule to the `private.googleapis.com` range, verifying the effect and reviewing allowed and denied connections in firewall logs. The VM ran as a dedicated service account with read access to one bucket. [Optional: I placed the project in a VPC Service Controls dry-run perimeter restricting Cloud Storage and found the Policy Denied dry-run audit entry for an out-of-perimeter request.] [Optional: I compared AWS security group and NACL defaults, created an S3 gateway endpoint, and overrode Azure's default outbound-internet NSG rule.] I deleted all resources afterward.
