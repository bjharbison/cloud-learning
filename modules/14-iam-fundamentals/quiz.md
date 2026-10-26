# 14 Quiz — IAM fundamentals

1. Define principal, permission, role, policy, and scope in one line each.
<details><summary>Answer</summary>

Principal: who (user, group, workload identity). Permission: one action on one resource type. Role: a named bundle of permissions. Policy: the document binding principals to roles/permissions on resources. Scope: where the policy applies — and on all three clouds, grants at a higher scope flow down.
</details>

2. On Google Cloud, a user has `roles/storage.admin` granted on a folder, and the project below it has no bindings for that user. Can they delete a bucket in that project? How would you stop them without removing the folder grant?
<details><summary>Answer</summary>

Yes — allow policies are inherited and additive. To carve out an exception, use an IAM deny policy (on the project or folder) denying the relevant permission (written in deny format, `SERVICE_FQDN/RESOURCE.ACTION`; only some permissions are deniable — check Google's list), possibly with exception principals. Deny is evaluated before allow.
</details>

3. What's the Google Cloud evaluation order among principal access boundary, deny, and allow policies?
<details><summary>Answer</summary>

PAB first (is the resource even eligible for this principal?), then deny policies, then allow policies. No matching allow means deny by default. Organization Policy is a separate configuration guardrail, not part of this check.
</details>

4. Which AWS policy types grant permissions, and which only limit them?
<details><summary>Answer</summary>

Grant: identity-based policies, resource-based policies (and legacy ACLs). Limit only: permissions boundaries, SCPs, RCPs, and session policies. An explicit Deny in any of them wins.
</details>

5. A role in account A needs to read an S3 bucket in account B. What has to be true?
<details><summary>Answer</summary>

Both sides must allow: account A's identity policy must allow `s3:GetObject` on the bucket, and account B's bucket policy must allow the role as principal. No explicit Deny in either account (or in applicable SCPs/RCPs).
</details>

6. Spot the misconfiguration: "Our Azure admin is Global Administrator, so they already control all our subscriptions."
<details><summary>Answer</summary>

Global Administrator is an Entra (directory) role and has no Azure resource access by default. They *can* use "elevate access" to grant themselves User Access Administrator at root scope — which is powerful, logged, and should be removed after use. Azure RBAC and Entra roles are separate systems.
</details>

7. List Azure RBAC's four scopes from broadest to narrowest. What's the per-subscription role-assignment limit?
<details><summary>Answer</summary>

Management group → subscription → resource group → resource. 5,000 role assignments per subscription.
</details>

8. Why are service-account keys and IAM user access keys risky, and what are the alternatives on each cloud?
<details><summary>Answer</summary>

They're long-lived bearer credentials that leak into code, CI, laptops, and images (T1552.001), and work from anywhere. Alternatives: Google — attached service accounts, impersonation, Workload Identity Federation (new orgs block key creation by default since May 3, 2024); AWS — IAM roles with STS temporary credentials, Identity Center for humans; Azure — managed identities, workload identity federation.
</details>

9. Why is granting `roles/iam.serviceAccountUser` on a powerful service account a privilege-escalation risk?
<details><summary>Answer</summary>

It includes `iam.serviceAccounts.actAs`, letting the holder attach that SA to a VM, function, or job and run code with its permissions. Effectively, they inherit the SA's power. (Token Creator is similar: it lets them mint tokens for the SA — MITRE T1548.005.)
</details>

10. Match the tool to the question — "Why was this denied?", "Who can access this?", "Which permissions go unused?" — on each cloud.
<details><summary>Answer</summary>

Why: Google Policy Troubleshooter; AWS IAM policy simulator; Azure Check access. Who: Google Policy Analyzer; AWS IAM Access Analyzer (external/internal access); Azure role-assignment lists and access reviews. Unused: Google role recommendations; AWS last accessed information and Access Analyzer unused access; Azure Defender CSPM Permissions Management (CIEM).
</details>

11. An attacker with a stolen token creates a new service-account key and grants a new Owner binding. Name the ATT&CK techniques and the audit events you'd alert on.
<details><summary>Answer</summary>

T1098.001 Additional Cloud Credentials (`CreateServiceAccountKey`) and T1098.003 Additional Cloud Roles (`SetIamPolicy` adding Owner). Initial access likely T1078.004 Valid Accounts: Cloud Accounts. Equivalent AWS events: `CreateAccessKey`, `AttachRolePolicy`/`PutRolePolicy`; Azure: role assignment writes.
</details>

12. Scenario: an agency team asks for Editor on the production project "to move fast." What do you recommend?
<details><summary>Answer</summary>

Decline the basic role. Identify the tasks, grant predefined roles to a group at the narrowest resource or project scope, use time-bound elevation (conditions or Privileged Access Manager) for rare admin tasks, keep separation of duties (network/security roles with the central team), and review with role recommendations after 30–90 days.
</details>
