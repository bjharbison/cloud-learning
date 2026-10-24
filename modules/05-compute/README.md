# 05 — Compute: virtual machines, images, instance groups, autoscaling

> **In one sentence:** you'll be able to launch, harden, scale, and reach cloud VMs on all three clouds — without ever opening SSH or RDP to the internet.

**Prereqs:** modules 00–04 · **Time:** ~3.5 hours incl. lab · **Phase:** 2

## Learning objectives

- Explain what a cloud VM is made of: machine type, image, boot disk, network interface, identity.
- Build a fleet from a **template** and let a **managed group** heal and scale it.
- Reach VMs through identity-based access — **OS Login + IAP**, **Session Manager**, **Azure Bastion** — and say why that beats open port 22/3389.
- Explain the VM's **attached identity** and the **metadata server**, and why attackers go straight for them.
- Describe **Shielded/Trusted Launch** and **Confidential** VMs at a concept level, and when a public-sector customer asks for them.

## Why this matters for the target roles

- **Customer engineer / architect:** lift-and-shift migrations land on VMs first (module 31). You'll size them, template them, and explain how they survive a zone failure.
- **Cloud security:** exposed SSH/RDP and over-privileged VM identities are two of the most common root causes in cloud incident reports.
- **CTI:** VMs are where cryptominers run and where stolen metadata credentials come from. Knowing the plumbing lets you read intrusion reports precisely.

---

## Concepts

### What a cloud VM is made of

Module 01 showed the hypervisor underneath. Here's what *you* choose on top:

| Piece | Plain meaning | Google Cloud | AWS | Azure |
|---|---|---|---|---|
| **Machine type** | How many vCPUs and how much RAM | Machine type (e.g., `e2-micro`, `n2-standard-4`) in a **machine series** | Instance type (e.g., `t3.micro`) in a **family** | VM size (e.g., `Standard_B1s`) in a **series** |
| **Image** | The OS disk you start from | Image; **image family** points at the latest | **AMI** | Marketplace image; custom images in **Azure Compute Gallery** |
| **Boot disk** | Block storage holding the OS | Persistent Disk / Hyperdisk | EBS volume | Managed disk |
| **Network interface** | Where it plugs in | VPC subnet; optional external IP | VPC subnet; optional public IP; **security group** | VNet subnet; optional public IP; **NSG** |
| **Identity** | What the VM itself can do in the cloud | Attached **service account** | **Instance profile** (IAM role) | **Managed identity** |
| **Metadata** | Settings and credentials served to the VM | Metadata server | **IMDS** | IMDS |

**Bridge:** this is a Proxmox VM template plus cloud-init, with one addition — the VM itself gets an identity that can call the cloud's APIs. On Proxmox, a VM can't create other VMs. In the cloud, a VM with the wrong identity can.

**Shared-core and burstable types** (Google `e2-micro`, AWS `t3`/`t4g`, Azure B-series) give you a fraction of a CPU with the ability to burst. They're what the free tiers offer, and they're fine for labs, not for steady load.

### Images: the golden image problem

An **image** is a snapshot of a boot disk you can stamp out repeatedly.

- **Public images** come from the provider or OS vendor (Debian, Ubuntu, RHEL, Windows Server).
- **Custom images** are ones you build — patched, hardened, agents installed. This is the **golden image** pattern.
- **Image families** (Google) let templates say "latest Debian 12" instead of a specific build.

Security consequence: an image is software supply chain. Anything baked in — a backdoor, a stale package, an SSH key — ships to every VM. ATT&CK even has a technique for it (T1525, below).


### Instance groups and scale sets

A single VM is a pet. A fleet built from a template is cattle.

1. **Template** — the blueprint: machine type, image, disk, network, labels, identity. Google **instance template**; AWS **launch template**; Azure **scale set model**.
2. **Managed group** — keeps N identical VMs running from that template. Google **managed instance group (MIG)**; AWS **Auto Scaling group**; Azure **Virtual Machine Scale Set**.

What a managed group gives you:

