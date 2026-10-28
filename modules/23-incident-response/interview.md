# 23 Interview Prep — Cloud incident response and forensics

## Likely questions

### Q1. "A customer calls: a service-account key was pushed to a public GitHub repo an hour ago. Walk me through it."

**Answer outline:**
- Check whether Google already auto-disabled it (default behavior; notice to owners/Essential Contacts).
- Preserve: export audit logs for the SA across the org (aggregated sink), hash, store in the forensics project.
- Contain: disable the key, disable or deny the SA (existing tokens last up to an hour), block key creation by org policy.
- Scope: every action since key creation — keys/roles/SAs created, discovery, data reads (only if Data Access was on), cross-project copies, sink changes, new VMs (mining), all regions.
- Eradicate persistence, replace with keyless identity (workload identity federation), rebuild from code; add secret scanning and detections.

**Strong signal:** "disable, don't delete," the token-lifetime caveat, and asking whether Data Access logs were enabled. **Avoid:** "rotate the key and we're done."

### Q2. "How is incident response different in the cloud?"

**Answer outline:**
- Evidence is API logs and snapshots, not seized hardware; collection is fast if logging was set up beforehand.
- Identity is the perimeter: containment means revoking tokens and sessions, not just passwords or keys.
- Resources are ephemeral; snapshot before autoscaling or the attacker deletes them.
- Shared responsibility: the provider handles its layers and notifies you; your identities and configs are yours.
- Attackers build persistence through the control plane (new principals, federation, roles).

### Q3. "What's in NIST SP 800-61 Rev. 3, and does it change how you work?"

**Answer outline:**
- April 2025; CSF 2.0 profile; Rev. 2 withdrawn.
- Preparation lives in Govern/Identify/Protect; IR in Detect/Respond/Recover; improvement continuous.
- Practically: same playbooks, but lessons learned feed back continuously, and IR is framed as part of enterprise risk management.
- Note many vendor guides (e.g., AWS's) still cite Rev. 2's phases.

### Q4. "An Entra Global Administrator account was phished. What do you do in the first hour?"

**Answer outline:**
- Use break-glass if needed; disable the account, revoke sessions, reset password (twice if hybrid), disable devices; CAE propagates within ~15 minutes.
- Preserve Entra sign-in/audit logs (export — default retention is short), Activity Log, Purview Audit.
- Hunt persistence: new apps/service principals and secrets, consent grants, MFA method changes, federation/domain changes (Golden SAML risk), role assignments, Azure subscription role changes.
- Report per obligations (federal: CISA within one hour).

### Q5. "What does each cloud provider offer to help with incidents?"

**Answer outline:** Google: compromised-credentials guidance, auto-disable of leaked keys, Mandiant IR and retainers, open-source Cloud Forensics Utils. AWS: Security Incident Response Guide, AWS Security Incident Response service (24/7 CIRT, metered, free tier), quarantine policy, SRA forensics account pattern. Microsoft: IR playbooks, emergency revocation guide, chain-of-custody architecture, Microsoft Incident Response.

## 60-second executive explanation

"Most cloud breaches today start with a stolen password or key, not a hacked server. When that happens, three things matter: how fast we can see what the intruder did, how completely we can cut them off, and whether we can prove what was and wasn't touched. Our plan prepares all three in advance. We keep detailed activity records for long enough to investigate, we have pre-approved procedures that shut off a compromised account without destroying the evidence, and we rebuild affected systems from our approved configurations rather than patching them by hand. We also practice: a playbook nobody has rehearsed fails at 2 a.m. And for federal reporting, we're set up to notify CISA within the required hour."

## Whiteboard prompt

Draw the first 24 hours of a compromised admin on a multicloud agency: a timeline (UTC) with detect → preserve → contain → scope → eradicate → recover → report, and for each step the specific action on Google Cloud, AWS, and Entra ID. Mark where tokens survive password resets, where evidence must already exist (Data Access, data events, Entra export), and where the forensics project/account sits.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud incident response on Google Cloud, AWS, and Azure — NIST SP 800-61 Rev. 3, cloud evidence and chain of custody, and containment playbooks for leaked credentials and compromised administrator identities."
- **After completing the lab:** "In a personal lab I ran a credential-compromise exercise: I emulated a compromised Google Cloud service account, scoped its activity from audit logs including the impersonation chain, preserved hashed evidence, contained it without deleting it, and wrote an incident timeline." Add the AWS temporary-credential exercise, VM snapshot, or Entra revocation only if you did them.
- **Still requires (cert / production experience / clearance):** leading or working real cloud incident response or digital forensics engagements, and production SOC experience. A GIAC cloud forensics certification ⚠️ (check current offerings) or the Google Professional Cloud Security Engineer would make some of this claimable. Your intelligence, targeting, and counterintelligence investigative experience is real and relevant — describe it at a publicly discussable level as investigative and analytic tradecraft, not as cloud IR experience.
