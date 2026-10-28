# 21 Quiz — Security posture management

1. Define CSPM, CWPP, CIEM, and CNAPP in one line each.
<details><summary>Answer</summary>

CSPM: continuous checks of cloud configuration against best practice. CWPP: protection for running workloads (VMs, containers, serverless). CIEM: finding and reducing excess cloud permissions. CNAPP: an umbrella platform combining those (plus DSPM and code/IaC scanning).
</details>

2. What's the difference between a posture finding and a threat finding? Give an example of each.
<details><summary>Answer</summary>

Posture: a risky configuration exists (`OPEN_SSH_PORT`, a public bucket). Threat: malicious activity is happening (GuardDuty `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS`, an SCC Event Threat Detection finding). Posture comes from configuration/inventory; threats from logs and runtime telemetry.
</details>

3. A customer says, "We'll buy SCC Enterprise for multicloud coverage." What do you tell them (as of October 2026)?
<details><summary>Answer</summary>

SCC Enterprise was deprecated on May 21, 2026 and shuts down on or after May 21, 2027, with customers moved to Premium. Discuss current options — SCC Premium for Google Cloud, and multicloud alternatives (Google acquired Wiz in March 2026; Defender for Cloud and others have multicloud connectors) — and verify the current roadmap with Google rather than speculating.
</details>

4. True or false: you can activate SCC Standard on a personal Google Cloud project that has no organization.
<details><summary>Answer</summary>

False. Even project-level activation requires the project to belong to an organization.
</details>

5. Name AWS's three posture/threat services after the December 2025 changes and what each does.
<details><summary>Answer</summary>

AWS Security Hub (new): unified risk view correlating GuardDuty, Inspector, Macie, and CSPM signals into exposure findings and attack paths, OCSF format. AWS Security Hub CSPM (the original, renamed): posture checks against standards (FSBP, CIS, NIST 800-53), needs AWS Config. Amazon GuardDuty: threat detection from CloudTrail, VPC Flow Logs, DNS logs plus protection plans.
</details>

6. Which parts of Microsoft Defender for Cloud are free, and what's a notable capability of the free tier?
<details><summary>Answer</summary>

Foundational CSPM: secure score, recommendations, the Microsoft cloud security benchmark, asset inventory — and connectors for AWS and Google Cloud, so it gives a free native multicloud posture view. Defender CSPM (attack paths, governance, compliance dashboards, CIEM, DSPM) and workload plans are paid.
</details>

7. What do CIS Level 1 and Level 2 mean, and why should you ask "which version?" when someone claims CIS compliance?
<details><summary>Answer</summary>

Level 1: baseline, low impact. Level 2: defense in depth for high-security environments, potentially disruptive. Tools lag the benchmarks — CIS GCP is at 5.0.0 but SCC's posture template is 2.0.0; CIS AWS is at 7.1.0 but Security Hub CSPM supports up to 5.0.0.
</details>

8. Spot the problem: a team's posture dashboard shows zero critical findings. They achieved it by suppressing all findings in the dev folder and muting `OPEN_FIREWALL` everywhere because "it's noisy."
<details><summary>Answer</summary>

Suppression without owner, rationale, or expiry hides real risk; dev environments are common initial-access points; an open-firewall mute blinds them to a top exposure. Fix: documented exceptions with expiry and risk owner, tuning by context (e.g., exclude only approved IAP ranges), and coverage metrics alongside finding counts.
</details>

9. Scenario: a scanner flags an internet-open SSH rule on a Terraform-managed network. An engineer fixes it in the console. What happens next, and what should have happened?
<details><summary>Answer</summary>

The next `terraform apply` reverts the fix (or the pipeline reports drift). The fix belongs in the Terraform code via a reviewed change, then a rescan to verify — and a guardrail or alert so it can't recur.
</details>

10. Your lab account is on the AWS Free plan. Can you enable GuardDuty to try it? What can you use instead?
<details><summary>Answer</summary>

No — GuardDuty and Security Hub aren't supported on the Free plan; you'd need to upgrade (then a 30-day GuardDuty trial applies). Instead, run an open-source scanner such as Prowler from CloudShell, which uses free read-only API calls.
</details>

11. According to Google's Cloud Threat Horizons H1 2026 report, what were the top initial-access vectors in Google Cloud incidents, and where did misconfiguration rank?
<details><summary>Answer</summary>

Software/third-party exploitation (44.5%) took the top spot for the first time, then weak or missing credentials (27.2%), then misconfiguration (21%).
</details>

12. Which ATT&CK techniques look almost identical to a legitimate CSPM scan, and how do you tell them apart?
<details><summary>Answer</summary>

T1580 Cloud Infrastructure Discovery and T1526 Cloud Service Discovery (also T1619 for storage objects). Tell them apart by identity (is it your known scanner principal?), source IP, timing, and whether the burst includes `AccessDenied` errors from an identity that normally doesn't enumerate.
</details>