- **Self-healing.** If a VM dies or is deleted, the group recreates it to keep the target size. With an application **health check**, Google calls this **autohealing**.
- **Spreading across zones.** A **regional MIG** spreads VMs over several zones in a region; Azure scale sets can spread across availability zones; AWS Auto Scaling groups span subnets in multiple AZs. This is how you survive the zone failure you simulated in module 02.
- **Rolling updates.** Change the template; the group replaces VMs gradually.
- **Autoscaling.** Add or remove VMs based on a signal.

Microsoft states the scale set itself has no extra charge — you pay for the VMs, disks, and network. ⚠️ Google and AWS were not re-verified this run on group-level charges; in practice you pay for the instances.

Azure detail: scale sets have **Uniform** and **Flexible** orchestration modes, chosen at creation and unchangeable afterwards.

### Autoscaling

**Plain version:** watch a number; add VMs when it's high, remove them when it's low.

- **Signals:** CPU utilization (simplest), load-balancer serving capacity, custom metrics, or schedules. Google's autoscaler supports all four.
- **Min and max.** The max is a cost control (module 04). Autoscaling with no max is an open-ended obligation.
- **Cool-down / initialization period.** New VMs need time to boot before their metrics count.
- **Scale-in surprises.** Autoscalers delete VMs. Anything stored only on a VM's disk is gone. Design stateless.

**Bridge:** this is the closed-loop control you know from OT — a setpoint, a process variable, and a controller with deadband and rate limits so it doesn't oscillate.

### Pricing models for VMs (quick recap)

- **On-demand** — default.
- **Spot** — Google Spot VMs, AWS Spot Instances, Azure Spot VMs: cheap, reclaimable. On Google you can set what happens on preemption (`STOP` or `DELETE`).
- **Commitments** — CUDs, Savings Plans, reservations (module 04).

Gotcha: Google's always-free e2-micro is specifically **non-preemptible**. A Spot e2-micro is *not* covered.

Google also has a handy lab safety net: **`--max-run-duration`** with `--instance-termination-action=DELETE` makes a VM delete itself after a set time.

---

### Getting in safely: no open SSH or RDP

Module 01 reached a VM through **IAP** instead of an open port. This is the full pattern on all three clouds.

**Why open ports are bad:** a VM with port 22 or 3389 open to `0.0.0.0/0` gets scanned within minutes and brute-forced continuously. One weak password, one leaked key, or one unpatched SSH/RDP bug becomes a breach. It also bypasses your identity provider — no MFA, no central revocation.

**The safer pattern:** no public IP on the VM, no inbound admin port from the internet, and a provider-run broker that checks your cloud identity first.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Broker | **IAP TCP forwarding** | **Systems Manager Session Manager** | **Azure Bastion** |
| How traffic gets in | You tunnel through IAP; firewall allows only IAP's range `35.235.240.0/20` on port 22 | An agent on the VM connects **outbound** to Systems Manager; **no inbound ports at all** | Bastion connects to the VM's private IP inside the VNet |
| Who decides access | IAM (`roles/iap.tunnelResourceAccessor` for the tunnel) | IAM policies for `ssm:StartSession` | Azure RBAC on the VM and Bastion |
| Who you are on the VM | **OS Login**: your Linux account is tied to your Google identity; IAM roles (`roles/compute.osLogin` or `roles/compute.osAdminLogin`) decide login and sudo | Session runs as an OS user mapped by Session Manager | Local or Entra ID-based login |
| Requirements | Firewall rule for the IAP range; OS Login enabled with metadata `enable-oslogin=TRUE` | SSM Agent (included on Amazon Linux 2023), an instance profile allowing Systems Manager, and outbound connectivity (or VPC endpoints) | A Bastion deployment in the VNet |
| Session logging | Cloud Audit Logs record IAP and OS Login activity (module 18) | Session activity to CloudTrail, S3, or CloudWatch Logs (not for port forwarding or SSH sessions) | Premium SKU adds session recording |
| Cheapest lab option | Free | Free to use; you pay for the instance and any logging | **Developer SKU: free**, dev/test only, one connection at a time, portal-only, limited regions, no VNet peering |

**OS Login vs metadata SSH keys:** without OS Login, Google VMs accept SSH keys stored in project or instance metadata. Those keys outlive the people who added them. OS Login ties access to IAM, so removing someone's role removes their access everywhere. Google's best-practice guidance is to use OS Login and enforce it with organization policy.

