# 01 — What the cloud is: NIST 800-145, virtualization, IaaS/PaaS/SaaS, shared responsibility

> **In one sentence:** you'll be able to explain what's physically and logically underneath a cloud VM or container — and draw the line, without hesitation, between what the provider secures and what the customer always owns.

**Prereqs:** module 00 · **Time:** ~3 hours incl. lab · **Phase:** 1

## Learning objectives

- Recite NIST's definition (5 / 3 / 4) and use it in a customer conversation.
- Explain hypervisors, VMs, and containers, and where the isolation boundary sits for each.
- Name the custom hardware each hyperscaler uses for isolation and offload: Google **Titan / Titanium**, AWS **Nitro**, Azure **Boost / Cerberus**.
- Place any service on the IaaS → PaaS → SaaS "sliding line" and state who owns each layer.
- State, every time, that **identity, firewall rules, VPN configuration, and SSH/RDP access are the customer's** — in every model.

## Why this matters for the target roles

- **Customer engineer:** "How do I know your hypervisor keeps my workload away from other tenants?" is a standard public-sector question. You need a crisp answer.
- **Cloud security:** most cloud incidents are customer-side misconfigurations, not provider failures. Shared responsibility tells you where to look first.
- **CTI:** container escapes and identity abuse are where real adversary tradecraft lives. Provider-hypervisor escapes are rare and high-value.

---

## Part 1 — Consolidation (you covered this in tutoring)

Short reference versions. Skim, then move on to Part 2.

### NIST SP 800-145 in one table

NIST published **SP 800-145, "The NIST Definition of Cloud Computing,"** in September 2011. It defines cloud as **5 essential characteristics, 3 service models, 4 deployment models.**

| 5 characteristics | 3 service models | 4 deployment models |
|---|---|---|
| On-demand self-service | IaaS | Private |
| Broad network access | PaaS | Community |
| Resource pooling (multi-tenant) | SaaS | Public |
| Rapid elasticity | | Hybrid |
| Measured service | | |

**Interview use:** if a customer calls a virtualized data center with a ticketing queue "our private cloud," ask about self-service and elasticity. No self-service, no cloud — by the government's own definition.

### CapEx → OpEx, and the appropriations tension

Cloud turns big up-front purchases (**CapEx**) into metered monthly spend (**OpEx**). Commercial buyers like the flexibility. Government buyers hit a wall: appropriations are fixed amounts for fixed periods, and an elastic bill doesn't fit neatly. Module 04 covers how agencies manage this (commitments, budgets, contract vehicles). For now: **elasticity is a feature for engineers and a risk for comptrollers.**

### The sliding line

```
              On-prem    IaaS       PaaS       SaaS
Data           YOU       YOU        YOU        YOU      ◄─ always yours
Identity/access YOU      YOU        YOU        YOU      ◄─ always yours
Application    YOU       YOU        YOU        provider
Runtime/middleware YOU   YOU        provider   provider
Guest OS       YOU       YOU        provider   provider
Virtualization YOU       provider   provider   provider
Hardware/DC    YOU       provider   provider   provider
```

As you move right, the provider takes more layers. **Two rows never move:** your data and who can access it.

---

## Part 2 — What's new: what's actually underneath

### Hypervisors

A **hypervisor** is software (sometimes with hardware help) that lets one physical server run many isolated virtual machines.

- **Type 1 (bare-metal):** runs directly on the hardware. Every hyperscaler uses this kind.
- **Type 2 (hosted):** runs as an app on a normal OS (VirtualBox on a laptop).

