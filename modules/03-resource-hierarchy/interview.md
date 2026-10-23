# 03 Interview Prep — Resource hierarchy

## Likely questions

### Q1. "How would you structure Google Cloud for a federal agency with several programs?"

**Answer outline:**
- Discovery first: programs, environments, ATO boundaries, impact levels, who pays.
- Org at the top (tied to the agency's Cloud Identity/Workspace domain); folders per program, then per environment; projects per workload.
- Guardrails at the org (resource locations, no external IPs by default, etc.); IAM granted low, to groups not individuals.
- Regulated programs in Assured Workloads folders; shared services (logging, networking) in their own folder.

**Strong signal:** leading with ATO boundaries and "grant low, guard high."
**Avoid:** one big project with labels.

### Q2. "Compare Google Cloud's hierarchy with AWS Organizations and Azure management groups."

**Answer outline:**
- GCP: org → folders → projects; projects are lightweight; IAM and org policy inherit.
- AWS: root → OUs → accounts; accounts are hard walls with their own IAM; SCPs cap permissions; management account is exempt from SCPs.
- Azure: tenant → management groups → subscriptions → resource groups; RBAC and Policy inherit across four scopes.
- Each has a "who" control and a "what" control.

**Strong signal:** the management-account exemption and the additive nature of GCP IAM inheritance.

### Q3. "What's the difference between IAM and Organization Policy?"

**Answer outline:**
- IAM = who can do what; org policy = what configurations are allowed at all.
- Org policy can block an Owner (example: resource-location constraint).
- Use both: IAM for least privilege, guardrails for "never" rules.

### Q4. "How does inheritance create risk?"

**Answer outline:**
- A high-level grant reaches every descendant; one compromised org-level identity is a total compromise.
- Attackers persist with quiet folder- or MG-level bindings, or move resources to escape guardrails (ATT&CK T1666).
- Mitigations: minimal top-level admins, phishing-resistant MFA, alerting on hierarchy and policy changes, periodic access review.

**Strong signal:** answering with both the defender's design and the adversary's view.

### Q5. "A customer only has a personal Gmail-based project. What's missing?"

**Answer outline:**
- No organization → no folders, no central IAM, no org policies, no clean offboarding.
- Fix: Cloud Identity (free edition available) or Workspace on a verified domain; migrate projects into the org.

## 60-second executive explanation

"Think of the cloud as a filing system with locked drawers. At the top is the agency; under it are folders for each program; inside those are the individual projects where work happens. Two kinds of rules flow down that tree. Access rules say who can open which drawer — and anything granted at the top opens every drawer below, so we grant as low as possible. Guardrail rules say what's allowed to exist at all — for example, 'no data stored outside the United States' — and those apply even to the most senior administrator. Setting the tree up right on day one means every new project automatically inherits the agency's security rules, instead of depending on each team to remember them."

## Whiteboard prompt

Draw the three hierarchies side by side (GCP, AWS, Azure) with two programs and prod/dev environments. Mark with one color where IAM/RBAC is granted, and with another where guardrails attach. Circle the one level on AWS that guardrails don't protect (the management account).

## What you can honestly claim

- **After reading + quiz:** "I've studied resource hierarchies and policy inheritance on Google Cloud, AWS, and Azure, including how IAM differs from organization-level guardrails."
- **After completing the lab:** "In personal lab environments I built resource hierarchies on all three clouds and enforced location guardrails with Azure Policy [and Google Cloud Organization Policy, if you completed Path 1], and [if you ran AWS Part B] wrote and attached an AWS SCP." State which Google path you did — if you had no organization, say so.
- **Still requires (cert / production experience / clearance):** designing a landing zone for a real organization, migrating projects into an org, or operating Assured Workloads / GovCloud / Azure Government hierarchies. Don't claim "designed enterprise cloud governance." The Associate Cloud Engineer and Professional Cloud Architect exams test this at a claimable level.
