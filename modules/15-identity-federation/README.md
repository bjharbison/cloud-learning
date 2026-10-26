# 15 — Federation, SSO, workload identity, Microsoft Entra ID, and privileged access

> **In one sentence:** you'll be able to explain how one identity provider signs people and workloads into all three clouds without passwords or keys — SAML, OIDC, SSO, workforce and workload identity federation, Microsoft Entra ID — and how just-in-time privileged access and Conditional Access blunt the token theft, consent phishing, MFA fatigue, and help-desk attacks that dominate public reporting.

**Prereqs:** modules 00–14 (module 14 for permissions; module 06 for Kubernetes workload identity; module 00 for MFA) · **Time:** ~4 hours incl. lab · **Phase:** 4

## Learning objectives

- Explain **SAML 2.0**, **OAuth 2.0**, and **OpenID Connect** in plain language, and what a **token** or **assertion** actually is.
- Describe **SSO** into each cloud from an external identity provider, with **SCIM** provisioning.
- Explain **workforce identity federation** (people) and **workload identity federation** (CI/CD, other clouds) on Google Cloud, and the AWS and Azure equivalents.
- Describe **Microsoft Entra ID** — tenants, app registrations vs enterprise apps, licensing tiers, **Conditional Access**, **PIM**.
- Compare **just-in-time** privileged access: Google **Privileged Access Manager**, Azure **PIM**, AWS **TEAM**/partners.
- Map identity attacks to **ATT&CK** and the public reporting behind them.

## Why this matters for the target roles

- **Customer engineer / architect:** nearly every agency already runs Microsoft Entra ID or Okta — and PIV/CAC. "How do our people and pipelines sign in to Google Cloud without new passwords or keys?" is a day-one question.
- **Cloud security:** federation removes stored secrets; misconfigured federation creates trust anyone can use.
- **CTI:** the most-reported intrusions of recent years — Midnight Blizzard, Scattered Spider, LAPSUS$, AiTM phishing campaigns — are identity attacks. You'll read their reports fluently after this module.

---

## Concepts

### Federation in one paragraph

**Plain version:** **federation** means one system vouches for a user, and other systems accept that vouching instead of keeping their own passwords. The **identity provider (IdP)** — Entra ID, Okta, Ping, an agency's PIV-backed IdP — authenticates the person. The **service provider (SP)** or **relying party (RP)** — Google Cloud, AWS, Azure, an app — trusts a signed statement from the IdP.

**Bridge to your intel background:** it's a liaison relationship. Your agency vouches for your clearance in a visit request; the host facility doesn't re-investigate you, it trusts the sending agency's signed statement — and only for what the statement says. The weak points are the same too: forged paperwork (token forgery), a stolen badge (token theft), and a host that trusts too broadly.

### The protocols, plainly

| | **SAML 2.0** | **OAuth 2.0** | **OpenID Connect (OIDC)** |
|---|---|---|---|
| Purpose | Authentication (SSO), mostly browser | **Authorization** — letting an app call an API on your behalf | **Authentication** layer built on OAuth 2.0 |
| Token | Signed **XML assertion** with claims | **Access token** (and refresh token) | **ID token** — a signed **JWT** with identity claims |
| Typical use | Enterprise SSO into consoles and SaaS | Delegated API access ("this app may read your mail") | Modern SSO, mobile apps, **workload federation** (GitHub Actions → cloud) |

- A **JWT** (JSON Web Token) is three Base64 parts: header, claims (issuer `iss`, subject `sub`, audience `aud`, expiry `exp`…), signature.
- **SCIM** is a REST standard for **provisioning** — creating, updating, and deleting users and groups automatically. SAML/OIDC signs people in; SCIM keeps the account list in sync, including **deprovisioning** when someone leaves.

**Homelab bridge:** if you've put Authentik, Keycloak, or Authelia in front of Grafana and Proxmox, you've run an OIDC IdP. Cloud federation is the same flow at enterprise scale.

**The security truth of all three:** whoever holds a valid, unexpired token **is** the user, until it expires or is revoked. MFA protects sign-in; it does not protect a token after it's issued. That's why token theft is the attack to understand.

### Signing people into each cloud

**Google Cloud — two models:**

