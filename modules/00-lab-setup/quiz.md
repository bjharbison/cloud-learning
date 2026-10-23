# 00 Quiz — Lab environment

1. In one line each: what does "account" mean on AWS, and what are the separate equivalents on Google Cloud?
<details><summary>Answer</summary>

On AWS, the account is the identity boundary, billing unit, and resource container all at once. Google Cloud splits these into a Google Account (identity), a Cloud Billing account (billing), and a project (resources).
</details>

2. True or false: setting a $10 budget in any of the three clouds will stop resources once you reach $10.
<details><summary>Answer</summary>

False. Budgets notify. Google calls alerts-only budgets non-capping; Azure says resources aren't affected and consumption isn't stopped. Stopping spend takes automation you build or manual cleanup.
</details>

3. Match the credit offer to the cloud (as of late 2026): (a) $200 for 30 days, (b) $300 for 90 days, (c) $100 at sign-up plus up to $100 more on a 6-month free plan.
<details><summary>Answer</summary>

(a) Azure, (b) Google Cloud, (c) AWS (accounts created on or after 2025-07-15).
</details>

4. You're on the Google Cloud Free Trial and create a budget with default settings. A misconfigured VM burns $40 of usage. Why might you get no alert?
<details><summary>Answer</summary>

By default the budget counts spend after credits. The $300 credit absorbs the $40, so net spend stays near $0. Exclude credits (`--credit-types-treatment=exclude-all-credits`) to track real usage.
</details>

5. Which kind of MFA resists a convincing fake login page, and why?
<details><summary>Answer</summary>

Passkeys / FIDO2 security keys. The credential is bound to the real site's origin, so a phishing site can't capture and replay it. SMS codes and push approvals can be relayed or fatigue-bombed.
</details>

6. On AWS, why does the recommended admin setup (IAM Identity Center) lead you to enable AWS Organizations?
<details><summary>Answer</summary>

Only the organization instance of Identity Center supports permission sets, which are how you grant users access to AWS accounts. An account instance can't grant access to the account itself, and organization instances live in an AWS Organizations management account. Catch: joining AWS Organizations automatically moves a free-plan account to the paid plan — so on the free plan, an MFA-protected IAM user is the practical stopgap.
</details>

7. Spot the problem: "I gave `labadmin` the Global Administrator role in Entra ID so it can create VMs in my subscription."
<details><summary>Answer</summary>

Wrong tool, too much power. Creating VMs needs an Azure RBAC role on the subscription (e.g., Owner or Contributor). Global Administrator controls the Entra tenant itself (users, sign-in policies). Over-granting it widens the blast radius if `labadmin` is phished.
</details>

8. You run `gcloud projects delete` and realize afterward you were in the wrong project. What habit would have prevented it?
<details><summary>Answer</summary>

Run `gcloud config list` (and use named configurations) before any destructive command, and pass `--project` explicitly. Bonus: a deleted project stays in a pending-deletion state for a period and can be restored during it.
</details>

9. Scenario: an agency CIO asks, "If a staffer's cloud password leaks, what stops an attacker?" Give a two-sentence answer.
<details><summary>Answer</summary>

Mandatory, preferably phishing-resistant MFA stops most password-only takeovers, and least-privilege roles limit what a compromised identity can do. Budget and sign-in alerts give you a fast signal if something still gets through. (Identity controls are the customer's responsibility under shared responsibility.)
</details>

10. Which ATT&CK technique describes an attacker using a stolen cloud login, and which describes them mining crypto on your bill?
<details><summary>Answer</summary>

T1078.004 Valid Accounts: Cloud Accounts; T1496.001 Resource Hijacking: Compute Hijacking.
</details>

11. Why choose Azure Cloud Shell's ephemeral mode for this curriculum?
<details><summary>Answer</summary>

It needs no storage account, so it creates nothing in your subscription that you'd have to clean up or pay for. Trade-off: files don't persist between sessions.
</details>