**Bridge to your intel background:** this is the difference between a door with a cipher lock whose code everyone learned years ago, and a badge reader tied to the current access roster. Session Manager is the version where the door doesn't exist on the outside at all.

> **Shared responsibility:** the provider builds IAP, Session Manager, and Bastion. **Whether port 22/3389 is open, to whom, and which identities can start a session is always the customer's decision.**

### The VM's own identity and the metadata server

Every VM can carry an identity. Code on the VM fetches short-lived credentials for it from the **metadata server** at a link-local address (`169.254.169.254`; Google also answers at `metadata.google.internal`).

Why this is a big deal:

- **Google:** if you don't pick a service account, VMs can use the **Compute Engine default service account**. Depending on org policy, it may have the broad **Editor** role (Google turns off that automatic grant by default for organizations created after May 3, 2024). **If your lab project sits under "No organization" (module 03), assume its default service account has Editor.** Google recommends a user-managed service account with only the permissions the workload needs — or none at all (`--no-service-account --no-scopes`). Google also notes that **anyone who can log in to a VM can use its service account's permissions.**
- **AWS:** **IMDSv2** requires a session token before the metadata service answers, which blocks the classic **SSRF** trick of tricking a web app into fetching credentials. Amazon Linux 2023 uses IMDSv2 by default; you can require it per instance (`HttpTokens=required`).
- **Azure:** **managed identities** get tokens from Azure's IMDS; give them the narrowest role assignment that works.

**Bridge:** the VM's identity is a standing delegation of authority. If the delegation is "Editor on the whole project," anyone who gets a shell on that VM inherits it.

### Shielded and confidential VMs

**Shielded VM** (Google) / **Trusted Launch** (Azure) / **NitroTPM + UEFI Secure Boot** (AWS) protect the boot chain:

- **Secure Boot** — only signed bootloaders and kernels run.
- **vTPM** — a virtual TPM for measured boot and keys.
- **Integrity monitoring** — compare boot measurements to a known-good baseline.

Azure says Trusted Launch is the default for new Gen2 VMs created in the portal, CLI, or PowerShell, at no extra cost. You enabled Shielded VM's Secure Boot in module 01.

**Confidential VMs** go further: memory is encrypted with keys the hypervisor can't read, and the VM can produce a hardware-signed **attestation** of its state.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Technologies | AMD SEV, AMD SEV-SNP, Intel TDX | AMD SEV-SNP | AMD SEV-SNP, Intel TDX |
| Example series | N2D (SEV, SEV-SNP), C3 and C4 (TDX), C2D/C3D/C4D (SEV) | m6a, c6a, r6a | DCasv5/v6, ECasv5/v6, DCesv6, ECesv6 |
| Notes | Not available on E2 | Shared tenancy only in some Regions; extra hourly fee of 10% of On-Demand | Optional confidential OS disk encryption bound to the vTPM |

**When a public-sector customer asks:** confidential computing addresses "what if the cloud operator or a compromised host could read memory?" It's increasingly part of sovereignty and data-in-use conversations (module 16, 27). It doesn't fix a weak IAM policy.

---

## Text diagram

