# 25 Quiz — Attack-path lab (purple team)

1. How does a purple-team exercise differ from a penetration test?
<details><summary>Answer</summary>

A pen test tries to find exploitable weaknesses and reports them. A purple team has attackers and defenders work together technique by technique to **improve detection and response** — the output is tested detections and a coverage scorecard, not just a list of holes.
</details>

2. What's the difference between emulation and simulation, and what does each actually test?
<details><summary>Answer</summary>

**Emulation** performs the real API calls, so it tests the whole chain: log generation, delivery, parsing, and the rule. **Simulation** injects or replays fake events — safer and cheaper, but it only tests the rule logic, not whether the logs arrive.
</details>

3. List four rules of engagement you'd write before running cloud emulation in your own account.
<details><summary>Answer</summary>

Any four: dedicated project/account only; only your own identities; no techniques that grant access to external principals or share resources outside the account; no organization-level or cross-project actions; cost cap (no compute/GPU); full cleanup and project deletion; a stop condition; written sign-off by the system owner.
</details>

4. Spot the problem: a learner runs `stratus detonate gcp.exfiltration.share-compute-snapshot` in their sandbox "because it's only a snapshot."
<details><summary>Answer</summary>

That technique grants an **outside "attacker" Google account** access to the snapshot — by default an account the tool's maintainers control. It moves data access outside the learner's own resources, violating the ROE. Read `stratus show` first; skip share/invite/backdoor techniques.
</details>

5. Which two of this lab's five techniques would be invisible with Google Cloud's default logging, and why?
<details><summary>Answer</summary>

**Service-account impersonation** (`GenerateAccessToken`, IAM Credentials) and **Secret Manager secret reads** (`AccessSecretVersion`). Both are **Data Access** logs, which are off by default for most services.
</details>

6. Name the four outcomes on a detection-coverage scorecard and which one is usually the most actionable.
<details><summary>Answer</summary>

Detected, Logged only, Not logged, Prevented. **Logged only** is the most actionable: the telemetry exists, so writing and testing a rule is a quick win.
</details>

7. Your IAM-001 rule fired for Stratus's admin-service-account technique but not for the Token Creator grant during the impersonation warm-up. Why?
<details><summary>Answer</summary>

IAM-001 watches `SetIamPolicy` on the **project** (`cloudresourcemanager.googleapis.com`). The Token Creator grant is an IAM policy change on a **service account** resource via `iam.googleapis.com` — a different service and resource, so the filter misses it. Resource-level IAM changes need their own rule.
</details>

8. The impersonation technique produced several "permission denied" calls followed by one success. Why is that sequence a better detection than any single event?
<details><summary>Answer</summary>

Individual `GenerateAccessToken` calls are normal for pipelines. A **burst of denials against many service accounts, then a success, from one principal** is characteristic of an attacker probing for a usable identity — a behavioral pattern that's harder to evade and lower in false positives.
</details>

9. Compare the disposable sandbox unit on each cloud and one catch for each.
<details><summary>Answer</summary>

Google Cloud: a **project** — cheap and quick; deletion is a 30-day pending state that still counts against quota. AWS: a separate **account** — needs AWS Organizations to create, which ends the AWS free plan. Azure: a separate **subscription** or resource group — a resource group shares the subscription's identity and policy scope.
</details>

10. What do Google, AWS, and Microsoft each require before you test your own cloud resources?
<details><summary>Answer</summary>

Google: no notification needed; follow the Acceptable Use Policy. AWS: listed services can be tested without prior approval under its penetration testing policy. Microsoft: no pre-approval since 2017; follow the Microsoft Cloud Penetration Testing Rules of Engagement. All forbid targeting other customers or the provider's infrastructure.
</details>

11. Scenario: an agency CISO asks how you'd prove its new SIEM rules work without risking production. What do you propose?
<details><summary>Answer</summary>

A dedicated test project/account mirroring production logging; written ROE signed by the system owner; emulate a prioritized set of techniques from current threat reporting with a recognized open-source tool; measure detection and latency per technique; deliver a scorecard and backlog; re-run on every logging or rule change (continuous validation).
</details>
