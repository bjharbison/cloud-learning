# 11 — Network security controls: firewall rules, security groups, NACLs, NSGs, private access, and data-exfiltration perimeters

> **In one sentence:** you'll be able to design layered network controls on all three clouds — from per-VM firewall rules to org-wide policies — keep workloads off the internet while still reaching cloud APIs, and explain to an agency why VPC Service Controls is a different kind of control from a firewall.

**Prereqs:** modules 00–10 (module 10 for VPCs and routes; module 05 for IAP; module 08 for buckets) · **Time:** ~4 hours incl. lab · **Phase:** 3

## Learning objectives

- Compare Google **VPC firewall rules** and **firewall policies**, AWS **security groups** and **NACLs**, and Azure **NSGs** — stateful vs stateless, allow vs deny, where each attaches.
- Explain **hierarchical** (org-level) network policy on each cloud and why central teams want it.
- Give private workloads access to provider APIs without the internet: **Private Google Access**, **Private Service Connect**, AWS **gateway/interface endpoints (PrivateLink)**, Azure **Private Endpoints**.
- Design **egress control** — the control most designs forget.
- Explain **VPC Service Controls** as a data-exfiltration boundary around Google APIs, and its AWS and Azure counterparts.

## Why this matters for the target roles

- **Customer engineer / architect:** "How do we keep our data from leaving?" is the question behind most agency security reviews. VPC Service Controls is one of Google Cloud's clearest public-sector differentiators; you need to explain it without overselling it.
- **Cloud security:** firewall misconfigurations remain a leading root cause of cloud exposure, and they're entirely the customer's.
- **CTI:** adversaries open firewall paths (T1562.007) and move data to accounts they control (T1537). Perimeter controls and their logs are where you catch that.

---

## Concepts

### The layers, from your homelab outward

On OPNsense you had one place for rules: per-interface firewall rules on the router. Cloud networks give you several layers, each enforced in the SDN at the VM's virtual NIC — not at a central box:

```
 Org-wide policy (central security team)        ← hierarchical firewall policy / AVNM security admin rules / Firewall Manager
   Network-wide policy (network team)           ← network firewall policy / NACL (subnet) / NSG on subnet
     Per-workload rules (app team)              ← VPC firewall rules by tag or SA / security groups / NSG on NIC + ASGs
       API-level perimeter (data boundary)      ← VPC Service Controls / data perimeter policies / network security perimeter
         Identity (who, regardless of network)  ← IAM (module 14)
```

**Bridge:** this is defense in depth as you know it from OT — zone and conduit, with the conduit rules owned by different people at different levels. The new part is the bottom two layers: controls on *API calls*, which a packet firewall never sees.

### Google Cloud: VPC firewall rules and firewall policies (Cloud NGFW)

Google's firewall family is called **Cloud Next Generation Firewall (Cloud NGFW)**.

- **VPC firewall rules** — the classic per-network rules you've used since module 01. **Stateful** (return traffic allowed automatically). Each has a direction, priority (0–65535, lower wins, default 1000), allow or deny action, and a **target**: all instances, instances with a **network tag**, or instances running as a **service account**.
- **Implied rules:** every network denies all ingress and allows all egress unless you say otherwise.
- **Always-allowed traffic:** a VM can always reach its metadata server (`169.254.169.254`). **Blocked by default:** outbound TCP 25 (SMTP) to external addresses.
- **Network firewall policies** (global or regional) — groupings of rules attached to a network, supporting newer features like **secure tags** (IAM-controlled tags for micro-segmentation) and, on paid tiers, **FQDN objects**, **geolocation**, and **threat-intelligence lists**.
- **Hierarchical firewall policies** — attached to the **organization or folders**. Lower levels **can't override** a higher-level rule; they only see traffic the higher policy passes down with **`goto_next`**. Use them to say "nobody in this org opens RDP to the internet," full stop. They require an organization and carry a small per-VM charge.
- **Evaluation order (default):** hierarchical policies (org, then folders down) → VPC firewall rules → global network firewall policy → regional network firewall policy → implied rules.
- **Tiers:** **Essentials** (IP/port/protocol rules) is free; **Standard** adds FQDN, geolocation, and threat-intelligence matching (billed per GiB evaluated on internet-bound traffic); **Enterprise** adds Layer 7 inspection — **intrusion prevention** and URL filtering — through firewall endpoints (billed per endpoint-hour plus per GiB).
- **Firewall Rules Logging** is per rule and off by default; turn it on for the rules you need evidence from.

