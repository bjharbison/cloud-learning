# 26 Quiz — Compliance: FedRAMP, DoD Impact Levels, CMMC, NIST 800-53, ATO

1. Put the seven RMF steps (NIST SP 800-37 Rev. 2) in order.
<details><summary>Answer</summary>

Prepare → Categorize → Select → Implement → Assess → Authorize → Monitor.
</details>

2. What three documents make up the core of an authorization package, and who signs the ATO?
<details><summary>Answer</summary>

The **System Security Plan (SSP)**, the **Security Assessment Report (SAR)** (with its plan), and the **POA&M**. The agency's **Authorizing Official (AO)** signs, accepting residual risk; in DoD the AO must be a government official.
</details>

3. FedRAMP's 2026 designations: what are Classes B, C, and D equivalent to, and what's the new label?
<details><summary>Answer</summary>

B = LI-SaaS + Low, C = Moderate, D = High (Class A is a new pilot baseline). The label is **"FedRAMP Certified"** (Certification) instead of "Authorized."
</details>

4. What did OMB M-24-15 (July 2024) change? Name two things.
<details><summary>Answer</summary>

Any two: rescinded the 2011 memo and re-established FedRAMP; a **presumption of adequacy** for existing authorizations; agency and program authorization types (no JAB); push to **machine-readable** packages (naming OSCAL); reliance on provider change processes; scope limited to unclassified, non-national-security systems.
</details>

5. What is a FedRAMP 20x **Key Security Indicator**, in one sentence?
<details><summary>Answer</summary>

A capability-level security requirement (abstracted over 800-53 controls) that a provider proves, ideally with automated, machine-validated evidence, instead of long narrative control descriptions.
</details>

6. Match the data to the DoD Impact Level: (a) CUI, (b) public information, (c) SECRET, (d) unclassified National Security Systems.
<details><summary>Answer</summary>

(a) IL4; (b) IL2; (c) IL6; (d) IL5. Top Secret is outside the SRG (IC accreditation under ICD 503).
</details>

7. Spot the error: "Our app runs on a FedRAMP High cloud, so it's FedRAMP High compliant and the agency can skip its own ATO."
<details><summary>Answer</summary>

The provider's authorization covers only the controls the provider implements, which the agency **inherits**. The agency still needs its **own ATO**, covering customer controls — identity, access, firewall rules, VPN, logging, keys, the application. Using in-scope services is necessary, not sufficient.
</details>

8. CMMC: how many requirements at Level 1 and Level 2, from which sources, and what happened in July 2026?
<details><summary>Answer</summary>

Level 1: **15** requirements from FAR 52.204-21. Level 2: **110** from NIST SP 800-171 **Rev. 2**. Level 3 adds 24 from SP 800-172. On **July 13, 2026**, the department suspended **Phase 2** (third-party Level 2 assessments due Nov 10, 2026); Phase 1 self-assessments and underlying obligations remain.
</details>

9. A defense contractor wants to store CUI in a SaaS tool that has no FedRAMP authorization but encrypts everything. Is that acceptable under DFARS 252.204-7012?
<details><summary>Answer</summary>

No. The cloud service must meet **FedRAMP Moderate or equivalent** (per DoD's December 2023 equivalency memo); DoD's CMMC FAQ says encrypting the CUI doesn't remove that requirement.
</details>

10. What is a continuous ATO (cATO), and what three competencies did DoD's 2022 memo require?
<details><summary>Answer</summary>

An ATO maintained through ongoing evidence instead of periodic reauthorization. Required: continuous monitoring of RMF controls, active cyber defense, and an approved DevSecOps reference design/pipeline.
</details>

11. Scenario: an agency needs IL5 for a new analytics workload and wants to stay in Google Cloud commercial regions. What do you tell them, and what do you check?
<details><summary>Answer</summary>

Google Cloud holds an IL5 PA for in-scope services in U.S. regions, using an **Assured Workloads** IL5 control package on a folder (premium tier). Check each planned service on Google's FedRAMP/DoD scope page, plan the DoD Cloud Access Point path, customer-managed keys and logging requirements — and remind them the mission owner still issues the ATO.
</details>

12. Why is NIST SP 800-171 Rev. 3 not what CMMC assessors use today?
<details><summary>Answer</summary>

The CMMC rule and DFARS clauses reference **Rev. 2** (applied through a class deviation); moving to Rev. 3 (May 2024) requires future rulemaking.
</details>
