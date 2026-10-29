# 27 Interview Prep — Government clouds

## Likely questions

### Q1. "How does Google Cloud support FedRAMP High and IL5 workloads?"

**Answer outline:**
- **Assured Workloads**: a folder with a control package (Data Boundary for FedRAMP High, IL4, IL5, …) on commercial **U.S. regions**.
- Enforced by org policy (locations, services), screened support (Assured Support), key controls (CMEK/EKM, Key Access Justifications), Access Transparency and Access Approval, violation monitoring.
- Authorizations: FedRAMP High; DISA IL2/IL4; IL5 for in-scope Google Cloud services — check the scope page per service.
- Pricing: premium packages at 20% of in-folder spend; free tier for US Data Boundary and FedRAMP Moderate.
- For classified: GDC air-gapped (module 28).

**Strong signal:** "check the scope page per service," and naming the cost honestly. **Avoid:** "everything in Google Cloud is IL5."

### Q2. "Compare Google's approach with AWS GovCloud and Azure Government."

**Answer outline:**
- AWS and Azure: separate partitions/instances — separate identities, endpoints, consoles; U.S.-screened operations; eligibility gates.
- Google: policy boundary on commercial regions — same identity plane and APIs, fewer parity gaps.
- Trade-offs: separation vs feature velocity and operational simplicity; customer policy may prefer physical separation.
- All three: identity, access, firewalls, VPNs, remote access remain the customer's.

**Strong signal:** fair to competitors, specific about trade-offs.

### Q3. "What's JWCC, and why does it matter to a Google CE?"

**Answer outline:** DoD's multi-vendor cloud contract (Dec 2022; Google, Oracle, AWS, Microsoft; shared $9B ceiling; unclassified through TOP SECRET; tactical edge; runs to ~2028). It's how DoD components buy cloud quickly through task orders — so a CE's DoD pipeline runs through it. Follow-on plans ("JWCC Next") have been reported in the press; verify before citing.

### Q4. "A defense contractor asks where to put CUI: GCC High, GovCloud, or Google Cloud?"

**Answer outline:**
- Requirement: FedRAMP Moderate or equivalent for the cloud service (DFARS 7012; module 26); many choose High/IL4-level environments for ITAR or customer requirements.
- Options: Microsoft 365 GCC High (collaboration, FedRAMP High, ITAR support); AWS GovCloud; Google Cloud with an Assured Workloads package (FedRAMP Moderate free tier; ITAR/IL4 premium).
- Decide by workload (email/collaboration vs data platform), existing identity, ITAR needs, and cost; minimize the CUI boundary.

### Q5. "What's available at SECRET and TOP SECRET today?"

**Answer outline:** AWS: Secret Region, Secret-West (Oct 2025, IL6), Top Secret-East (2014) and -West (2021). Microsoft: Azure Government Secret (IL6, 2020) and Top Secret (2021). Google: GDC air-gapped — TS/Secret authorization (Apr 2024), IL6 (May 2025). Oracle reports national security regions authorized for TS. All reached only from classified networks. Say "as of" with a date.

## 60-second executive explanation

"All three major cloud providers serve government, but they do it differently. Amazon and Microsoft built separate government clouds — separate data centers, separate accounts, separate sign-in. Google instead applies government controls to its regular U.S. regions: a protected folder that keeps data in the U.S., limits which services can be used, and restricts support to screened U.S. staff. Google's approach means fewer missing features and one set of accounts to manage; the separate-cloud approach gives physical separation that some policies prefer. For classified work, all three — plus Oracle — offer isolated, air-gapped options, and the Defense Department can buy from all four through one contract, JWCC. Our job is to match the workload's data sensitivity to the right option, then secure our own part of it."

## Whiteboard prompt

Draw a classification ladder (IL2 → IL4/High → IL5 → SECRET/IL6 → TOP SECRET) with three columns — Google, AWS, Azure. Place each offering with its year. Draw the Google column as a folder boundary inside commercial regions, the AWS and Azure columns as separate boxes with their own identity planes. Add JWCC across the top and "customer responsibilities" across the bottom.

## What you can honestly claim

- **After reading + quiz:** "I've studied how Google, AWS, and Microsoft deliver cloud to U.S. government customers — Assured Workloads, AWS GovCloud and classified regions, Azure Government and its classified clouds — and the JWCC contract, and can compare their trade-offs."
- **After completing the lab:** "In a personal lab I [created a free-tier Google Cloud Assured Workloads boundary and confirmed it blocked non-U.S. resources / mapped Assured Workloads compliance regimes to packages and pricing], compared AWS and Azure government partitions and endpoints, and built a sourced IL5 service-scope matrix across the three providers."
- **Still requires (cert / production experience / clearance):** designing or operating workloads in GovCloud, Azure Government, or IL5 Assured Workloads environments for a real customer; any work on classified regions (which requires a clearance and access); contract and capture experience with JWCC. Your national-security career gives you real context on classified environments — describe it at a publicly discussable level and don't imply classified cloud experience you don't have.