**Prefer service accounts or secure tags as targets over network tags.** Anyone who can edit a VM can add a network tag to it — and inherit whatever the tag's rules allow. Service-account and secure-tag targets are controlled by IAM.

### AWS: security groups and network ACLs

| | **Security group** | **Network ACL (NACL)** |
|---|---|---|
| Attaches to | An instance's network interface (ENI) | A subnet |
| Rules | **Allow only** | Allow **and** deny |
| Evaluation | All rules considered together | Numbered rules, lowest first, first match wins |
| State | **Stateful** — return traffic automatic | **Stateless** — you must allow return traffic (ephemeral ports) explicitly |
| Defaults | Default SG: allows inbound from members of the same SG, all outbound | Default NACL: allows everything; custom NACLs deny everything until you add rules |
| AWS guidance | Primary control | Secondary, coarse guardrail (e.g., block a known-bad range subnet-wide) |

A security group can reference **another security group** as a source — "the app tier may talk to the DB tier" — the AWS equivalent of Google's service-account targets. Central enforcement across accounts uses **AWS Firewall Manager** ⚠️ (feature details not verified this run); deeper inspection uses **AWS Network Firewall**.

**Homelab bridge:** NACLs behave like a stateless ACL on a basic switch — forget the ephemeral-port return rule and "everything's broken." Security groups behave like OPNsense's stateful rules.

### Azure: network security groups and friends

- **NSG** — **stateful** allow/deny rules, priorities **100–4096** (lower first, first match wins), attached to a **subnet** and/or a **NIC**.
- **Default rules** you can override but not delete: inbound allows `VirtualNetwork` → `VirtualNetwork` (65000) and the Azure load balancer (65001), then **DenyAllInbound** (65500); outbound allows VNet traffic and **AllowInternetOutBound** (65001) before DenyAllOutBound. Note the last one: **Azure allows outbound internet by default** in NSGs.
- **Service tags** (`Storage`, `Internet`, `AzureCloud`…) are Microsoft-maintained IP groups; **application security groups (ASGs)** group VMs by role so rules reference "web" and "db" instead of IPs — analogous to AWS SG references.
- **Central enforcement:** **Azure Virtual Network Manager security admin rules** are evaluated **before** NSGs; actions are Allow (NSGs still evaluate), **Always allow** (skip NSGs), and **Deny**. Microsoft's example use: block 22, 3389, and 445 across every VNet regardless of what app teams put in their NSGs. **Azure Firewall** provides centralized, stateful L3–L7 filtering in a hub.

### Comparing the "central team" layer

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Org/hierarchy-level network rules | **Hierarchical firewall policies** (org/folder; lower levels can't override) | **AWS Firewall Manager** policies across accounts ⚠️ | **Virtual Network Manager security admin rules** (evaluated before NSGs) |
| Guardrails on *configuration* (not packets) | Org policies, e.g., `compute.vmExternalIpAccess`, `compute.skipDefaultNetworkCreation` | SCPs | Azure Policy |

### Private access to provider services — no internet required

A VM with no external IP (every lab since module 01) can't reach the internet — including **Google Cloud APIs**, **S3**, or **Azure Storage**, which live on public endpoints. Options:

| Google Cloud | AWS | Azure |
|---|---|---|
| **Private Google Access** — per-subnet switch letting internal-only VMs reach Google APIs. Optional special domains: `private.googleapis.com` (199.36.153.8/30) and `restricted.googleapis.com` (199.36.153.4/30) — the latter only serves APIs that VPC Service Controls supports | **Gateway endpoints** — S3 and DynamoDB only; a route-table entry; **free**; don't use PrivateLink | **Service endpoints** — extend VNet identity to a PaaS service; free; Microsoft says insufficient where exfiltration is a compliance concern |
| **Private Service Connect (PSC)** — your own internal IP as an endpoint for Google APIs or for a **published service** (Cloud SQL, partner, or your own) | **Interface endpoints (AWS PrivateLink)** — ENIs with private IPs for many services; hourly + per-GB charges; reachable from on-prem | **Private Endpoint (Azure Private Link)** — a private IP mapped to **one specific resource**; Microsoft's preferred option for new designs; reachable from on-prem |

**The security difference that matters:** some of these reach *any* instance of a service; some reach *only yours*. An Azure Private Endpoint maps to one storage account, so a compromised VM can't use it to write to an attacker's storage account. A service endpoint or plain internet path doesn't make that distinction. AWS solves it with **VPC endpoint policies** ("only these buckets, only principals from my org"); Google solves it with **VPC Service Controls**.

**After you add private access, turn off the public path** where the service allows (e.g., Azure: disable public network access on the storage account; Google: Cloud SQL private IP only, enforced by `sql.restrictPublicIp`).

### Egress control — the forgotten direction

Most designs obsess over ingress and leave egress at "allow all" — which is every cloud's default (Google's implied egress allow; AWS SG default outbound; Azure `AllowInternetOutBound`). But egress is how malware calls home and how data leaves.

