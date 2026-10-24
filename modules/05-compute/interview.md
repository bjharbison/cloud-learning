# 05 Interview Prep — Compute

## Likely questions

### Q1. "How do your admins get onto VMs without opening SSH to the internet?"

**Answer outline:**
- No public IPs on VMs; no inbound admin ports from `0.0.0.0/0`.
- Google: OS Login (IAM-controlled Linux accounts) + IAP TCP forwarding; firewall allows 22 only from IAP's range; IAP and OS Login roles granted to groups.
- AWS: Systems Manager Session Manager — no inbound ports at all; IAM controls who can start sessions; sessions logged.
- Azure: Azure Bastion to private IPs; Premium adds session recording.
- Everything is identity-checked (MFA upstream) and logged.

**Strong signal:** saying "the provider builds the broker; whether port 22 is open is always our decision."
**Avoid:** "we restrict SSH to the office IP range" as the whole answer.

### Q2. "Walk me through making a VM-based app survive a zone failure."

**Answer outline:**
- Template → regional managed group across ≥2 zones (MIG / ASG across AZs / scale set across zones).
- Health checks with autohealing; autoscaling with explicit min/max.
- Load balancer in front (module 12); stateless VMs, state in managed storage/databases.
- Test it: kill a zone's VMs and watch recovery (module 02's RTO/RPO).

**Strong signal:** linking zones to RTO, and calling out that autoscalers delete VMs, so no state on local disks.

### Q3. "What's the risk with the VM's service account?"

**Answer outline:**
- Credentials are served by the metadata server to anything on the VM — and to SSRF.
- Google's default compute SA may have Editor; Google recommends user-managed, least-privilege SAs (or none).
- AWS: require IMDSv2, least-privilege instance profiles. Azure: narrow managed-identity role assignments.
- Maps to ATT&CK T1552.005.

**Strong signal:** "anyone who can log in to the VM can use its service account" (Google's own warning).

### Q4. "A customer asks if their data is protected while it's being processed. What do you say?"

**Answer outline:**
- At rest and in transit are standard (module 16); in-use is where Confidential VMs come in.
- Hardware memory encryption (AMD SEV-SNP, Intel TDX) plus attestation, available on all three clouds on specific machine series.
- Be honest about limits: it protects against host/operator memory access; it doesn't fix IAM mistakes, and not every machine type supports it.

### Q5. "When would you not use VMs?"

**Answer outline:**
- When the app can be containerized and you want density and faster deploys (module 06), or it's event-driven/request-driven (module 07).
- VMs fit lift-and-shift, legacy OS dependencies, licensed software, and full OS control.

## 60-second executive explanation

"Virtual machines are rented servers. The important decisions aren't the size — they're who can get in and what the machine itself is allowed to do. We set them up so nobody reaches a server directly from the internet; administrators sign in with their agency identity and multi-factor authentication through a provider-run gateway, and every session is logged. Each server is stamped from an approved, hardened template, and we run them in groups spread across separate data centers, so if one fails the group automatically replaces it. The groups grow and shrink with demand, but only up to a ceiling we set — which is also how we keep spending inside the budget."

## Whiteboard prompt

Draw a regional MIG across two zones behind a load balancer. Show: instance template (image family, Shielded VM, no external IP, least-privilege SA), autoscaler min/max, the IAP path with its firewall rule, and OS Login roles bound to an admin group. Then draw the attacker's path from an SSRF bug to the metadata server and mark the two controls that break it.

## What you can honestly claim

- **After reading + quiz:** "I've studied VM fleets, autoscaling, and secure administrative access on Google Cloud, AWS, and Azure, including OS Login/IAP, Session Manager, and Azure Bastion, and VM identity risks."
- **After completing the lab:** "In a personal lab I built a regional managed instance group from a Shielded VM template with no external IPs and no attached service account, enforced OS Login, administered it only through IAP, and observed autohealing and autoscaling." Add the AWS Session Manager / Azure Bastion sentence only if you did those parts.
- **Still requires (cert / production experience / clearance):** running production VM fleets, building golden-image pipelines, patch management at scale, or operating STIG-hardened systems in an accredited environment. Don't claim "managed cloud infrastructure." The Google Associate Cloud Engineer exam tests MIGs and access at a claimable level.
