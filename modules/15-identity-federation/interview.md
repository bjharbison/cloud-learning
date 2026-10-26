# 15 Interview Prep — Federation, SSO, workload identity, Entra ID, privileged access

## Likely questions

### Q1. "Our agency uses Microsoft Entra ID with PIV cards. How would our people sign in to Google Cloud?"

**Answer outline:**
- Keep Entra as the single IdP; Conditional Access enforces phishing-resistant authentication (PIV via certificate-based auth) and device compliance.
- Two Google options: Cloud Identity with SSO to Entra (users provisioned automatically) — broadest product support; or Workforce Identity Federation — no user sync, roles granted to workforce-pool groups — check product support.
- Map Entra groups to Google IAM roles at folder/project scope; Privileged Access Manager for production admin; break-glass account outside the federation.
- Same pattern for AWS (IAM Identity Center with SAML + SCIM) if they're multi-cloud.

**Strong signal:** asking about product support for federated identities and naming the super-admin/break-glass caveat.
**Avoid:** "create Google accounts for everyone with passwords."

### Q2. "How do you get rid of service-account keys in CI/CD?"

**Answer outline:**
- Workload Identity Federation: the CI platform's OIDC token is exchanged at Google STS for a short-lived credential.
- The security control is the attribute condition (owner ID, repo, branch/environment); shared issuers like GitHub's make it mandatory.
- Grant roles directly to the principal set, or allow impersonation of a least-privilege SA.
- Then block key creation by org policy; same pattern on AWS (OIDC provider + role trust `sub` condition) and Azure (federated identity credential).
- Remaining risk: compromise of the repo itself — use branch protection and protected environments.

### Q3. "Explain SAML vs OIDC to a non-specialist."

**Answer outline:**
- Both let a trusted identity provider vouch for a user so apps don't keep their own passwords.
- SAML: older, XML, browser-centric enterprise SSO.
- OIDC: modern, JSON/JWT, built on OAuth 2.0; works for apps, mobile, and machine-to-machine federation.
- OAuth 2.0 alone is authorization (API access), not login. SCIM handles account provisioning.

### Q4. "What identity attacks worry you most, and how do you defend against them?"

**Answer outline:**
- AiTM phishing and session-cookie theft (T1557/T1539) → phishing-resistant MFA, token protection, CAE.
- MFA fatigue (T1621) → phishing-resistant methods instead of simple push approval; alert on prompt storms.
- Help-desk social engineering (T1566.004; CISA AA23-320A) → strict identity verification for resets, especially for admins.
- Consent phishing (T1528) → restrict user consent; admin consent workflow; review grants.
- Legacy/test tenants and apps (Midnight Blizzard) → inventory and policy coverage everywhere.
- Standing privilege → PIM/PAM.

**Strong signal:** citing the public reporting and the detection for each.

### Q5. "What is just-in-time access and how does each cloud do it?"

**Answer outline:**
- No standing admin; request → (approve) → time-bound elevation → automatic removal, all logged.
- Google Privileged Access Manager (entitlements and grants); Azure/Entra PIM (eligible vs active); AWS via partners or the TEAM sample on IAM Identity Center.
- Pair with Conditional Access requiring phishing-resistant MFA at activation.

## 60-second executive explanation

"Instead of giving every system its own passwords, we let one trusted identity system — the one that already checks our employees' PIV cards — vouch for people everywhere: Google Cloud, AWS, Azure, and our other applications. One place to turn access on and off, one place to enforce strong sign-in. We do the same for our software: our build pipelines prove who they are with short-lived credentials instead of stored keys that can leak. Administrators don't hold permanent admin rights; they request elevated access for a few hours, with a reason, and it expires on its own. The attacks we see in public reporting today mostly target identity — stealing sign-in sessions, tricking the help desk, or fooling users into approving apps — and this design is aimed squarely at those."

## Whiteboard prompt

Draw Entra ID (PIV via certificate-based auth, Conditional Access, PIM) as the single IdP federating to Google Cloud (Workforce Identity Federation pool → groups → IAM roles; PAM for prod), AWS (IAM Identity Center with SAML + SCIM → permission sets), and Azure (native). Add GitHub Actions federating to all three with conditions shown. Then overlay four attacks — AiTM cookie theft, MFA fatigue, help-desk reset, consent phishing — and mark the control and log source for each.

## What you can honestly claim

- **After reading + quiz:** "I've studied identity federation and SSO (SAML, OIDC, SCIM), Google Cloud workforce and workload identity federation, AWS IAM Identity Center, Microsoft Entra ID with Conditional Access and PIM, and the identity-focused attack techniques in recent public reporting."
- **After completing the lab:** "In a personal lab I configured Google Cloud Workload Identity Federation for GitHub Actions with an attribute condition restricting access to one repository and branch, granted bucket access to the federated principal set without any service-account key, and verified that tokens from another branch were rejected." Add the AWS OIDC role and Entra federated-credential sentences only if you did them.
- **Still requires (cert / production experience / clearance):** designing or operating enterprise SSO, Conditional Access, or PIM for a real organization; PIV/ICAM integration in an agency; identity incident response. Don't claim "implemented zero-trust identity" or "Entra ID administration." Your CTI work on identity-centric intrusions (if it involved them, and only at the level you can discuss publicly) is legitimate experience — describe it accurately and without classified detail. Microsoft SC-300 (Identity and Access Administrator) ⚠️ (not in `reference/certifications.md`; verify the current exam) and Google Professional Cloud Security Engineer cover this area.
