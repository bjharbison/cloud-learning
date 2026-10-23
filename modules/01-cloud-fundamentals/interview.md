# 01 Interview Prep — Cloud fundamentals

## Likely questions

### Q1. "Explain the shared responsibility model to me."

**Answer outline:**
- Provider secures the cloud itself: facilities, hardware, hypervisor, global network.
- Customer secures what they put in it; the split shifts with IaaS → PaaS → SaaS.
- Two things never move: **data** and **identity/access**. Firewall rules, VPN configuration, and SSH/RDP exposure are the customer's in every model.
- Use the words each provider uses: AWS "of vs in"; Azure's matrix (customer always keeps data, endpoints, accounts, access management); Google "shared fate."

**Strong signal:** the distinction "provider builds the control; customer configures it," with a concrete example (security groups).
**Avoid:** "In PaaS the provider handles security." That's the error customers make before an incident.

### Q2. "What's the difference between a VM and a container? Which is more secure?"

**Answer outline:**
- VM virtualizes hardware, own kernel, hypervisor boundary. Container virtualizes the OS, shared kernel, namespaces + cgroups.
- VMs are the stronger isolation boundary; containers win on speed and density.
- In practice: containers run *inside* VMs in the cloud, so you get both — package with containers, isolate tenants with VMs.
- Real-world container risk is misconfiguration (privileged containers, host mounts) → T1611.

**Strong signal:** "more secure for what threat?" framing.

### Q3. "How does Google (or AWS, or Azure) keep tenants isolated on shared hardware?"

**Answer outline:**
- Minimal hypervisor (Google: KVM-based with a custom VMM; AWS: Nitro Hypervisor; Azure: Hyper-V-based).
- Silicon root of trust verifies firmware before boot (Titan / Nitro Controller + Security Chip / Cerberus).
- Offload cards take networking, storage, encryption, and management off the host CPU (Titanium TOPs / Nitro Cards / Azure Boost).
- Backed by third-party audits and authorizations (module 26).

**Strong signal:** naming the components accurately for the cloud you're interviewing with, and saying "Google documents…" rather than overclaiming.
**Avoid:** "It's impossible to break out."

### Q4. "A customer says they already have a private cloud. How do you respond?"

**Answer outline:**
- Use NIST 800-145 without being condescending: ask about self-service, elasticity, measured service.
- Find where they want to be (speed? cost visibility? resilience?) and map the gap.
- Hybrid is a legitimate model; the goal is the mission outcome, not a label.

### Q5. "Why would a government customer care about the hardware underneath?"

**Answer outline:**
- Higher-impact authorizations and mission data raise questions about supply chain, firmware integrity, and operator access.
- Hardware roots of trust and offload designs are part of the provider's answer; documentation and audits are the evidence.
- Some workloads need dedicated or disconnected options (modules 27–28).

## 60-second executive explanation

"The cloud is someone else's data center, run as a utility you can switch on in minutes and pay for by the hour. Under the hood, each physical server is split into many virtual machines, and the big providers have built custom chips to keep those machines walled off from each other and from the provider's own operators. That part — the buildings, hardware, and isolation — is the provider's job. Ours is everything we put on top: who can log in, which doors are open to the network, how our connections are set up, and how our data is protected. Most cloud breaches don't come from the provider's side; they come from a stolen password or a door left open. So our security plan starts with identity and network exposure, and that's where we'll focus first."

## Whiteboard prompt

Draw the sliding line (on-prem → IaaS → PaaS → SaaS) with the seven layers. Shade provider vs customer. Then draw a VM stack next to a container stack and mark the isolation boundary on each. Finally, circle the four things that are always the customer's: identity/access, firewall rules, VPN configuration, SSH/RDP access (plus data).

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud fundamentals — NIST 800-145, virtualization, VMs vs containers, the custom isolation hardware at Google, AWS, and Azure, and the shared responsibility model — and can explain them to technical and non-technical audiences."
- **After completing the lab:** "In a personal Google Cloud lab, I deployed a VM with no public IP and accessed it only through Identity-Aware Proxy, and compared kernel sharing between a container and a VM." Your existing homelab experience with Proxmox (KVM/LXC) and Docker is real and claimable on its own.
- **Still requires (cert / production experience / clearance):** operating production workloads, assessing a provider's isolation for an ATO, or advising on hardware assurance for classified systems. Don't claim cloud architecture experience from this module; a Google Cloud Digital Leader or Associate Cloud Engineer cert is the claimable next step.
