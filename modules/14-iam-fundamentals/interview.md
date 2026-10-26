# 14 Interview Prep — IAM fundamentals

## Likely questions

### Q1. "Explain how IAM works on Google Cloud."

**Answer outline:**
- Allow policies attached to resources in the hierarchy (org → folder → project → resource); bindings of roles to principals, optionally with conditions; inherited and additive.
- Roles: basic (avoid in production), predefined (default choice), custom (when predefined is materially too broad).
- Restrictions: deny policies (org/folder/project, evaluated before allow) and principal access boundary policies (limit what a set of principals is eligible to access).
- Order: PAB → deny → allow → default deny. Org Policy separately governs configuration.
- Practice: groups, lowest scope, no keys, time-bound elevation, recommendations.

**Strong signal:** "inheritance is additive, so carve-outs need deny policies."
**Avoid:** describing Google IAM in AWS terms ("attach a policy to the user").

### Q2. "How does Google Cloud IAM differ from AWS and Azure?"

**Answer outline:**
- Google: policy lives on resources in one hierarchy; roles bundle permissions.
- AWS: grants live on identities *and* resources; a family of limiters (boundaries, SCPs, RCPs, session policies); explicit deny anywhere wins; cross-account needs both sides.
- Azure: RBAC role assignments at four scopes for resources; a separate Entra role system for the directory; "elevate access" bridges them.
- All three: least privilege, workload identities over keys, logs on every change.

**Strong signal:** getting AWS evaluation logic right and naming Azure's two systems.

### Q3. "A developer needs to run a deployment script as a service account. How do you set that up?"

**Answer outline:**
- No JSON key. Grant the developer (via a group) Token Creator on that one SA and use impersonation — short-lived, logged, revocable. Or run the script in CI with Workload Identity Federation (module 15).
- Give the SA only the roles the deployment needs, on the target project or resources.
- Watch the escalation paths: Token Creator and actAs on a powerful SA are equivalent to its permissions.
- Consider time-bound access (Privileged Access Manager) for production.

### Q4. "How would you find and remove excess permissions in an existing environment?"

**Answer outline:**
- Inventory: Policy Analyzer / Access Analyzer / role-assignment exports; flag basic roles, org-level grants, external principals, `allUsers`.
- Usage: role recommendations, last accessed data, CIEM in Defender CSPM.
- Keys: list and age all SA keys / access keys / SP secrets; migrate to keyless.
- Change safely: replace, don't just remove; monitor 403s; iterate.
- Prevent regrowth: org policies (key creation disabled, domain-restricted sharing), SCPs, review cadence.

### Q5. "What does an attacker do with cloud IAM after initial access?"

**Answer outline:**
- Discover (T1087.004, T1069.003, T1580) — list roles, policies, SAs.
- Escalate — actAs/Token Creator/PassRole (T1548.005), attach admin policies.
- Persist — new keys (T1098.001), new bindings (T1098.003), new federated trusts.
- Public example: Google's H1 2026 Cloud Threat Horizons case UNC6426 — stolen GitHub token → over-permissive OIDC trust → role → AdministratorAccess in under 72 hours.
- Detection: alert on key creation, privileged bindings, elevate access, enumeration bursts.

## 60-second executive explanation

"In the cloud, almost every breach comes down to who has access to what. Our rule is simple: people and programs get only the access they need, only where they need it, and only for as long as they need it — the same need-to-know principle we use for sensitive information. We grant access to groups, not individuals, so it's easy to review. We avoid permanent passwords for software, because those leak; instead, systems get short-lived credentials that expire on their own. And every change to access is logged, so if someone tries to give themselves more power, we see it. The cloud provider enforces our rules faithfully — but writing those rules is entirely our job."

## Whiteboard prompt

Draw an agency Google Cloud org: org → folders (Prod, Nonprod, Security) → projects. Place: a deny policy at the org blocking SA key creation and IAM role creation except for the security team; groups (`grp-network-admins`, `grp-app-deployers`, `grp-analysts`) bound at folder or project scope with predefined roles; a deployment SA with Token Creator granted only to the CI identity; analysts with `objectViewer` on one bucket. Then trace one attacker path (stolen developer token → actAs → admin) and mark where the design or the logs stop it. Redraw the same intent with AWS SCPs + permission sets + boundaries, and Azure management groups + RBAC + PIM.

## What you can honestly claim

- **After reading + quiz:** "I've studied IAM on Google Cloud, AWS, and Azure — allow and deny policies, AWS policy evaluation logic, Azure RBAC versus Entra roles — and least-privilege practices, including replacing long-lived keys."
- **After completing the lab:** "In a personal lab I implemented least privilege for a Google Cloud service account at bucket scope, used it keylessly via impersonation, diagnosed access with Policy Troubleshooter, and applied a time-bound IAM condition and a custom role." Add the deny-policy, AWS boundary/simulator, or Azure RBAC sentences only if you did them.
- **Still requires (cert / production experience / clearance):** designing and operating IAM for a real organization, running access reviews, or remediating an IAM-based intrusion. Don't write "IAM administration experience" or "implemented least privilege for an enterprise." Your intel background in need-to-know and access control is real, transferable experience — describe it as that, not as cloud IAM. The Google Associate Cloud Engineer and Professional Cloud Security Engineer exams test this material and are claimable once earned.
