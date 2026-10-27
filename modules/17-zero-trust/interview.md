# 17 Interview Prep — Zero trust

## Likely questions

### Q1. "What does zero trust mean to you?"

**Answer outline:**
- Per-request access decisions based on identity, device, and context; assume the network is hostile.
- NIST SP 800-207: policy engine/administrator decide, enforcement points gate; everything logged.
- A model you implement across pillars (identity, devices, networks, apps, data), not a product.
- Google's origin story: BeyondCorp after Aurora — internal apps on the internet behind an access proxy.

**Strong signal:** using NIST vocabulary and naming the pillars. **Avoid:** "zero trust means no VPN" or naming a single product.

### Q2. "We have a VPN for remote access. How would we move toward zero trust on Google Cloud?"

**Answer outline:**
- Inventory apps and who uses them; start with a high-value, low-complexity web app.
- Put it behind IAP (direct on Cloud Run, or behind a load balancer); grant per-group access; lock firewalls so IAP can't be bypassed.
- Federate to the agency IdP with phishing-resistant MFA (PIV); add device signals and access levels (Chrome Enterprise Premium) where required.
- Admin access through IAP TCP forwarding and OS Login; data inside VPC Service Controls.
- Log decisions (IAP Data Access logs) and measure against CISA ZTMM pillars; retire the VPN path app by app.

### Q3. "How do Google, AWS, and Microsoft approach zero trust differently?"

**Answer outline:**
- Google: IAP + Access Context Manager + Chrome Enterprise Premium; the browser is a key enforcement point; IAP core is free.
- AWS: building blocks — Verified Access (per app-hour), VPC Lattice, Verified Permissions, Session Manager.
- Microsoft: Conditional Access as the policy engine, Global Secure Access (Private/Internet Access) as SSE, Intune device compliance.
- Many agencies mix: Entra as IdP and Conditional Access, Google IAP enforcing for apps on Google Cloud.

### Q4. "What federal zero-trust requirements should a cloud provider help an agency meet?"

**Answer outline:**
- OMB M-22-09 goals: phishing-resistant MFA, device signals, encrypted DNS/HTTPS, apps treated as internet-facing, data categorization and logging (M-21-31).
- CISA ZTMM 2.0: five pillars, three cross-cutting capabilities, four stages — use it to show progression.
- DoD: Target Level (91 activities) by end of FY2027; NSA implementation guidelines phase the work.
- Be precise: map specific services to specific activities; don't claim a product "delivers zero trust."

**Strong signal:** noting M-22-09's status ("no rescission found") and that pillar mappings must be traceable.

### Q5. "Why do so many breaches start at the VPN?"

**Answer outline:**
- Internet-facing, high-value, patched on vendor schedules, often poorly monitored; compromise gives network-level access (T1190, T1133).
- Public examples: CISA AA24-060B (Ivanti), Citrix Bleed exploitation.
- Zero trust removes the flat network behind the gate and makes every request carry identity and device context — but the IdP and proxy become crown jewels to protect and monitor.

## 60-second executive explanation

"For decades we protected data by building a wall around the network and letting anyone inside move freely. Attackers learned that once they got past the wall — often through the VPN itself — they could go anywhere. Zero trust flips that: every request to every application is checked — who you are, whether your device is healthy, whether you need this right now — and every decision is recorded. Google built its own company this way after a major intrusion in 2009, and the federal government now requires agencies to move in this direction. It's not one product we buy; it's a series of steps, application by application, starting with the ones that matter most."

## Whiteboard prompt

Draw an agency's path from a VPN to zero trust on Google Cloud: Entra ID as IdP (PIV, Conditional Access) federated to Google; IAP in front of a Cloud Run case-management app and a legacy app on Compute Engine behind a load balancer (firewall allows only LB/IAP ranges); IAP TCP forwarding for admins with Privileged Access Manager; VPC Service Controls around the data; all decisions flowing to a central log sink (module 18). Label PDP and PEP, and the CISA pillar each box serves.

## What you can honestly claim

- **After reading + quiz:** "I've studied zero-trust architecture (NIST SP 800-207), Google's BeyondCorp model and Identity-Aware Proxy, AWS Verified Access, Microsoft Conditional Access and Global Secure Access, and the federal zero-trust framework — OMB M-22-09, the CISA Zero Trust Maturity Model, and the DoD Zero Trust Strategy."
- **After completing the lab:** "In a personal lab I protected a Cloud Run application with Google Cloud Identity-Aware Proxy, granted time-limited access with an IAM Condition, reviewed access decisions in IAP audit logs, and revoked access through policy alone."
- **Still requires (cert / production experience / clearance):** planning or running an agency zero-trust program, Chrome Enterprise Premium device-based policies, or DoD Target Level implementation; claiming "implemented zero trust." Context-aware access levels need an organization. If your prior roles involved assessing remote-access or network-segmentation risk (including OT), that's relevant experience — describe it accurately and only at the level you can discuss publicly.
