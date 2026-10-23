# 00 Interview Prep — Lab environment

## Likely questions

### Q1. "A customer is spinning up their first cloud environment for a pilot. What do you set up on day one?"

**Answer outline:**
- Lock down the top-level identity: phishing-resistant MFA, no access keys, break-glass procedure.
- Separate admin identities through the provider's identity service (Identity Center / Entra / Cloud Identity).
- Billing guardrails: budgets with alerts, owners who actually read them.
- A resource container per environment (project / account / subscription) so the pilot is isolated and easy to delete.
- Audit logging on from the start (module 18).

**Strong signal:** framing it as "identity first, then money, then everything else," and noting that all of it is customer-side under shared responsibility.
**Avoid:** jumping straight to networks and VMs.

### Q2. "Do budgets protect a customer from runaway spend?"

**Answer outline:**
- Budgets alert; they don't stop resources (all three providers say so).
- Billing data lags hours; alerts can fire late.
- Real protection: quotas, org-level policy limits, automation triggered by budget notifications, and cleanup discipline.
- For government: ties directly to appropriations — overspend is a compliance problem, not just a cost one (module 04).

**Strong signal:** knowing the "alert, not cap" distinction and the data lag.
**Avoid:** "Yes, set a budget and you're safe."

### Q3. "Why does it matter what kind of MFA someone uses?"

**Answer outline:**
- All three hyperscalers now require MFA for console/admin access.
- SMS and push can be phished, relayed, or fatigue-bombed; passkeys/FIDO2 are bound to the real site.
- Federal context: phishing-resistant MFA is a recurring requirement in federal zero-trust guidance (module 17 will verify specifics).

**Strong signal:** distinguishing "MFA on" from "phishing-resistant MFA on."
**Avoid:** treating all MFA as equal.

### Q4. "What's the difference between the AWS root user and an administrator?"

**Answer outline:**
- Root has unrestricted access to the account, including billing and closure; it's tied to the sign-up email.
- Admins get permissions through IAM or Identity Center and can be scoped, audited, and revoked.
- Best practice: MFA on root, no root access keys, use root only for the few tasks that require it.
- Compare: Google Cloud has no root user — power lives in hierarchy roles; Azure separates tenant admin (Entra) from resource admin (RBAC).

**Strong signal:** the cross-cloud comparison.

### Q5. "Walk me through how you'd keep lab or PoC costs at zero."

**Answer outline:**
- Use trial safety nets (no auto-upgrade, free plan, spending limit) and don't remove them early.
- Smallest sizes in free-tier regions; label everything; one project/resource group per lab.
- Budget alerts that exclude credits; delete the container at the end.

## 60-second executive explanation

"Before anyone builds anything in the cloud, we set up three things. First, who can get in: every administrator signs in with a phishing-resistant second factor, and the master account is locked away like a safe combination. Second, what it costs: we set budget alarms so we know within a day if spending moves — but alarms don't stop spending, so we also limit what can be created. Third, where things live: each project gets its own container so we can see it, bill it, and shut it down cleanly. None of this is the cloud provider's job — the provider gives us the tools; configuring them is ours. Getting these right on day one is cheaper than any incident later."

## Whiteboard prompt

Draw, from memory, the three-column diagram from this module's README: top-level identity → admin identity → billing guardrail → resource container, for Google Cloud, AWS, and Azure. Label which boxes are "customer responsibility." (Answer: all of them.)

## What you can honestly claim

- **After reading + quiz:** "I've studied account setup, identity hardening, and cost guardrails across Google Cloud, AWS, and Azure, and can discuss how they differ."
- **After completing the lab:** "In personal lab environments on all three clouds, I've configured phishing-resistant MFA, separate admin identities (an MFA-protected AWS IAM user — or IAM Identity Center if you've moved to it — and Microsoft Entra ID with Azure RBAC), and budget alerts."
- **Still requires (cert / production experience / clearance):** setting up landing zones, identity federation, or billing governance for a real organization is production work you haven't done. Don't describe a personal sandbox as "administering cloud environments." A cert (e.g., Associate Cloud Engineer) is the credible next step.
