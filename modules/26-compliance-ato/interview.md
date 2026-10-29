# 26 Interview Prep — Compliance: FedRAMP, DoD Impact Levels, CMMC, NIST 800-53, ATO

## Likely questions

### Q1. "Explain FedRAMP to me — and what's changed recently."

**Answer outline:**
- Government-wide program (GSA) authorizing cloud services for unclassified federal use, based on NIST 800-53 baselines; law since the 2022 FedRAMP Authorization Act.
- OMB M-24-15 (2024): presumption of adequacy, machine-readable packages, no JAB.
- FedRAMP 20x (2025–): automation-first, Key Security Indicators instead of narrative controls.
- 2026: "FedRAMP Certified," Classes A–D (C = Moderate, D = High); Consolidated Rules for 2026; Rev5 closes to new applications June 11, 2027.
- What it means for a customer: reuse existing authorizations; check service-level scope.

**Strong signal:** current terms *and* the old ones customers still use. **Avoid:** describing the JAB P-ATO as the current path.

### Q2. "What's the difference between FedRAMP High and IL5?"

**Answer outline:**
- FedRAMP High: civilian baseline (Class D) for high-impact unclassified data.
- IL5: DoD level for higher-sensitivity CUI and unclassified NSS — FedRAMP High **plus** FedRAMP+ controls, separation from non-federal tenants, DoD Cloud Access Point, personnel requirements; DISA issues a PA per offering.
- Provider models differ: Google in commercial U.S. regions with Assured Workloads; AWS in GovCloud; Azure in Azure Government (module 27).

### Q3. "A customer asks, 'If we use your FedRAMP-authorized cloud, are we compliant?'"

**Answer outline:**
- No — they inherit the provider's controls (physical, infrastructure), share some (encryption, IR), and own the rest.
- Theirs: identity and access, firewall rules, VPNs, remote access, logging configuration, key choices, application security.
- Offer help: control inheritance matrices from the provider's package, landing-zone blueprints, policy-as-code guardrails, posture tools mapped to 800-53.
- Only their AO grants the ATO.

### Q4. "How would you help a defense contractor think about CMMC and the cloud?"

**Answer outline:**
- Identify where FCI and CUI live; CUI drives Level 2 (110 requirements of 800-171 Rev 2).
- Any cloud handling CUI must be FedRAMP Moderate or equivalent (DFARS 7012; Dec 2023 memo) — hence GCC High, GovCloud, or in-scope Google services.
- Status: rules effective (Dec 2024, Nov 2025); Phase 2 suspended July 2026 — obligations under 7012 and 800-171 still apply.
- Shrink the CUI boundary (enclave) to shrink the assessment.

### Q5. "What's continuous ATO, and how does cloud help?"

**Answer outline:** cATO keeps authorization through continuous monitoring, active defense, and an approved DevSecOps pipeline. Cloud makes the evidence automatable: IaC as the configuration baseline and change record, policy as code, posture scanning mapped to 800-53, centralized audit logs, tested detections. FedRAMP 20x pushes providers the same way.

## 60-second executive explanation

"Before any government system goes live, a senior official has to formally accept its security risk — that's the Authorization to Operate. Cloud makes that faster because the provider has already been independently assessed for everything it controls: the buildings, the hardware, the underlying platform. FedRAMP is the government's program for that, and the Defense Department adds Impact Levels for more sensitive data. What the cloud doesn't do is secure our part — who has access, how our network is configured, what we log, and our own applications. So our plan is to choose services already authorized at the level we need, build guardrails that keep us inside those rules automatically, and collect evidence continuously, so the authorization is a steady process rather than a once-every-three-years scramble."

## Whiteboard prompt

Draw the inheritance stack for an IL4 agency workload on Google Cloud: provider controls (FedRAMP + DISA PA) at the bottom, shared controls in the middle, customer controls on top. Label five control IDs in the right layers (PE-3, SC-28, AU-2, AC-2, SC-7). Add the Assured Workloads folder, the DoD Cloud Access Point, and the AO signing the ATO. Show the ConMon loop.

## What you can honestly claim

- **After reading + quiz:** "I've studied federal cloud compliance — FedRAMP including the 20x changes and new classes, DoD Impact Levels, CMMC, NIST SP 800-53 and 800-171, and the RMF/ATO process — and can explain how each shapes cloud architecture."
- **After completing the lab:** "In a personal lab I drafted a System Security Plan excerpt for a Google Cloud project, mapping eight NIST SP 800-53 controls to customer, shared, and inherited responsibility with command-line evidence, built a POA&M, and parsed the 800-53 Moderate baseline in OSCAL."
- **Still requires (cert / production experience / clearance):** producing or assessing real ATO packages, working with a 3PAO or as a CMMC assessor (which requires formal training and certification), and supporting authorizations for classified systems. Your career working inside accredited national-security systems is real context — describe it at a publicly discussable level, without implying you prepared cloud ATO packages. Relevant credentials include the ISC2 CGRC ⚠️ (check current name) or a CMMC assessor certification, plus the Google Professional Cloud Security Engineer.