**Bridge:** your Proxmox cluster is a Type 1 setup. Proxmox VE runs VMs on **KVM** (the Linux kernel's built-in hypervisor) and containers on **LXC**. You already run both models covered below.

What each cloud runs:

| Cloud | Hypervisor basis | What's notable |
|---|---|---|
| Google Cloud | **KVM**-based | Google wrote its own virtual machine monitor instead of using QEMU, cutting attack surface. Google's public description of this dates to 2017; details may have evolved. |
| AWS | **Nitro Hypervisor** | Deliberately minimal: no networking stack, no general-purpose file system, no shell, no interactive access mode. I/O is pushed onto Nitro Cards. |
| Azure | **Hyper-V**-based | A root partition runs the host OS with device access; guest VMs get virtual devices. Microsoft runs a Hyper-V bug bounty. |

**Practitioner vocabulary:**

- **Multi-tenancy** — many customers' workloads on shared hardware. This is NIST's "resource pooling."
- **Noisy neighbor** — one tenant's load affecting another's performance. A fairness problem, not a security breach.
- **VM escape** — code in a guest breaking out to the hypervisor or host. Rare in public reporting, and devastating if it happens; it's the provider's job to prevent.

### VMs vs containers

The plain version:

- A **VM** virtualizes **hardware**. Each VM boots its own kernel.
- A **container** virtualizes the **operating system**. All containers on a host share one kernel; Linux **namespaces** (what you can see) and **cgroups** (what you can use) keep them apart.

```
   VMs                                   Containers
┌────────┐┌────────┐               ┌──────┐┌──────┐┌──────┐
│ App A  ││ App B  │               │App A ││App B ││App C │
│ Libs   ││ Libs   │               │Libs  ││Libs  ││Libs  │
│ Kernel ││ Kernel │ ◄ own kernel  └──────┘└──────┘└──────┘
└────────┘└────────┘               ┌──────────────────────┐
┌──────────────────┐               │ Container runtime     │
│   Hypervisor     │ ◄ boundary    │ ONE shared host kernel│ ◄ boundary
└──────────────────┘               └──────────────────────┘
      Hardware                             (VM or) hardware
```

| | VM | Container |
|---|---|---|
| Starts in | Tens of seconds | About a second |
| Isolation boundary | Hypervisor (small, hardened, hardware-assisted) | Shared kernel (large attack surface) |
| Unit of patching | Guest OS + app | Image (rebuild and redeploy) |
| Typical cloud use | Lift-and-shift, legacy apps, full OS control | Microservices, CI/CD, Kubernetes |

**Bridge from your homelab:** on Proxmox, a KVM VM and an LXC container side by side show exactly this. Run `uname -r` in each: the LXC container reports the *host's* kernel. In your Docker stack (MQTT, InfluxDB, Grafana), every container shares the Docker host's kernel too.

**Key point for interviews:** in the cloud, multi-tenant isolation between *customers* is almost always a **VM boundary** (or hardware). With managed Kubernetes (GKE, EKS, AKS), the worker nodes that run your containers are VMs in your own project, account, or subscription; serverless container platforms add their own sandboxing layers (module 07). Containers are a packaging and density tool; they're not, by default, a strong security boundary.

### What's physically inside a hyperscaler

A cloud region is buildings full of standardized servers, top-of-rack switches, and a private backbone (module 02). What's different from your rack is **custom silicon** that does two jobs:

1. **Root of trust:** a chip that checks the server's firmware *before* the main CPU runs anything, so a tampered server won't boot.
2. **Offload:** dedicated cards that handle networking, storage, encryption, and management *off* the main CPU. This frees CPU for customers and moves the provider's control software out of reach of tenant code.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Umbrella name | **Titanium** (hardware security architecture) | **Nitro System** | **Azure Boost** (offload) |
| Root of trust | **Titan** chip (holds the CPU in reset, verifies boot firmware, then releases it); **Caliptra** root of trust for measurement in CPUs/GPUs/TPUs | **Nitro Controller** card (hardware root of trust) + **Nitro Security Chip** on the main board (mediates firmware access) | **Cerberus** chip (independent hardware root of trust) |
| Offload | **Titanium Offload Processors (TOPs)** — encryption in transit/at rest, deprivileging host components | **Nitro Cards** — VPC networking, EBS storage, instance storage, management | **Azure Boost** — MANA network adapter; storage on an FPGA exposed to VMs as NVMe |
| Extra | Open-source pieces (OpenTitan) | Encryption keys for EBS/instance storage/VPC described as inaccessible to AWS operators | **Azure Integrated HSM** — FIPS 140-3 Level 3 key cache on new servers (select VM sizes, opt-in) |

**What to take from this:** all three made the same architectural bet — **shrink the hypervisor, move control and I/O onto separate hardware, verify boot from silicon up.** The names differ; the pattern doesn't.

**Bridge to your OT/ICS background:** it's the same idea as separating a safety instrumented system from the basic process control system. The thing that enforces safety isn't running on the box it's protecting.

**Honesty note:** these are vendor descriptions of their own systems. You can cite them; you can't independently verify them. In an interview, say "Google documents…" or "AWS states…", not "it's impossible to…".

---

## Part 3 — Shared responsibility, hammered

### The model in each cloud's words

- **AWS:** "security **of** the cloud" (AWS: hardware, software, networking, facilities) vs "security **in** the cloud" (customer). Customer items AWS lists include the guest OS and its patches, installed software, **the configuration of security groups (the firewall)**, data, and **using IAM to set permissions**.
- **Azure:** whatever the model, the customer always keeps **data, endpoints, accounts, and access management**. Microsoft's responsibility matrix marks **customer data, configurations and settings, and identities and users** as the customer's even in SaaS.
- **Google Cloud:** uses shared responsibility and adds **"shared fate"** — Google's framing that the provider should actively help customers be secure (secure defaults, blueprints, guidance), not just draw a line. It doesn't move the line.

### The correction — memorize this

You've needed this twice, so here it is as a rule:

> **Identity, access control, firewall rules, VPN configuration, and SSH/RDP access are ALWAYS the customer's responsibility. IaaS, PaaS, or SaaS. Every cloud.**

Why the confusion happens: the provider **builds** the firewall, the VPN gateway, the IAM system, and the MFA feature. That's "of the cloud." But **configuring** them — which ports, which peers, which users, which roles — is "in the cloud." The provider sells you a lock; you decide who gets keys.

| Item | Who builds the capability | Who configures it |
|---|---|---|
| Firewall / security groups / NSGs | Provider | **Customer** |
| VPN gateway | Provider | **Customer** (peers, keys, routes, ciphers) |
| IAM roles and MFA | Provider | **Customer** (who gets what; MFA enforcement) |
| SSH/RDP access path | Provider (IAP, Session Manager, Bastion) | **Customer** (whether port 22/3389 is open, and to whom) |
| Physical security, hypervisor, host firmware | Provider | Provider |

**Bridge:** in your OPNsense box, Deciso wrote the firewall software. Nobody would say Deciso is responsible for the rule you wrote allowing `any → any`.

---

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Hypervisor | KVM-based, custom VMM | Nitro Hypervisor (minimal) | Hyper-V-based | AWS documents the most stripped-down hypervisor feature list |
| Hardware root of trust | Titan; Caliptra | Nitro Controller + Nitro Security Chip | Cerberus | All verify firmware before boot |
| Offload system | Titanium (TOPs) | Nitro Cards | Azure Boost | Same pattern, different names |
| VM service | Compute Engine | Amazon EC2 | Azure Virtual Machines | Module 05 |
| Managed containers | GKE, Cloud Run | EKS, ECS, Fargate | AKS, Container Apps | Modules 06–07 |
| Shared-responsibility framing | Shared responsibility + **shared fate** | Security **of** vs **in** the cloud | Responsibility matrix by model; customer always keeps data, endpoints, accounts, access | Google's "shared fate" is a posture, not a contractual shift |

## Administer and monitor it

- **Know which hypervisor generation you're on:** on AWS, `aws ec2 describe-instance-types` returns a `Hypervisor` field (`nitro` or `xen`). Older Xen-based instance types still exist.
- **Inside a VM:** `systemd-detect-virt` and `/sys/class/dmi/id/product_name` tell you what you're running on — useful in forensics (module 23).
- **Where your responsibilities show up in logs:** firewall and IAM changes appear in Cloud Audit Logs / CloudTrail / Azure Activity Log (module 18). Physical and hypervisor events do not — that's the provider's side, attested through compliance reports instead (module 26).

## Security angle

Common customer-side failures, mapped to the sliding line:

- **IaaS:** unpatched guest OS; SSH/RDP open to `0.0.0.0/0`; overly broad IAM roles.
- **PaaS:** public endpoints with no auth; secrets in environment variables; over-permissioned service identities.
- **SaaS:** no MFA; over-shared data; stale accounts.

Notice the common thread: **identity and exposure configuration.** None are provider failures.

Containers add one more: **privileged containers** and host mounts (e.g., mounting the Docker socket) collapse the namespace boundary.

## Threat intel angle

- **T1611 Escape to Host** — breaking out of a container to the underlying host. Realistic in misconfigured Kubernetes, and a key reason providers keep a VM or sandbox boundary between tenants.
- **T1078.004 Valid Accounts: Cloud Accounts** — the common path in. Attackers rarely beat the hypervisor; they log in.
- **T1496.001 Compute Hijacking** — crypto-mining on stolen compute, often via exposed container APIs or stolen keys.
- **Provider-side hypervisor escapes** are high-value and rare in public reporting. When they occur, they're typically handled through coordinated disclosure and bug bounties. As an analyst, weight your collection toward identity and misconfiguration, where the volume is.

**Bridge to your targeting background:** the adversary picks the softest point on the path to the objective. In cloud, that's almost never the silicon; it's a person's credentials or a permissive rule.

## Public sector notes

- **NIST 800-145** is the shared vocabulary in federal procurement and FedRAMP conversations. Using it signals you speak the customer's language.
- Hardware isolation is a real factor in higher-sensitivity authorizations (module 26–27). Expect questions like "is this dedicated hardware?" — the honest answer depends on the offering and impact level.
- **Shared responsibility shows up in ATO packages** as inherited, shared, and customer-specific controls. AWS uses exactly this language: physical/environmental controls are inherited; patch and configuration management are shared.

## Key takeaways

- NIST 800-145: 5 characteristics, 3 service models, 4 deployment models (Sept 2011). Self-service + elasticity separate "cloud" from "virtualized data center."
- VMs isolate at the hypervisor; containers share a kernel. Tenant-to-tenant isolation in public cloud rests on the VM/hardware boundary.
- All three hyperscalers shrink the hypervisor and move I/O and control onto custom hardware with a silicon root of trust: **Titanium/Titan**, **Nitro**, **Azure Boost/Cerberus**.
- The provider **builds** firewalls, VPN gateways, and IAM; the customer **configures** them.
- **Identity, access control, firewall rules, VPN configuration, and SSH/RDP access are always the customer's.**
- Attackers rarely beat the hypervisor; they log in or walk through an open port.

## Sources

- [NIST SP 800-145 — The NIST Definition of Cloud Computing](https://csrc.nist.gov/pubs/sp/800/145/final)
- [Google Cloud — Titanium hardware security architecture](https://docs.cloud.google.com/docs/security/titanium-hardware-security-architecture)
- [Google Cloud — Titan hardware chip](https://docs.cloud.google.com/docs/security/titan-hardware-chip)
- [Google Cloud Blog — 7 ways we harden our KVM hypervisor (2017)](https://cloud.google.com/blog/products/gcp/7-ways-we-harden-our-kvm-hypervisor-at-google-cloud-security-in-plaintext)
- [Google Cloud — Shared responsibilities and shared fate](https://docs.cloud.google.com/architecture/framework/security/shared-responsibility-shared-fate)
- [AWS — The components of the Nitro System (whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/security-design-of-aws-nitro-system/the-components-of-the-nitro-system.html)
- [AWS — Shared responsibility model](https://aws.amazon.com/compliance/shared-responsibility-model/)
- [AWS — EC2 InstanceTypeInfo (Hypervisor field)](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceTypeInfo.html)
- [Microsoft — Azure Boost overview](https://learn.microsoft.com/en-us/azure/azure-boost/overview)
- [Microsoft — Azure Integrated HSM overview](https://learn.microsoft.com/en-us/azure/security/fundamentals/azure-integrated-hardware-security-module-overview)
- [Microsoft — Azure hypervisor security](https://learn.microsoft.com/en-us/azure/security/fundamentals/hypervisor)
- [Microsoft — Shared responsibility in the cloud](https://learn.microsoft.com/en-us/azure/security/fundamentals/shared-responsibility)
- [MITRE ATT&CK — T1611 Escape to Host](https://attack.mitre.org/techniques/T1611/), [T1078.004](https://attack.mitre.org/techniques/T1078/004/), [T1496.001](https://attack.mitre.org/techniques/T1496/001/)

Verified: 2026-10-23
