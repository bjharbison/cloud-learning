# 17 Quiz — Zero trust

1. In one sentence, what's the core idea of zero trust — and what is it *not*?
<details><summary>Answer</summary>

Access is decided per request from identity, device, and context, with the network assumed hostile — not granted because a request comes from "inside." It's an architecture model, not a product or simply "no VPN."
</details>

2. Name the NIST SP 800-207 components and what each does.
<details><summary>Answer</summary>

Policy Engine (decides grant/deny/revoke), Policy Administrator (establishes or tears down the session), together the Policy Decision Point; Policy Enforcement Point (the gate in the data path that enforces the decision).
</details>

3. What's the current name of Google's commercial zero-trust offering, and which two components have been shut down?
<details><summary>Answer</summary>

Chrome Enterprise Premium (formerly BeyondCorp Enterprise, announced April 2024). The client connector (end of 2023) and the App Connector (formerly the BeyondCorp app connector, shut down July 31, 2026).
</details>

4. Map these to NIST roles: Google IAP; Microsoft Conditional Access; AWS Verified Access endpoint; Google IAM + Access Context Manager.
<details><summary>Answer</summary>

IAP = PEP. Conditional Access = policy engine/PDP. Verified Access endpoint = PEP (its Cedar policies + trust providers are the decision side). IAM + Access Context Manager = policy engine on Google.
</details>

5. Spot the misconfiguration: a web app on Compute Engine is behind a load balancer with IAP enabled; the VM firewall allows TCP 443 from `0.0.0.0/0`.
<details><summary>Answer</summary>

IAP can be bypassed by connecting to the VM directly. Restrict ingress to the load balancer (and IAP) source ranges and remove public IPs. Firewall rules are the customer's responsibility.
</details>

6. Why should an app behind IAP verify `x-goog-iap-jwt-assertion` rather than read `x-goog-authenticated-user-email`?
<details><summary>Answer</summary>

The JWT is signed by IAP and bound to the resource (audience); the email header is unsigned and could be forged by anyone who found a path around IAP.
</details>

7. Compare cost models: Google IAP, AWS Verified Access, Microsoft Entra Private Access.
<details><summary>Answer</summary>

Core IAP for Google Cloud resources is free (device attributes and custom access levels are paid Chrome Enterprise Premium). Verified Access bills per app-hour (about $0.27/hour per HTTP app in US East Ohio) plus per GB, no free tier. Entra Private Access is licensed (Entra Suite or standalone) and requires Entra ID P1/P2.
</details>

8. List three OMB M-22-09 requirements and its target date.
<details><summary>Answer</summary>

Any three of: centralized identity with phishing-resistant MFA; device inventory and EDR; encrypted DNS and HTTPS everywhere including internal traffic; treat applications as internet-connected (at least one FISMA-Moderate app fully usable over the internet); categorize data and audit access to encrypted cloud data; logging per M-21-31. Target: end of FY2024.
</details>

9. Name the CISA ZTMM 2.0 pillars, cross-cutting capabilities, and stages.
<details><summary>Answer</summary>

Pillars: Identity, Devices, Networks, Applications and Workloads, Data. Cross-cutting: Visibility and Analytics, Automation and Orchestration, Governance. Stages: Traditional, Initial, Advanced, Optimal.
</details>

10. What does the DoD Zero Trust Strategy require by the end of FY2027, and how many pillars does it have?
<details><summary>Answer</summary>

Target Level — 91 of 152 activities — across seven pillars (User; Device; Network & Environment; Application & Workload; Data; Visibility & Analytics; Automation & Orchestration). Advanced Level is the full set.
</details>

11. Scenario: an agency runs an internet-facing VPN appliance for all remote access. Using public reporting, explain the risk and a zero-trust alternative on Google Cloud.
<details><summary>Answer</summary>

Edge/VPN appliances are repeatedly exploited (T1190; e.g., CISA AA24-060B on Ivanti Connect Secure), and a compromise puts the attacker "inside" a flat network. Alternative: identity-aware access per app — IAP for web apps and IAP TCP forwarding for admin protocols, phishing-resistant MFA through the IdP, access levels/device signals, VPC Service Controls around data, and logged decisions — then retire the VPN path.
</details>

12. Why did the lab's IAP grant use an IAM Condition, and what zero-trust principle does it show?
<details><summary>Answer</summary>

The condition made access expire automatically after an hour — access is evaluated per request against current context and granted for only as long as needed (least privilege in time), with no network change.
</details>
