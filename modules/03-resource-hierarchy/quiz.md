# 03 Quiz — Resource hierarchy

1. Name the levels of each cloud's hierarchy, top to bottom.
<details><summary>Answer</summary>

Google Cloud: organization → folders → projects → resources. AWS: organization root → OUs → accounts → resources. Azure: Entra tenant / tenant root management group → management groups → subscriptions → resource groups → resources.
</details>

2. What's the difference between an IAM policy and a guardrail policy? Give each cloud's guardrail service.
<details><summary>Answer</summary>

IAM answers *who* can do *what*; guardrails restrict *what may exist or be configured*, regardless of who asks. Guardrails: Google Organization Policy; AWS SCPs/RCPs; Azure Policy.
</details>

3. You grant a user Viewer on a Google Cloud folder. Can a project owner below remove that access by editing the project's allow policy?
<details><summary>Answer</summary>

No. Allow policies are additive — the effective policy is the project's own plus everything inherited. Removing inherited access needs a change at the folder, or a deny policy.
</details>

4. True or false: an SCP attached to the AWS organization root restricts everyone in the management account.
<details><summary>Answer</summary>

False. SCPs don't restrict users or roles in the management account. Keep workloads out of it.
</details>

5. Does an SCP that allows `s3:*` give a user S3 access?
<details><summary>Answer</summary>

No. SCPs set the maximum available permissions; an IAM policy in the account must still grant access.
</details>

6. Spot the problem: "We put prod and dev in the same Azure subscription and named the resource groups `prod-*` and `dev-*`."
<details><summary>Answer</summary>

Naming isn't isolation. Subscription-level roles, policies, quotas, and billing are shared, so a dev mistake or compromise can reach prod. Separate subscriptions (under separate management groups) give a real boundary.
</details>

7. Brian's personal Google Account shows "No organization." What can't he do, and what are his options?
<details><summary>Answer</summary>

No folders, no org-level IAM, no org policies he can set. Options: Cloud Identity Free (needs a domain he owns and verifies) or Google Workspace. Standalone organizations are created for new Free Trial sign-ups, not existing accounts.
</details>

8. Maximum nesting depth: Google folders, AWS OUs, Azure management groups?
<details><summary>Answer</summary>

Google: 10 levels of folders. AWS: 5 levels of OUs under the root. Azure: 6 levels of management groups (excluding root and subscription).
</details>

9. You move an Azure subscription to a different Entra tenant. What happens to its RBAC role assignments?
<details><summary>Answer</summary>

They're lost — role assignments don't transfer. Managed identities and Key Vault tenant settings also need rework.
</details>

10. Scenario: an agency has three programs, each with prod and dev, and one program needs FedRAMP High controls. Sketch a Google Cloud folder layout and say where the controls attach.
<details><summary>Answer</summary>

Org → folder per program → prod/dev folders → projects. The FedRAMP High program's folder becomes an Assured Workloads folder (control packages attach at the folder). Org-wide guardrails (e.g., resource locations) attach at the org; IAM is granted at the lowest workable level.
</details>

11. Which ATT&CK technique covers an attacker moving an account out of your AWS organization to escape SCPs, and what event would you alert on?
<details><summary>Answer</summary>

T1666 Modify Cloud Resource Hierarchy. Alert on Organizations events such as `LeaveOrganization`, account moves between OUs, and policy detachments (in the management account's CloudTrail).
</details>

12. Why is a Google Cloud project often compared to an AWS account, and where does the comparison break?
<details><summary>Answer</summary>

Both are the main isolation and billing-attribution unit. But projects are lightweight and sit inside an identity-backed org where IAM inherits from above; AWS accounts are heavier, carry their own root user and IAM, and don't inherit IAM across accounts.
</details>
