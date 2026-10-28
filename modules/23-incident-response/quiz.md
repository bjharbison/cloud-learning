# 23 Quiz — Cloud incident response and forensics

1. What is the current revision of NIST SP 800-61, and how does it organize incident response?
<details><summary>Answer</summary>

Rev. 3 (April 2025; Rev. 2 withdrawn). It's a CSF 2.0 Community Profile: Govern, Identify, and Protect cover preparation; Detect, Respond, and Recover are incident response; improvement runs continuously across all of them.
</details>

2. Name the four phases of the older Rev. 2 lifecycle and one widely used cloud guide that still follows it.
<details><summary>Answer</summary>

Preparation; Detection & Analysis; Containment, Eradication & Recovery; Post-Incident Activity. The AWS Security Incident Response Guide says it follows Rev. 2.
</details>

3. List four kinds of cloud evidence and which one must be enabled *before* the incident to be useful.
<details><summary>Answer</summary>

Control-plane audit logs, sign-in logs, flow logs, disk snapshots (also config history and object versions). Data-plane audit (Google Data Access logs, CloudTrail data events, Azure resource logs) must be enabled beforehand; Entra sign-in logs must be exported to outlast 7/30 days.
</details>

4. Spot the problem: during an incident, the responder deletes the compromised service account and the VM it created, then starts investigating.
<details><summary>Answer</summary>

Evidence destroyed: the VM's disk is gone (no snapshot), and deleting the SA complicates correlation. Correct order: snapshot and export logs, then disable the SA (and deny/isolate), investigate, and delete only during eradication.
</details>

5. On Google Cloud, you disable a compromised service account. Is the attacker locked out immediately? What else can you do?
<details><summary>Answer</summary>

Not necessarily — access tokens already issued remain valid until they expire (up to about an hour). Apply an IAM deny policy for immediate effect, remove Token Creator grants, and wait at least 60 minutes before re-enabling.
</details>

6. On AWS, you set a leaked access key to Inactive. Why might the attacker still have access, and how do you stop it?
<details><summary>Answer</summary>

They may have minted temporary credentials (`GetSessionToken`/`AssumeRole`) from the key. Change permissions — an explicit deny on the user, the quarantine policy, or "Revoke active sessions" for roles (`AWSRevokeOlderSessions`) — because permissions are evaluated on every request.
</details>

7. What does Microsoft's emergency-revocation guidance say to do for a compromised cloud-only Entra user?
<details><summary>Answer</summary>

Disable the account, revoke sign-in sessions (refresh tokens and session cookies via `revokeSignInSessions`), reset the password, and disable registered devices (Intune wipe if needed). For hybrid accounts, disable in AD and reset the password twice. CAE propagates critical events to supporting apps within about 15 minutes.
</details>

8. After resetting a compromised admin's password and revoking sessions, the attacker returns a week later. Name three persistence paths you should have checked.
<details><summary>Answer</summary>

Any three of: new service accounts/users/service principals with credentials (T1136.003, T1098.001); new role grants (T1098.003); new or modified federation trusts (T1556.007, T1606.002); OAuth app consent grants; roles assumable from outside accounts; new access keys; functions or VMs running attacker code; changes to guardrails or logging (T1666, T1685.002).
</details>

9. What do Google and AWS do automatically when a credential is found exposed publicly?
<details><summary>Answer</summary>

Google auto-disables leaked SA keys by default (`iam.serviceAccountKeyExposureResponse`, `DISABLE_KEY` since June 2024) and notifies contacts. AWS attaches the `AWSCompromisedKeyQuarantineV3` managed policy to the exposed IAM user (as part of a support case) — don't remove it.
</details>

10. Describe cloud chain of custody in four steps.
<details><summary>Answer</summary>

Export logs/snapshot metadata to a separate forensics project/account; compute and record hashes (SHA-256); store in versioned, retention-locked/immutable storage with restricted access; document every action (your own actions also appear in the audit log). Microsoft's reference architecture adds legal hold and hashes in Key Vault.
</details>

11. A federal agency confirms an incident at 14:00. By when must it report to CISA, and what's the status of CIRCIA?
<details><summary>Answer</summary>

Within one hour (by 15:00) under CISA's Federal Incident Notification Guidelines. CIRCIA (72-hour incident / 24-hour ransom-payment reporting for covered critical infrastructure) isn't in effect yet — its final rule went to OIRA review on October 1, 2026.
</details>

12. Name each provider's IR service or team.
<details><summary>Answer</summary>

Google Cloud: Mandiant Incident Response (and retainer). AWS: AWS Security Incident Response (24/7 CIRT; first 10,000 findings/month free). Microsoft: Microsoft Incident Response (formerly DART).
</details>