Layered egress options:

1. **No public IPs** on workloads (org policy `compute.vmExternalIpAccess` on Google).
2. **Controlled NAT**: Cloud NAT / NAT gateway / Azure NAT Gateway — one known exit, logged.
3. **Deny-by-default egress rules**, then allow specific destinations: Google API ranges, update mirrors, partners.
4. **FQDN-aware filtering**: Cloud NGFW Standard FQDN objects or Google's **Secure Web Proxy** ⚠️; **AWS Network Firewall** and **Route 53 Resolver DNS Firewall** ⚠️; **Azure Firewall**.
5. **API-level boundaries** (next section), because a lot of exfiltration never touches a firewall — it's an authorized API call to copy a bucket.

**Bridge to your OT background:** this is the Purdue-model instinct — Level 2 shouldn't initiate connections to the internet at all, and anything that must leave goes through a defined, monitored conduit.

### VPC Service Controls: a perimeter around APIs, not packets

**The problem it solves:** an analyst's service-account key leaks. The attacker, sitting on a laptop anywhere, calls `storage.objects.get` — IAM says yes, because the credential is valid. Or an insider with legitimate access copies a dataset to a bucket in their personal project. **No firewall sees either action**, because both are HTTPS calls to Google's public API endpoints.

**What VPC Service Controls does:** you draw a **service perimeter** around projects and choose **restricted services** (e.g., Cloud Storage, BigQuery). Then:

- Requests to those services from **outside** the perimeter are denied — even with valid credentials — unless an **access level** (source IP range, device attributes, geography, via Access Context Manager) or an **ingress rule** allows them.
- Resources **inside** can't read from or write to resources **outside** (e.g., a public bucket, an external BigQuery table) unless an **egress rule** allows it.
- **Dry-run mode** logs what *would* be blocked without blocking — the safe way to roll out.
- Every denial (and every dry-run violation) is written to **Policy Denied audit logs**, which can't be disabled.

**What it is not:** it's not an IAM replacement — Google recommends both — and Google says it isn't designed for comprehensive control of metadata movement. It requires an organization-level access policy (or scoped policies delegated to folders/projects). It also has a reputation for breaking things when enforced without a dry-run period.

**Why agencies care:** it directly addresses the two scenarios security reviewers ask about most — stolen credentials used from outside, and insiders moving data to unauthorized locations — at the API layer, where cloud data actually moves. It also gives a clear, auditable boundary that maps onto an authorization boundary (modules 26–27).

**The peers:**

- **AWS data perimeters:** not a single product but a pattern — SCPs, RCPs, resource-based policies, and **VPC endpoint policies** using condition keys like `aws:PrincipalOrgID`, `aws:ResourceOrgID`, and `aws:SourceVpce` so that only trusted identities reach trusted resources from expected networks.
- **Azure:** **Private Endpoints** with public access disabled, plus **network security perimeter**, which Microsoft describes as an explicit boundary around PaaS resources, used alongside Private Endpoints for exfiltration protection.

**Bridge to your intel background:** IAM is your clearance and need-to-know. VPC Service Controls is the SCIF door: even a cleared person can't carry the material out through it, and a stranger with someone else's badge can't use it from the parking lot. It doesn't replace clearances; it constrains where cleared access can be exercised.

> **Shared responsibility — say it plainly:** the provider builds the firewall engines, endpoints, and perimeter service. **Every rule, every exposure, every egress path, every private endpoint, and every perimeter is configured by the customer.** An open port, a missing egress rule, or a perimeter left in dry-run forever is the customer's gap.

---

## Text diagram — layered controls on Google Cloud