1. **Cloud Identity / Google Workspace with SSO.** Users exist as Cloud Identity accounts (synced by **Google Cloud Directory Sync** from AD/LDAP, or auto-provisioned from Entra ID or Okta); sign-in is redirected to your IdP via **SAML** (Workspace also supports **OIDC** SSO profiles). Google's guidance: super admins can bypass SSO, so protect them with strong 2SV.
2. **Workforce Identity Federation.** **Sync-less**: users from any SAML 2.0 or OIDC IdP sign in to the Google Cloud console (federated) and APIs **without** Google accounts being created. Configured at the **organization** level as **workforce pools** and **providers**; you grant IAM roles to identifiers like `principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/group/GROUP`. Not every product supports federated identities — check Google's supported-services list. No added per-user cost.

Google is also enforcing **mandatory 2-Step Verification** for console sign-in: personal accounts from May 2025, enterprise non-SSO Cloud Identity accounts from October 20, 2026; federated users satisfy it through their IdP's MFA (timeline for them "to be announced").

**AWS — IAM Identity Center.** The recommended path for humans: connect an external IdP with **SAML 2.0 + SCIM**; users sign in at the **AWS access portal** and receive **permission sets** in accounts (module 00 previewed this). The **organization instance** is recommended. Older alternative: per-account **IAM SAML/OIDC identity providers** with roles.

**Azure — Microsoft Entra ID is the identity plane.** Every Azure subscription trusts one Entra tenant. External or on-prem identities arrive through Entra Connect sync or federation; Entra then signs users into Azure, Microsoft 365, and thousands of SaaS apps.

### Microsoft Entra ID essentials

- **Tenant** — the directory instance (module 03).
- **App registration** vs **enterprise application**: the registration is the app's global definition (with its client ID); the enterprise application is the **service principal** — the app's instance in *your* tenant, where admins assign users and apply policy.
- **Licensing:** **Free**, **P1** (adds **Conditional Access**), **P2** (adds **ID Protection** risk policies and **PIM**), **Entra ID Governance**, and **Entra Suite**. **Security defaults** (free) give baseline MFA for tenants without P1.
- **User consent:** Microsoft recommends allowing user consent only for **verified publishers and low-impact permissions**, with an **admin consent workflow** for everything else. New tenants default to a Microsoft-managed consent policy.

### Conditional Access: policy at sign-in

**Conditional Access** (Entra ID P1) evaluates **signals** — who, from where (IP/location), which device and its compliance state, which app, sign-in and user **risk** — and returns **block** or **grant with requirements**: MFA, an **authentication strength**, a compliant or hybrid-joined device, terms of use.

- **Authentication strengths** include **phishing-resistant MFA**: FIDO2 security keys, Windows Hello for Business / platform credentials, certificate-based authentication (PIV/CAC). The Authenticator app's phone sign-in is passwordless but **not** phishing-resistant.
- **Report-only mode** lets you test a policy on real traffic before enforcing — the same discipline as Cloud Armor preview and VPC-SC dry run.
- **Continuous Access Evaluation (CAE)** lets services revoke access quickly on critical events (account disabled, password reset, high user risk) rather than waiting for token expiry.
- **Token protection** binds sign-in session tokens to the device — GA for Windows native apps, preview elsewhere.

Google's analog is **Context-Aware Access** (access levels on identity, IP, and device state for the console and APIs); AWS relies on the IdP's policies plus IAM conditions.

### Workload identity federation: no more keys in CI/CD

Module 14 said "replace keys." This is how, for workloads that run **outside** the cloud.

**The flow (GitHub Actions → Google Cloud):**

```
 GitHub runner ──(1) request OIDC token── GitHub's issuer (token.actions.githubusercontent.com)
      │            claims: repository, repository_owner_id, ref, workflow, sub...
      ├─(2) exchange token ──► Google STS (workload identity pool + provider)
      │                         checks issuer, audience, ATTRIBUTE CONDITION
      ├─(3) short-lived Google credential (federated token, or impersonated SA token)
      └─(4) call Google APIs ── IAM checks the principal / principalSet binding
```

