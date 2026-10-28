# 21 Interview Prep — Security posture management

## Likely questions

### Q1. "How would you give an agency CISO visibility into security posture across hundreds of Google Cloud projects?"

**Answer outline:**
- Activate Security Command Center at the **organization** level so every current and future project is covered; choose Standard vs Premium based on need (Premium for threat detection, attack path simulations, posture and compliance reporting).
- Set the benchmark: Google's security baseline, CIS GCP, NIST 800-53 mappings via Compliance Manager.
- Route findings: SCC notifications → Pub/Sub → ticketing and SIEM; owners derived from labels/folders.
- Measure: open criticals by age, time to remediate, exception count, coverage.
- Close the loop: guardrails (org policy) for the repeat offenders.

**Strong signal:** knowing SCC Enterprise was deprecated in May 2026 and not leading with it. **Avoid:** "turn on SCC and you're secure."

### Q2. "What's the difference between CSPM and CNAPP, and do customers need both?"

**Answer outline:**
- CSPM = configuration checks; CNAPP = CSPM + workload protection + entitlements + data posture + code scanning in one platform.
- Need depends on estate: container-heavy and multicloud estates benefit from CNAPP correlation (attack paths, toxic combinations); a small single-cloud estate may start with native CSPM.
- Examples: Defender for Cloud describes itself as a CNAPP; Google acquired Wiz (March 2026); AWS's new Security Hub correlates GuardDuty, Inspector, Macie, and CSPM.

### Q3. "Walk me through what happens after a critical misconfiguration finding fires."

**Answer outline:**
- Triage by exposure, blast radius, asset value — not severity alone.
- Ticket to the owner with evidence, ATT&CK context, fix, SLA, verification.
- Fix in IaC; rescan; attach audit-log proof.
- Exception path: risk owner, rationale, expiry (POA&M in federal terms).
- Prevent recurrence with a guardrail.

### Q4. "How do AWS and Azure compare with Google here?"

**Answer outline:**
- AWS: Security Hub CSPM (standards incl. CIS AWS up to v5.0.0, NIST 800-53; needs Config), GuardDuty for threats, new Security Hub (Dec 2025) for correlation and ticketing; not available on the AWS Free plan.
- Azure: Defender for Cloud — Foundational CSPM free (secure score, MCSB, AWS/GCP connectors); Defender CSPM and workload plans paid; moving into the Defender portal and Exposure Management.
- Google: SCC Standard free (needs an organization) / Premium.

### Q5. "How does posture management relate to threat intelligence?"

**Answer outline:**
- Threat reporting (e.g., Google's Cloud Threat Horizons: exploitation, weak credentials, and misconfiguration as top initial-access vectors) tells you which findings adversaries exploit now.
- Prioritize findings that match active TTPs (exposed SA keys, open management ports, public storage).
- Attackers run the same scanners; know your scanner's identity and alert on look-alike discovery (T1580/T1526).

## 60-second executive explanation

"Cloud environments change constantly, and one wrong setting — a storage bucket left open, a management port exposed to the internet — can undo every other investment. Posture management is a continuous inspection: tools from Google, Amazon, and Microsoft check every setting in every project against recognized benchmarks, every day. The value isn't the list of problems; it's what we do with it. Each finding goes to a named owner with a deadline, gets fixed in our automated configuration so it stays fixed, and anything we decide to accept is written down with an expiration date. Over time, we turn the most common problems into rules the cloud simply won't allow. That gives you a defensible, measurable picture of risk — and evidence for continuous monitoring in our authorization."

## Whiteboard prompt

Draw an agency with a Google Cloud org, an AWS organization, and an Azure tenant. Place the native posture and threat tools on each (SCC tier, Security Hub CSPM + GuardDuty + Security Hub, Defender for Cloud Foundational/Defender CSPM). Show findings flowing to one ticketing system and the SIEM, the owner lookup by labels/tags, the exception path with expiry, and the feedback arrow to guardrails (module 20). Mark which components are free.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud security posture management across Google Cloud, AWS, and Azure — Security Command Center tiers, Security Hub and GuardDuty, Defender for Cloud — plus CIS Benchmarks and how findings are triaged and remediated."
- **After completing the lab:** "In a personal lab I ran a CIS-aligned posture assessment of a Google Cloud project with the open-source tool Prowler, triaged findings by exposure, wrote and closed a remediation ticket, and verified the fix by rescanning and reviewing audit logs." Add GuardDuty sample findings or Defender secure score only if you did them.
- **Still requires (cert / production experience / clearance):** operating a posture management program, SIEM/SOAR integration, or vulnerability management in production cloud environments; Google Professional Cloud Security Engineer, AWS Certified Security – Specialty, or Microsoft AZ-500 would make the cloud-security knowledge claimable. Your assessment and inspection experience in national security environments is relevant — describe it at a publicly discussable level, and don't present it as cloud CSPM experience.
