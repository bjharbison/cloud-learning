# 15 Quiz — Federation, SSO, workload identity, Entra ID, privileged access

1. In one line each: what are SAML 2.0, OAuth 2.0, OpenID Connect, and SCIM for?
<details><summary>Answer</summary>

SAML: browser SSO using signed XML assertions from an IdP. OAuth 2.0: authorization — access tokens letting an app call an API. OIDC: an authentication layer on OAuth 2.0 that issues a signed JWT ID token. SCIM: provisioning — creating, updating, and deleting users and groups automatically.
</details>

2. What's the difference between Google Cloud Identity SSO and Workforce Identity Federation?
<details><summary>Answer</summary>

With Cloud Identity/Workspace SSO, users exist as Google accounts (synced or provisioned) and authenticate at your IdP. Workforce Identity Federation is sync-less: users from an external SAML/OIDC IdP access the console (federated) and APIs without Google accounts; you grant roles to `principal://`/`principalSet://` workforce-pool identifiers. Configured at the organization level; not every product supports it.
</details>

3. Spot the misconfiguration: a Google workload identity provider for `https://token.actions.githubusercontent.com` with no attribute condition.
<details><summary>Answer</summary>

GitHub uses one issuer for every customer, so any GitHub repository could present a valid token to the provider. Google says you must set an attribute condition — e.g., on `repository_owner_id` (numeric, harder to spoof than names), repository, and ref — and grant roles only to the specific principal set.
</details>

4. What's the AWS equivalent of that mistake?
<details><summary>Answer</summary>

A role trust policy for the GitHub OIDC provider that doesn't restrict `token.actions.githubusercontent.com:sub` (or uses `StringLike` with a broad wildcard like `repo:*`). Restrict `aud` to `sts.amazonaws.com` and `sub` to the exact repo and branch/environment.
</details>

5. Microsoft Entra: what's the difference between an app registration and an enterprise application?
<details><summary>Answer</summary>

The app registration is the application object — the app's global definition with its client ID. The enterprise application is the service principal — the app's instance in a particular tenant, where admins assign users, grant consent, and apply Conditional Access.
</details>

6. Which Entra license tier do you need for Conditional Access, and which for PIM?
<details><summary>Answer</summary>

Conditional Access: Entra ID P1. PIM (and ID Protection risk-based policies): P2 or Entra ID Governance. Security defaults are free for tenants without Conditional Access.
</details>

7. Why isn't "we require MFA" enough against AiTM phishing, and what authentication strength helps?
<details><summary>Answer</summary>

AiTM proxies the real sign-in, the user completes MFA, and the attacker steals the session cookie (T1557, T1539) — the token works without MFA. Phishing-resistant MFA (FIDO2 keys, Windows Hello for Business, certificate-based auth/PIV) is bound to the real site and defeats the relay; token protection and CAE help further.
</details>

8. Map each to an ATT&CK technique: (a) dozens of push prompts until a user approves; (b) a caller impersonates an employee to the help desk to reset MFA; (c) users grant a malicious app `Mail.Read`; (d) a stolen token-signing key used to mint SAML tokens.
<details><summary>Answer</summary>

(a) T1621 Multi-Factor Authentication Request Generation. (b) T1566.004 Phishing: Spearphishing Voice (CISA AA23-320A, Scattered Spider). (c) T1528 Steal Application Access Token (consent phishing), with later use as T1550.001. (d) T1606.002 Forge Web Credentials: SAML Tokens.
</details>

9. Compare just-in-time privileged access on the three clouds.
<details><summary>Answer</summary>

Google: Privileged Access Manager — entitlements (eligible requesters, roles, max duration, justification, approvals) and time-bound grants, auto-revoked. Azure/Entra: PIM — eligible vs active assignments, activation with MFA/justification/approval, for Entra roles, Azure resource roles, and groups. AWS: no native JIT in IAM Identity Center; AWS points to partner tools and the self-hosted TEAM sample.
</details>

10. What does OMB M-22-09 require for agency workforce authentication, and how does a PIV/CAC fit into Entra?
<details><summary>Answer</summary>

Phishing-resistant MFA for staff, contractors, and partners — PIV/derived PIV as the simplest path, FIDO2/WebAuthn where PIV isn't practical. Entra supports PIV/CAC through certificate-based authentication, which counts as phishing-resistant in its authentication strengths.
</details>

11. What was Midnight Blizzard's path into Microsoft's corporate environment, per Microsoft's January 2024 guidance?
<details><summary>Answer</summary>

A password spray against a legacy, non-production test tenant account without MFA; then compromise of a legacy test OAuth application, creation of malicious OAuth apps, and granting them high-privilege Exchange access — using residential proxies to blend in. Lessons: no unmanaged legacy tenants/apps, MFA everywhere, monitor app consents and permissions.
</details>

12. Scenario: an agency's CI pipeline stores a Google service-account JSON key as a GitHub secret. What do you recommend, step by step?
<details><summary>Answer</summary>

Create a workload identity pool and GitHub OIDC provider with a tight attribute condition (owner ID, repo, branch/environment); grant the needed roles directly to the repository's principal set (or let it impersonate a least-privilege SA if a product requires it); switch the workflow to `id-token: write` and Google's auth action; delete the old key; enforce the org policy that blocks key creation; add GitHub branch protection and environment reviewers for production deploys.
</details>
