# 27 Quiz — Government clouds

1. Name the three delivery models for government cloud and one example of each.
<details><summary>Answer</summary>

**Controls on commercial regions** (Google Assured Workloads); **separate government partition/instance** (AWS GovCloud (US), Azure Government); **isolated classified regions** (AWS Secret/Top Secret regions, Azure Government Secret/Top Secret, Google Distributed Cloud air-gapped).
</details>

2. What does an Assured Workloads control package actually do to the projects in its folder? Name three controls.
<details><summary>Answer</summary>

Any three: restricts resource **locations** (org policy); restricts **services** to those in scope; routes **support** to screened U.S. personnel (Assured Support, with Enhanced/Premium Support); key-management requirements (CMEK/EKM; ITAR needs a separate key project); Access Transparency / Access Approval / Key Access Justifications; **violation monitoring**.
</details>

3. Which U.S. Assured Workloads packages are free, and what do FedRAMP High and IL5 cost?
<details><summary>Answer</summary>

Free: US Data Boundary, Data Boundary for FedRAMP Moderate, US Data Boundary for Healthcare and Life Sciences. FedRAMP High, IL2, IL4, IL5, CJIS, ITAR, and IRS 1075 are Premium at **20% of spend inside the folder**; the "…and Support" packages are 5%.
</details>

4. True or false: Google Workspace holds IL5.
<details><summary>Answer</summary>

**Not as held, per Google's scope page (Oct 2026).** Google Cloud holds IL5 for in-scope services; Google Cloud and Workspace hold FedRAMP High, IL2, and IL4; several Workspace services show IL5 "in DISA review." Don't claim it until the page says so.
</details>

5. What are the two AWS GovCloud regions, and how can you tell from an ARN that a resource is in GovCloud?
<details><summary>Answer</summary>

`us-gov-west-1` (US-West) and `us-gov-east-1` (US-East). GovCloud ARNs start with **`arn:aws-us-gov:`** (a separate partition) instead of `arn:aws:`.
</details>

6. Spot the problem: "We'll put our GovCloud accounts into our existing AWS Organization so we can use the same SCPs."
<details><summary>Answer</summary>

GovCloud accounts need **their own AWS Organization** in the GovCloud partition; they can't share one with commercial accounts. SCPs, Identity Center, and logging have to be set up separately there.
</details>

7. List Azure Government's regions and which are DoD-only.
<details><summary>Answer</summary>

US Gov Virginia, US Gov Arizona, US Gov Texas (federal, state, local, and partners; FedRAMP High, IL2/4/5) and **US DoD Central** and **US DoD East** (exclusively DoD; IL5).
</details>

8. Match the classified offering to its provider and level: Secret-West; Azure Government Secret; GDC air-gapped; Top Secret-West.
<details><summary>Answer</summary>

Secret-West → AWS, SECRET (ICD 503 and IL6; available Oct 2025). Azure Government Secret → Microsoft, IL6/ICD 503 (2020). GDC air-gapped → Google, Top Secret and Secret (Apr 2024) and IL6 (May 2025). Top Secret-West → AWS, TOP SECRET under ICD 503 (announced Dec 2021).
</details>

9. Is IL6 the same thing as Top Secret? Explain.
<details><summary>Answer</summary>

No. **IL6** is DoD's level for classified up to **SECRET**. Top Secret cloud is accredited under IC policy (**ICD 503**), outside the DoD SRG's Impact Levels.
</details>

10. Summarize JWCC in three facts.
<details><summary>Answer</summary>

Awarded **Dec 7, 2022** to **Google, Oracle, AWS, and Microsoft**; IDIQ contracts sharing a **$9B** ceiling, estimated to run to **June 2028**; covers **unclassified, SECRET, and TOP SECRET** out to the tactical edge, with DoD components placing task orders.
</details>

11. Scenario: an agency CIO asks, "Why doesn't Google have a GovCloud?" Give a fair two-part answer.
<details><summary>Answer</summary>

Google's model applies FedRAMP High and IL2/4/5 controls (location, service, personnel, keys) to **commercial U.S. regions** through Assured Workloads — fewer feature gaps, one identity plane, faster access to new services. The trade-off: it's a policy boundary, not a physically separate environment, premium packages add cost, and some customers' policies prefer separate infrastructure. For SECRET and above, Google offers **GDC air-gapped**.
</details>

12. Why must an application change before moving from commercial Azure to Azure Government?
<details><summary>Answer</summary>

Different **endpoints** (`portal.azure.us`, `management.usgovcloudapi.net`, `login.microsoftonline.us`), a **separate Entra tenant** and identities, and possibly missing services or features — check Microsoft's Azure Government vs global Azure comparison.
</details>