- **Google Cloud Workload Identity Federation** supports AWS, Azure, any OIDC or SAML IdP (GitHub, GitLab, Terraform Cloud, Kubernetes), and **X.509 certificates** (GA May 2025). You grant roles **directly** to federated principals (Google's recommended approach) or let them **impersonate** a service account where a product requires it.
- **The critical control is the attribute condition.** GitHub, GitLab SaaS, and HCP Terraform each use **one issuer for all their customers**. Google says you **must** restrict tokens — e.g., `assertion.repository_owner_id == '1234567'` — or **any** GitHub repository in the world could present a valid token to your provider. Prefer numeric IDs over names to resist re-registered or typo-squatted names.
- **AWS:** an **IAM OIDC identity provider** for `token.actions.githubusercontent.com` (audience `sts.amazonaws.com`) plus a role whose trust policy conditions on `token.actions.githubusercontent.com:sub` (e.g., `repo:ORG/REPO:ref:refs/heads/main`). For non-OIDC workloads, **IAM Roles Anywhere** uses X.509 certificates.
- **Azure:** **federated identity credentials** on an app registration or user-assigned managed identity — issuer, audience `api://AzureADTokenExchange`, and an exact subject such as `repo:ORG/REPO:ref:refs/heads/main` (no wildcards in standard credentials — Entra's *flexible* federated credentials with claim-matching expressions are in Preview; up to 20 per object).
- **GitHub change to know:** GitHub now issues **immutable subject claims** (`repo:owner@OWNER_ID/repo@REPO_ID:...`) automatically for repositories created, renamed, or transferred from July 15, 2026; older repos keep the old format until they opt in. Trust conditions must match whichever format your repo uses.

**Bridge:** the attribute condition is the "for what" line on the liaison visit request. A token from GitHub proves only "GitHub ran *some* workflow." Your condition decides *whose* workflow, on *which* branch, gets in.

### Privileged access: just in time, not all the time

**Standing privilege** — admin rights held 24/7 — is what attackers steal. **Just-in-time (JIT)** access grants elevated roles only when requested, approved, and for a set duration.

| | Google Cloud | AWS | Azure / Entra |
|---|---|---|---|
| Service | **Privileged Access Manager (PAM)** (GA Sept 2024) | No native JIT in IAM Identity Center; AWS points to **partner** tools and the **TEAM** sample solution (self-hosted) | **Privileged Identity Management (PIM)** (Entra ID P2 or Governance) |
| Model | **Entitlements** (who may request which roles, max duration, justification, optional approvers) → time-bound **grants**, auto-revoked | TEAM: request → approve (no self-approval) → temporary Identity Center account assignment | **Eligible** vs **active** assignments; activation with MFA, justification, approval; for Entra roles, Azure resource roles, and groups |
| Audit | Cloud Audit Logs | CloudTrail | Entra audit logs |

**Bridge:** this is the two-person-integrity, sign-out-the-key model. Nobody keeps the master key on their keyring; they sign it out with a reason, someone may countersign, and it goes back automatically.

> **Shared responsibility — say it plainly:** the providers run the token services, IdP platforms, and policy engines. **Which IdPs you trust, attribute conditions and trust policies, Conditional Access policies, MFA methods, consent settings, who holds standing privilege, and the help-desk reset process are always the customer's.**

---

## Text diagram — one identity plane, three clouds

```
                      Agency IdP: Microsoft Entra ID (PIV/CAC via certificate-based auth)
                      Conditional Access: phishing-resistant MFA + compliant device; PIM for admins
                         │ SAML/OIDC SSO                          │ SCIM provisioning
     ┌───────────────────┼───────────────────────────┬────────────┘
     ▼                   ▼                           ▼
 Google Cloud          AWS IAM Identity Center      Azure subscriptions
 Workforce Identity    permission sets per account  (same tenant; RBAC + PIM)
 Federation pool       (JIT via TEAM/partner)
 → groups → IAM roles
 → PAM entitlements for prod admin

 Workloads (no keys):
 GitHub Actions ─OIDC─► Google WIF provider (condition: repository_owner_id + repo + ref)
                ─OIDC─► AWS IAM OIDC provider + role trust (sub = repo:ORG/REPO:ref:refs/heads/main)
                ─OIDC─► Entra federated identity credential (exact subject)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Human SSO from external IdP | Cloud Identity/Workspace SSO (SAML; Workspace also OIDC) or **Workforce Identity Federation** (sync-less) | **IAM Identity Center** (SAML 2.0 + SCIM) | **Microsoft Entra ID** (is the IdP) | Google offers a no-sync option |
| Provisioning | GCDS; Entra/Okta connectors | SCIM into Identity Center | Entra Connect / SCIM to apps | |
| Sign-in policy | Context-Aware Access; mandatory 2SV rollout | IdP policy + IAM conditions | **Conditional Access** (P1) | Entra's is the most mature |
| Workload federation | **Workload Identity Federation** (OIDC, SAML, AWS, Azure, X.509) | IAM OIDC/SAML providers; **IAM Roles Anywhere** (X.509) | **Federated identity credentials**; managed identities | All three accept GitHub OIDC |
| JIT privileged access | **Privileged Access Manager** | Partners / TEAM sample (no native JIT) | **PIM** (P2/Governance) | AWS is the outlier |
| Federated principal syntax | `principal://` / `principalSet://` | Role ARN + trust policy conditions | Federated credential → app/managed identity | |

## Administer and monitor it

- **Sign-in and token logs:** Google Cloud Audit Logs (federated principals appear with pool identifiers) and Workspace/Cloud Identity login audit; CloudTrail `AssumeRoleWithWebIdentity` / `AssumeRoleWithSAML` and Identity Center events; **Entra sign-in logs** (interactive, non-interactive, service principal) and **audit logs**.
- **Watch:** new federated providers or trust relationships, attribute-condition changes, new app consents and service-principal credentials, PIM/PAM activations outside expected times.
- **Hygiene:** remove unused providers and apps; review consent grants; keep a monitored **break-glass** account excluded from Conditional Access (module 00).

## Security angle

1. **Workload federation without a tight condition** — trusting all of GitHub, or matching on a repo *name* that can be re-registered.
2. **AWS role trust on `token.actions.githubusercontent.com` with a wildcard `sub`** — any branch or fork may get in.
3. **Users allowed to consent to any app** — the setup for consent phishing.
4. **MFA that can be phished or fatigued** (push, SMS) for admins; no phishing-resistant authentication strength.
5. **Standing Global Admin / Owner** instead of PIM/PAM eligibility.
6. **Help desk resets MFA on a phone call** with weak identity verification.
7. **Legacy or test tenants and apps** outside policy (Midnight Blizzard's entry point).

## Threat intel angle

| Technique | ATT&CK | Public reporting |
|---|---|---|
| Password spray on a legacy test account without MFA, then abuse of an OAuth app to gain mailbox access | T1078.004; T1550.001 Use Alternate Authentication Material: Application Access Token | Microsoft, *Midnight Blizzard: Guidance for responders on nation-state attack* (Jan 25, 2024) |
| **Consent phishing** — a malicious app asks users to grant it API access | **T1528 Steal Application Access Token** | Microsoft Learn guidance on protecting against consent phishing and remediating illicit consent grants |
| **MFA fatigue** / push bombing | **T1621 Multi-Factor Authentication Request Generation** | Microsoft on DEV-0537/LAPSUS$ (Mar 2022); CISA AA23-320A Scattered Spider |
| **Help-desk social engineering** — posing as an employee to reset password/MFA | **T1566.004 Phishing: Spearphishing Voice** (plus SIM swap) | CISA **AA23-320A Scattered Spider** (Nov 2023; updated July 29, 2025 with partners) |
| **AiTM phishing** steals the session cookie after MFA | **T1557 Adversary-in-the-Middle**; **T1539 Steal Web Session Cookie** | Microsoft, *From cookie theft to BEC* (July 2022) — 10,000+ orgs targeted |
| Forged SAML tokens with a stolen signing key ("Golden SAML") | **T1606.002 Forge Web Credentials: SAML Tokens** | CISA guidance on detecting APT activity after the SolarWinds compromise (2021) |
| Changing federation trust / adding an IdP | **T1484.002 Domain or Tenant Policy Modification: Trust Modification**; **T1556.007 Modify Authentication Process: Hybrid Identity** | CISA AA21-008A, *Detecting Post-Compromise Threat Activity in Microsoft Cloud Environments* (Jan 2021) ⚠️ advisory text not re-read this run |
| Registering a device for persistence | **T1098.005 Account Manipulation: Device Registration** | |

The Cyber Safety Review Board's March 2024 report on the 2023 Microsoft Exchange Online intrusion (Storm-0558, a stolen signing key) is the long-form case study in token-signing-key risk.

**Detection ideas:** many MFA prompts denied then one approved; sign-in from a new device right after a help-desk reset; new OAuth app consent with high-privilege scopes; new service-principal credentials; new federation providers or changed attribute conditions; token use from an unfamiliar ASN shortly after interactive sign-in elsewhere (possible cookie theft).

**Bridge to your CTI work:** these campaigns rarely use malware early on. The evidence is in identity logs — sign-ins, consents, MFA events, trust changes. If you've done CI work, the help-desk vector is familiar: it's an elicitation and pretexting problem, defended with process (callback verification, in-person proofing for admins) as much as technology.

## Public sector notes

- **OMB M-22-09** (Federal Zero Trust Strategy, January 2022) requires **phishing-resistant MFA** for agency staff, contractors, and partners — **PIV/derived PIV** as the simplest path, FIDO2/WebAuthn where PIV isn't practical. No rescission was found as of this module's verification date. Microsoft documents mapping PIV/CAC to Entra **certificate-based authentication**.
- **FICAM** (idmanagement.gov) frames federal identity across five service areas — identity, credential, access, federation, governance; its **phishing-resistant authenticator playbook** is practical reading.
- **Login.gov** (GSA) is the shared SSO for the *public* to reach government sites — a different problem from workforce access.
- Zero trust (module 17) builds directly on this module's identity plane.

## Key takeaways

- Federation = the IdP vouches; the cloud trusts a signed token. SAML (XML assertions), OAuth 2.0 (authorization), OIDC (identity on OAuth; JWT ID tokens), SCIM (provisioning).
- Google: Cloud Identity SSO or sync-less **Workforce Identity Federation**; AWS: **IAM Identity Center**; Azure: **Entra ID** natively.
- **Workload identity federation** removes CI/CD keys — but only with a tight attribute condition or trust policy.
- **Conditional Access** with phishing-resistant authentication strengths, and **JIT** (PAM, PIM, TEAM/partners), shrink what a stolen identity can do.
- Today's major intrusions are identity attacks: token theft, consent phishing, MFA fatigue, help-desk social engineering.
- IdP trust, conditions, consent, MFA methods, and privileged-access design are **always the customer's**.

## Sources

- [Google Cloud — Single sign-on architecture](https://docs.cloud.google.com/architecture/identity/single-sign-on), [Federating with Entra ID](https://docs.cloud.google.com/architecture/identity/federating-gcp-with-azure-ad-configuring-provisioning-and-single-sign-on), [Synchronizing with Active Directory](https://docs.cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts)
- [Google Workspace — Set up SSO](https://knowledge.workspace.google.com/admin/apps/setting-up-sso)
- [Google Cloud — Workforce Identity Federation](https://docs.cloud.google.com/iam/docs/workforce-identity-federation) and [supported services](https://docs.cloud.google.com/iam/docs/federated-identity-supported-services)
- [Google Cloud — Workload Identity Federation with deployment pipelines](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines), [with other clouds](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds), [with X.509 certificates](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-x509-certificates), [IAM release notes](https://docs.cloud.google.com/iam/docs/release-notes), [IAM product page](https://cloud.google.com/products/iam)
- [Google Cloud — Privileged Access Manager](https://docs.cloud.google.com/iam/docs/pam-overview), [MFA requirement](https://docs.cloud.google.com/docs/authentication/mfa-requirement), [Context-aware access for console and APIs](https://docs.cloud.google.com/access-context-manager/docs/securing-console-and-apis)
- [AWS — IAM Identity Center identity sources](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-identity-source-idp.html), [organization instances](https://docs.aws.amazon.com/singlesignon/latest/userguide/organization-instances-identity-center.html), [temporary elevated access](https://docs.aws.amazon.com/singlesignon/latest/userguide/temporary-elevated-access.html), [IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), [Create an OIDC identity provider](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html), [IAM Roles Anywhere](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/introduction.html)
- [AWS Security Blog — Temporary elevated access management with IAM Identity Center](https://aws.amazon.com/blogs/security/temporary-elevated-access-management-with-iam-identity-center/)
- [GitHub Docs — Configuring OpenID Connect in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
- [Microsoft — What is Entra](https://learn.microsoft.com/en-us/entra/fundamentals/what-is-entra), [licensing](https://learn.microsoft.com/en-us/entra/fundamentals/licensing), [application objects](https://learn.microsoft.com/en-us/entra/architecture/establish-applications), [SAML](https://learn.microsoft.com/en-us/entra/architecture/auth-saml), [OIDC](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc), [SCIM](https://learn.microsoft.com/en-us/entra/architecture/sync-scim)
- [Microsoft — Conditional Access overview](https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview), [authentication strengths](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-strengths), [Continuous Access Evaluation](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-continuous-access-evaluation), [token protection](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-token-protection)
- [Microsoft — PIM](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure), [workload identity federation trust](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust), [GitHub immutable subjects](https://learn.microsoft.com/en-us/entra/workload-id/workload-identities-github-immutable-subjects), [managed identities](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)
- [Microsoft — Configure user consent](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/configure-user-consent), [app consent policies](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-app-consent-policies), [protect against consent phishing](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/protect-against-consent-phishing), [illicit consent grants](https://learn.microsoft.com/en-us/defender-office-365/detect-and-remediate-illicit-consent-grants)
- [Microsoft Security blog — Midnight Blizzard guidance (Jan 2024)](https://www.microsoft.com/en-us/security/blog/2024/01/25/midnight-blizzard-guidance-for-responders-on-nation-state-attack/), [DEV-0537 (Mar 2022)](https://www.microsoft.com/en-us/security/blog/2022/03/22/dev-0537-criminal-actor-targeting-organizations-for-data-exfiltration-and-destruction/), [AiTM phishing (Jul 2022)](https://www.microsoft.com/en-us/security/blog/2022/07/12/from-cookie-theft-to-bec-attackers-use-aitm-phishing-sites-as-entry-point-to-further-financial-fraud/)
- [CISA — AA23-320A Scattered Spider](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a) and [2025 update](https://www.cisa.gov/news-events/alerts/2025/07/29/cisa-and-partners-release-updated-advisory-scattered-spider-group), [AA21-008A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-008a), [Detecting APT activity from known TTPs (2021)](https://www.cisa.gov/sites/default/files/publications/Supply_Chain_Compromise_Detecting_APT_Activity_from_known_TTPs.pdf), [CSRB review of the Summer 2023 Exchange Online intrusion](https://www.cisa.gov/sites/default/files/2025-03/CSRBReviewOfTheSummer2023MEOIntrusion508.pdf)
- [OMB M-22-09](https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf), [idmanagement.gov M-22-09 page](https://idmanagement.gov/laws-policies-standards/m-22-09), [FICAM architecture](https://www.idmanagement.gov/arch/), [Phishing-resistant authenticator playbook](https://www.idmanagement.gov/playbooks/altauthn/), [Microsoft M-22-09 MFA guidance](https://learn.microsoft.com/en-us/entra/standards/memo-22-09-multi-factor-authentication), [Login.gov](https://www.login.gov/about-us/)
- [MITRE ATT&CK — T1528](https://attack.mitre.org/techniques/T1528/), [T1550.001](https://attack.mitre.org/techniques/T1550/001/), [T1621](https://attack.mitre.org/techniques/T1621/), [T1539](https://attack.mitre.org/techniques/T1539/), [T1557](https://attack.mitre.org/techniques/T1557/), [T1566.004](https://attack.mitre.org/techniques/T1566/004/), [T1606.002](https://attack.mitre.org/techniques/T1606/002/), [T1556.007](https://attack.mitre.org/techniques/T1556/007/), [T1484.002](https://attack.mitre.org/techniques/T1484/002/), [T1098.005](https://attack.mitre.org/techniques/T1098/005/), [T1078.004](https://attack.mitre.org/techniques/T1078/004/)

Verified: 2026-10-26