```
             YOU (Cloud Shell / browser)
                 │  identity + MFA checked first
   ┌─────────────┼───────────────────────────────┬──────────────────────────────┐
   ▼ Google                                       ▼ AWS                          ▼ Azure
 IAP TCP forwarding (35.235.240.0/20)      Session Manager ◄── outbound ──┐   Azure Bastion (in VNet)
   │ firewall: allow 22 from IAP only         ▲ (no inbound ports)       │      │ private IP
   ▼                                          │                          │      ▼
 ┌─ Regional MIG (instance template) ─┐   ┌─ Auto Scaling group ─┐       │   ┌─ Scale set ─┐
 │ zone a: VM   zone b: VM            │   │ AZ1: EC2  AZ2: EC2   │───────┘   │ zone1 zone2 │
 │ no external IP · OS Login · Shielded│   │ instance profile     │           │ managed id  │
 │ SA: none / least privilege          │   │ IMDSv2 required      │           │ Trusted Launch│
 └──────────── autoscaler (min/max) ───┘   └── scaling policy ────┘           └─ autoscale ──┘
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| VM service | Compute Engine | EC2 | Azure Virtual Machines | |
| Free-tier VM | 1 non-preemptible `e2-micro`/month in us-west1, us-central1, us-east1 (hours pooled across instances) + 30 GB-month standard PD | Free plan (since July 2025): eligible types include `t3.micro`, `t3.small`, `t4g.micro`, `t4g.small`, `c7i-flex.large`, `m7i-flex.large`; usage draws on plan credits ⚠️ hour allowances not verified | 12 months: B1s, B2pts v2, B2ats v2, up to 750 hours/month in any combination of instances (⚠️ whether the three sizes share one pool isn't stated) | AWS's new plan works differently from the old "750 hours of t2.micro" |
| Blueprint | Instance template | Launch template | Scale set model | |
| Managed fleet | Managed instance group (zonal or regional) | Auto Scaling group | Virtual Machine Scale Set (Uniform/Flexible) | Azure's mode can't be changed later |
| Identity-based admin access | OS Login + IAP TCP forwarding | Session Manager | Azure Bastion | Only Session Manager needs no inbound network path at all |
| VM identity | Service account | Instance profile (IAM role) | Managed identity | Google's default SA may carry Editor |
| Metadata hardening | Metadata server requires `Metadata-Flavor: Google` header ⚠️ not re-verified this run | IMDSv2 tokens (default on AL2023) | IMDS | AWS's IMDSv2 is the most-discussed SSRF mitigation |
| Boot integrity | Shielded VM | NitroTPM / UEFI Secure Boot | Trusted Launch (default for new Gen2 VMs) | |
| Confidential VM | SEV, SEV-SNP, TDX | SEV-SNP | SEV-SNP, TDX | AWS charges a 10% uplift on shared tenancy |

## Administer and monitor it

- **Inventory:** `gcloud compute instances list`; `aws ec2 describe-instances`; `az vm list`. Filter by label `lab=05`.
- **Serial console** for boot problems (all three have one; restrict who can use it — it's another way in).
- **Patching:** Google VM Manager, AWS Systems Manager Patch Manager, Azure Update Manager (⚠️ product names not re-verified this run).
- **Logs:** VM creation, metadata changes, firewall changes, and IAP/OS Login/Session Manager sessions are control-plane events in Cloud Audit Logs, CloudTrail, and the Azure Activity Log (module 18). Guest OS logs need an agent.
- **Metrics:** CPU, disk, and network are collected by default; memory usually needs an agent (module 19).

## Security angle

Most common VM misconfigurations:

1. **SSH/RDP open to `0.0.0.0/0`.** Use IAP / Session Manager / Bastion. Remove the `default` network's permissive rules (module 11).
2. **Public IPs on VMs that don't need them.** Use private IPs and a load balancer or NAT.
3. **Over-privileged VM identity** — the default service account with Editor, or an instance profile with `AdministratorAccess`. One SSRF or shell = cloud-wide compromise.
4. **Metadata SSH keys or local passwords** that outlive their owners. Use OS Login / central identity.
5. **Unpatched golden images.** Rebuild images on a schedule; scan them.
6. **IMDSv1 left enabled on AWS.** Require IMDSv2.

**Shared responsibility:** the provider secures the hypervisor and host (module 01). **The guest OS, its patches, the image, the firewall rules, the admin access path, and the VM's identity are all the customer's.** That's IaaS.

## Threat intel angle

- **T1552.005 Unsecured Credentials: Cloud Instance Metadata API** — steal the VM's credentials from the metadata service, often via SSRF. The reason IMDSv2 and least-privilege VM identities exist.
- **T1098.004 Account Manipulation: SSH Authorized Keys** — add a key for persistence; on Google, writing to project metadata reaches every VM that accepts metadata keys. OS Login closes that.
- **T1578.002 Create Cloud Instance** — spin up attacker-controlled VMs (often for mining, T1496.001) or to stage data.
- **T1525 Implant Internal Image** — backdoor a golden image so every future VM is compromised.
- **T1651 Cloud Administration Command** — use the provider's management agent (e.g., Systems Manager Run Command) to execute on VMs without SSH. The same agent that removes open ports can be abused by a stolen admin identity.

**Bridge to your targeting background:** the VM's metadata service is a high-value node — one hop from an internet-facing app to cloud credentials. Defenders harden the node (IMDSv2, least privilege); attackers look for the edge (SSRF) that reaches it.

## Public sector notes

- **Hardened images** are a common requirement: CIS benchmark images and DISA STIG-aligned builds show up in agency standards (⚠️ specific marketplace offerings not verified this run). Golden-image pipelines are part of the ATO evidence story.
- **No-inbound admin access** maps cleanly to zero-trust expectations (module 17): identity-checked, logged, no exposed management ports.
- **Confidential VMs and sole-tenant/dedicated hosts** come up when customers ask "is this hardware shared?" The honest answer depends on the offering and impact level (modules 26–27).
- **Azure Bastion Developer** is dev/test only; production and regulated deployments use the paid SKUs.

## Key takeaways

- A VM = machine type + image + disk + network + **identity**. The identity is the part people forget.
- Templates plus managed groups (MIG / Auto Scaling group / scale set) give self-healing, zone spreading, rolling updates, and autoscaling. Always set a **max**.
- **Never open SSH/RDP to the internet.** Use OS Login + IAP, Session Manager, or Azure Bastion.
- Lock down the metadata path: least-privilege VM identities, IMDSv2 on AWS.
- Shielded/Trusted Launch protects boot; Confidential VMs protect memory in use.
- The guest OS, image, firewall, admin path, and VM identity are **always the customer's**.

## Sources

- [Google Cloud — Free cloud features (Compute Engine free tier)](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Google Cloud — Instance groups](https://docs.cloud.google.com/compute/docs/instance-groups)
- [Google Cloud — Autoscaling groups of instances](https://docs.cloud.google.com/compute/docs/autoscaler)
- [Google Cloud — About OS Login](https://docs.cloud.google.com/compute/docs/oslogin) and [Enable OS Login sample (`enable-oslogin`)](https://docs.cloud.google.com/compute/docs/samples/compute-project-for-oslogin-example)
- [Google Cloud — Best practices for controlling SSH login access](https://docs.cloud.google.com/compute/docs/connect/ssh-best-practices/login-access)
- [Google Cloud — Compute Engine service accounts](https://docs.cloud.google.com/compute/docs/access/service-accounts)
- [Google Cloud — Confidential VM supported configurations](https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations)
- [Google Cloud — `gcloud compute instances create` reference (Spot, Shielded, max-run-duration flags)](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/create)
- [AWS — Track your Free Tier usage for Amazon EC2 (eligible instance types)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
- [AWS — Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [AWS — Verify or add instance permissions for Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started-instance-profile.html)
- [AWS News Blog — IMDSv2 by default (2023)](https://aws.amazon.com/blogs/aws/amazon-ec2-instance-metadata-service-imdsv2-by-default/)
- [AWS — Requirements for UEFI Secure Boot on EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/launch-instance-with-uefi-sb.html) and [NitroTPM requirements](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/enable-nitrotpm-prerequisites.html)
- [AWS — AMD SEV-SNP for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/sev-snp.html)
- [AWS — Create your first Auto Scaling group](https://docs.aws.amazon.com/autoscaling/ec2/userguide/create-your-first-auto-scaling-group.html)
- [Microsoft — Create free services with an Azure free account](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/create-free-services)
- [Microsoft — Azure Bastion SKU comparison](https://learn.microsoft.com/en-us/azure/bastion/bastion-sku-comparison)
- [Microsoft — Virtual Machine Scale Sets overview](https://learn.microsoft.com/en-us/azure/virtual-machine-scale-sets/overview)
- [Microsoft — Trusted Launch for Azure VMs](https://learn.microsoft.com/en-us/azure/virtual-machines/trusted-launch)
- [Microsoft — About Azure confidential VMs](https://learn.microsoft.com/en-us/azure/confidential-computing/confidential-vm-overview)
- [MITRE ATT&CK — Cloud IaaS matrix](https://attack.mitre.org/matrices/enterprise/cloud/iaas/) (T1552.005, T1098.004, T1578.002, T1525, T1651)

Verified: 2026-10-24
