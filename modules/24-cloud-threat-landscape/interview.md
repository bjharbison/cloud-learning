# 24 Interview Prep — Cloud threat landscape for CTI

## Likely questions

### Q1. "How are adversaries actually getting into cloud environments right now?"

**Answer outline:**
- Mostly **identity**, not exploits against the provider: stolen or sprayed credentials, MFA fatigue, help-desk social engineering, OAuth app abuse, stolen tokens.
- Cite one stat with its source: Google's *Cloud Threat Horizons H1 2026* says identity compromise underpinned 83% of incidents it reviewed in major cloud and SaaS environments.
- Then misconfiguration and exposed services; increasingly, third-party integrations (Salesloft Drift tokens, 2025).
- Once in, they persist through the **control plane**: new keys, roles, federation trusts, VMs.

**Strong signal:** a named case per point, with the reporting organization. **Avoid:** "zero-days in the hypervisor" as the headline risk.

### Q2. "Walk me through Storm-0558 and what the CSRB concluded."

**Answer outline:**
- 2023: a China-based actor (Microsoft, moderate confidence) used a stolen consumer signing key to forge tokens for Exchange Online; about 25 organizations affected per Microsoft.
- A federal agency caught it via MailItemsAccessed in premium audit logs (AA23-193A).
- CSRB (released April 2024): preventable; Microsoft culture deprioritized enterprise security; recommended default logging at no extra cost, stronger key management, better transparency, and FedRAMP updates.
- Microsoft later said it never found the crash dump it first hypothesized as the source.

**Strong signal:** separating fact from hypothesis, and drawing the customer lesson (visibility, ask about key custody). **Avoid:** gloating about a competitor — a Google CE should be factual and fair.

### Q3. "A customer asks what Scattered Spider means for their Google Cloud environment."

**Answer outline:**
- Their entry point is people: help desk, MFA resets, SIM swaps — so start with phishing-resistant MFA (FIDO2/passkeys), verified reset procedures, and removing SMS factors.
- In cloud they create persistence: federation trusts, new MFA devices, VMs, keys. On Google Cloud that's Admin Activity (`instances.insert`, `CreateServiceAccountKey`, `SetIamPolicy`) plus Cloud Identity / Workspace admin audit.
- Detections for each (module 22), org policies to block SA keys and restrict who can create VMs (module 20).
- Cite CISA AA23-320A (updated July 2025) and Mandiant's UNC3944 hardening guide.

### Q4. "How do you turn threat intelligence into something a SOC can use?"

**Answer outline:**
- Extract TTPs → ATT&CK IDs → detection strategies → log sources → check collection gaps → write and test rules.
- IOCs as enrichment: STIX/TAXII into Sentinel, GuardDuty threat lists, SecOps IOC matching — with expiry.
- Deliver a product for each audience: exec BLUF, engineer appendix with queries.
- Measure: did the rule fire in emulation (module 25)?

### Q5. "What threat-intel capabilities does each cloud provider bring?"

**Answer outline:** Google: Google Threat Intelligence (Mandiant + VirusTotal + telemetry), GTIG reporting, Applied Threat Intelligence in SecOps. Microsoft: Microsoft Threat Intelligence reporting; Defender TI capabilities now inside Defender XDR and Sentinel; TAXII and upload API. AWS: intel embedded in GuardDuty (including Extended Threat Detection) and automatic protections from MadPot/Mithra/Sonaris; bring-your-own threat entity lists.

### Q6. "How do you handle attribution when vendors disagree?"

**Answer outline:** treat names as source-specific clusters; map overlaps explicitly; attribute each assessment and its confidence; distinguish government attribution (e.g., NCSC-UK and partners on APT29/SVR) from vendor assessments; say what's unknown.

## 60-second executive explanation

"Almost every major cloud breach of the last few years started the same way: someone got hold of a valid identity. Sometimes it was a stolen password on an old test account with no multi-factor sign-in. Sometimes it was a phone call to the help desk pretending to be an employee. Once inside, the intruders didn't need malware — they used the cloud's own admin features to give themselves more access and copy data out. The good news is that the defenses are known: strong, phishing-resistant sign-in for everyone, careful help-desk procedures, tight control over which apps can reach our data, and the right activity logs so we can see it happening. I'd focus our next quarter's investment there."

## Whiteboard prompt

Draw a three-column board — **Initial access → Persistence/escalation → Objective** — and place Storm-0558, APT29, UNC5537, and Scattered Spider on it. Under each, write one ATT&CK ID, the log that would show it on Google Cloud and on Entra ID, and one control that breaks the chain. Circle the step where each case was (or could have been) detected.

## What you can honestly claim

- **After reading + quiz:** "I've studied recent nation-state and criminal intrusions into cloud and identity platforms — including Storm-0558 and the CSRB report, Midnight Blizzard's intrusion into Microsoft, the 2024 Snowflake-customer campaign, Scattered Spider, and Volt Typhoon — and can discuss their techniques, ATT&CK mappings, and defensive lessons."
- **After completing the lab:** "In a personal lab I converted a CISA advisory into a cloud intel-to-detection matrix across Google Cloud, AWS, and Entra ID, hunted my own audit logs for those techniques, packaged indicators in STIX 2.1, and wrote an attributed intelligence brief."
- **Still requires (cert / production experience / clearance):** cloud-specific CTI or SOC experience in a production environment, and work with non-public provider or government threat data. Your all-source, targeting, CI, and CTI career is real analytic experience — describe it at a publicly discussable level as intelligence tradecraft, and don't present lab work as operational cloud threat hunting. A cloud security certification (module 22's list) would add a claimable credential.