```
 Org ── Hierarchical FW policy: deny 22/3389 from 0.0.0.0/0 (except IAP 35.235.240.0/20 → goto_next)
  └─ Folder Prod ── VPC SC perimeter "prod" (restricted: storage, bigquery) ── dry run → enforced
       └─ Host project net-prod ── VPC prod-vpc
            ├─ Network FW policy: egress deny 0.0.0.0/0 (logged) · allow 199.36.153.4/30 :443
            ├─ subnet app (Private Google Access ON) ── VMs: no external IP, SA-targeted ingress rules
            └─ Cloud NAT (only for the patch-mirror subnet)
  Leaked SA key on attacker laptop ──► storage.googleapis.com ──✗ Policy Denied (outside perimeter)
  Insider copy prod bucket → personal-project bucket ──✗ Policy Denied (egress from perimeter)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Per-workload stateful rules | VPC firewall rules / network firewall policies (target by SA or secure tag) | Security groups (allow-only; reference other SGs) | NSGs on NIC + ASGs | AWS SGs can't deny |
| Subnet-level rules | (rules are network-wide with targets) | NACLs (stateless) | NSG on subnet (stateful) | Only AWS has a stateless layer |
| Org-level network rules | Hierarchical firewall policies | Firewall Manager ⚠️ | Virtual Network Manager security admin rules | Google's attach to the resource hierarchy |
| Default egress | Allow (implied) | Allow (SG outbound) | Allow (`AllowInternetOutBound`) | Egress control is always opt-in |
| L7 / IPS | Cloud NGFW Enterprise | AWS Network Firewall | Azure Firewall Premium ⚠️ | |
| Private API access (free) | Private Google Access | Gateway endpoints (S3, DynamoDB) | Service endpoints | |
| Private endpoint to a specific service | Private Service Connect | Interface endpoints (PrivateLink) | Private Endpoint (Private Link) | |
| API-level exfiltration boundary | **VPC Service Controls** (perimeters, access levels, ingress/egress rules, dry run) | Data perimeter pattern (SCP/RCP + endpoint and resource policies) | Private Endpoints + network security perimeter | Google's is one purpose-built service |
| Denial telemetry | Firewall Rules Logging; Policy Denied audit logs (VPC-SC, always on) | VPC Flow Logs; CloudTrail access-denied events | NSG/VNet flow logs ⚠️; Activity Log | |

## Administer and monitor it

- **Review effective rules**, not just configured ones: `gcloud compute networks get-effective-firewalls`; AWS Reachability Analyzer ⚠️; Azure "effective security rules" on a NIC ⚠️.
- **Firewall Insights** (Google) flags shadowed, unused, and overly permissive rules ⚠️ (feature naming not re-verified this run).
- **Logs:** rule and policy changes are Admin Activity / CloudTrail / Activity Log events (module 18) — alert on new `0.0.0.0/0` ingress. Firewall Rules Logging and VPC Flow Logs (opt-in, sampled) show traffic. VPC-SC Policy Denied logs show blocked API calls — gold for detecting stolen-credential use.
- **Change process:** hierarchical policies and perimeters are high blast radius; dry-run and staged rollouts are standard practice.

## Security angle

1. **`0.0.0.0/0` ingress on SSH/RDP/database ports** — the perennial #1. Hierarchical policy or AVNM admin rule to block it org-wide; IAP/Session Manager/Bastion for admin access (module 05).
2. **Network-tag targeting** that any VM editor can abuse; prefer service accounts or secure tags.
3. **Allow-all egress** with public IPs on workloads.
4. **Private endpoint added, public endpoint left open** — the private path is decoration if the public one still works.
5. **AWS default security group** left with its self-referencing allow rule, or NACLs used as the only control.
6. **VPC Service Controls left in dry run indefinitely**, or so many ingress/egress exceptions that the perimeter is meaningless.
7. **No logging on deny rules** — you can't see the attempts.

## Threat intel angle

- **T1562.007 Impair Defenses: Disable or Modify Cloud Firewall** — adversaries add permissive rules or delete restrictive ones to open access or egress. Alert on firewall rule/policy changes, especially by unusual principals or outside change windows.
- **T1537 Transfer Data to Cloud Account** — moving data to an adversary-controlled account in the *same* provider, which looks like normal provider traffic to a network monitor. VPC Service Controls egress restrictions and AWS `aws:ResourceOrgID` conditions are aimed squarely at this.
- **T1078.004 Valid Accounts: Cloud Accounts** — stolen credentials used from outside; perimeters with access levels turn that into a Policy Denied log entry instead of a breach.
- **T1048 Exfiltration Over Alternative Protocol** and **T1071 Application Layer Protocol** (C2) — the reason for deny-by-default egress and FQDN filtering.

**Detection ideas:** new ingress rules with `0.0.0.0/0`; changes to hierarchical policies or perimeters; bursts of VPC-SC Policy Denied events for one principal (a stolen key being tried from outside); egress-deny hits from a workload that never talked externally before.

**Bridge to your CTI work:** Policy Denied logs are a rare collection source that captures attempted *misuse of valid credentials* — the activity that blends in everywhere else. In an intrusion timeline, the first perimeter denial is often the earliest observable.

## Public sector notes

- **VPC Service Controls is commonly part of Google's regulated-workload story**, including alongside Assured Workloads ⚠️ (the specific relationship per control package is module 27 material).
- **Org-level rules map to agency structure:** a central SOC/network office owns hierarchical policies and perimeters; programs own their workload rules.
- **Egress control** connects to federal requirements for monitored internet connections (TIC 3.0) and zero trust (module 17) ⚠️ — detail deferred to those modules.
- **Private-only access to managed services** (no public endpoints) is a frequent assessor expectation for moderate and high systems (module 26).

## Key takeaways

- Layers: org-level policy → network policy → workload rules → API perimeter → IAM. Each is owned by a different team; all are the customer's.
- Google: VPC firewall rules + network and hierarchical firewall policies (Cloud NGFW). AWS: stateful allow-only security groups + stateless NACLs. Azure: stateful NSGs + ASGs, with Virtual Network Manager admin rules above them.
- Egress is allow-all by default everywhere. Deny by default, allow by exception, and remove public IPs.
- Private Google Access / gateway endpoints / service endpoints reach services privately; PSC / PrivateLink interface endpoints / Private Endpoints reach *specific* services by private IP. Turn off the public path afterward.
- VPC Service Controls blocks API access from outside a perimeter and data movement across it — even with valid credentials. It complements IAM; roll it out in dry run first.
- Firewall rules, egress paths, private endpoints, and perimeters are **always the customer's** configuration.

## Sources

- [Google Cloud — VPC firewall rules](https://docs.cloud.google.com/firewall/docs/firewalls)
- [Google Cloud — Cloud NGFW overview](https://docs.cloud.google.com/firewall/docs/about-firewalls) and [Cloud NGFW pricing](https://cloud.google.com/firewall/pricing)
- [Google Cloud — Hierarchical firewall policies](https://docs.cloud.google.com/firewall/docs/firewall-policies)
- [Google Cloud — Evaluation order for firewall policies and rules](https://docs.cloud.google.com/firewall/docs/firewall-policies-rule-eval-order)
- [Google Cloud — Private Google Access](https://docs.cloud.google.com/vpc/docs/private-google-access) and [Configure Private Google Access](https://docs.cloud.google.com/vpc/docs/configure-private-google-access)
- [Google Cloud — Private Service Connect](https://docs.cloud.google.com/vpc/docs/private-service-connect)
- [Google Cloud — Overview of VPC Service Controls](https://docs.cloud.google.com/vpc-service-controls/docs/overview), [Dry run mode](https://docs.cloud.google.com/vpc-service-controls/docs/dry-run-mode), [Audit logging](https://docs.cloud.google.com/vpc-service-controls/docs/audit-logging), [Pricing](https://cloud.google.com/vpc-service-controls/pricing)
- [Google Cloud Architecture Center — Preventative controls (org policy constraints)](https://docs.cloud.google.com/architecture/blueprints/security-foundations/preventative-controls)
- [AWS — Infrastructure security in Amazon VPC (SGs vs NACLs)](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html), [Security groups](https://docs.aws.amazon.com/vpc/latest/userguide/security-groups.html), [Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)
- [AWS — Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html)
- [AWS Security Blog — Establishing a data perimeter on AWS](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws/)
- [Microsoft — Network security groups overview](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview)
- [Microsoft — Security admin rules in Azure Virtual Network Manager](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-security-admins)
- [Microsoft — Private access to Azure PaaS services](https://learn.microsoft.com/en-us/azure/networking/design-guide/private-platform-as-a-service) and [What is Azure Private Link?](https://learn.microsoft.com/en-us/azure/private-link/private-link-overview)
- [MITRE ATT&CK — T1562.007](https://attack.mitre.org/techniques/T1562/007/), [T1537](https://attack.mitre.org/techniques/T1537/), [T1078.004](https://attack.mitre.org/techniques/T1078/004/), [T1048](https://attack.mitre.org/techniques/T1048/)

Verified: 2026-10-25
