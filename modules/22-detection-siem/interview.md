# 22 Interview Prep — Cloud detection engineering and SIEM

## Likely questions

### Q1. "How would you build detections for a customer's Google Cloud environment?"

**Answer outline:**
- Start from requirements: threat reporting and ATT&CK cloud techniques relevant to the mission (T1078.004, T1098.001/.003, T1580, T1530, T1685.002).
- Confirm collection: Admin Activity is on by default; enable Data Access for identity, secrets, and sensitive data stores; centralize with an org aggregated sink (module 18).
- Ingest into Google SecOps (direct Google Cloud ingestion, UDM) and turn on curated Cloud Threats detections; add custom YARA-L for agency-specific logic.
- Test with emulation, manage rules as code, attach runbooks, track true-positive rates.

**Strong signal:** naming the log gap (Data Access) before naming the product. **Avoid:** "turn on the SIEM and it detects everything."

### Q2. "How does Google SecOps compare with Microsoft Sentinel and Splunk?"

**Answer outline:**
- SecOps: UDM normalization, YARA-L continuous rules, 12 months hot retention included, ingestion-based packages, curated detections and Google/Mandiant threat intel.
- Sentinel: KQL on Log Analytics, deep Microsoft 365/Entra/Defender integration, moving fully to the Defender portal by March 31, 2027; free AzureActivity and Office 365 audit ingestion.
- Splunk: SPL, broad ecosystem, common incumbent in federal SOCs.
- Migration: Sigma and detection-as-code make content portable; Google and Microsoft both publish SPL migration guides.

**Strong signal:** being fair to competitors and steering to the customer's data sources and skills.

### Q3. "Write me a detection for an attacker disabling cloud logging."

**Answer outline:** T1685.002. Google: Admin Activity `DeleteSink`/`UpdateSink`, audit-config removal in `SetIamPolicy`. AWS: `StopLogging`, `DeleteTrail`, `UpdateTrail`, `PutEventSelectors` (EventBridge for real time). Azure: diagnostic setting deletion in the Activity Log. Plus a metric-absence alert on log volume, because a deleted pipeline may simply go quiet. Reference ATT&CK Detection Strategy DET0289.

### Q4. "How do you keep false positives manageable?"

**Answer outline:**
- Narrow, documented exclusions (named pipeline identity + expected user agent), never whole classes like "all service accounts."
- Enrich with context: change tickets, asset criticality, identity type.
- Prefer behavioral rules (sequences, thresholds) for noisy atomics.
- Track per-rule outcomes; retire rules nobody acts on.

### Q5. "How would your Splunk experience transfer?"

**Answer outline:**
- SPL → KQL is nearly one-to-one (`stats`→`summarize`, `eval`→`extend`, `table`→`project`).
- SPL → YARA-L: filters → `events`, `stats by` → `match` window + `outcome`, `where` → `condition`; rules are continuous rather than scheduled.
- The analytic skills — knowing your data, baselining, tuning — are tool-independent.

**Strong signal:** being precise that the Splunk work was on enterprise/on-prem sources (if so), and that the cloud log sources are what you've studied and labbed.

## 60-second executive explanation

"In the cloud, most attacks don't involve malware on a computer. They look like someone logging in with stolen credentials, quietly giving themselves extra permissions, and turning off the logs. All of that leaves a trail in the cloud's audit records — if we collect them and know what to look for. Detection engineering is the discipline of turning what we know about adversaries into specific, tested alerts on those records. Google, Microsoft, and others offer security operations platforms that store the data and run those alerts at scale. The important decisions are ours: which records to collect, which threats matter to our mission, and making sure every alert comes with clear instructions for the analyst who receives it."

## Whiteboard prompt

Pick one threat — "stolen service-account credentials used to add a key and read a sensitive bucket." Draw the ATT&CK chain (T1078.004 → T1098.001 → T1530), the log source for each step (Admin Activity; Data Access — note it must be enabled), and the detection for each in YARA-L and KQL. Show where the alert goes (case + runbook) and how the rule is tested and deployed as code.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud detection engineering — the ATT&CK cloud matrices and Detection Strategies, Google Security Operations with YARA-L, Microsoft Sentinel with KQL, and AWS detection building blocks — and can map threats to the cloud audit logs that reveal them."
- **After completing the lab:** "In a personal lab I wrote detection specifications as code, hunted Google Cloud audit logs, deployed and validated log-based detections by emulating the behaviors, and translated the logic into YARA-L, KQL, and SPL." Add the Azure KQL and AWS pattern tests only if you ran them. Be clear that YARA-L was written, not run (no SecOps access).
- **Still requires (cert / production experience / clearance):** operating a production SIEM or SOC detection program, or running Google SecOps or Sentinel at enterprise scale; Microsoft SC-200 or Google Professional Cloud Security Engineer would make the platform knowledge claimable. Your Splunk Core User certification and prior analytic work are real — describe the Splunk work as it actually was (on-prem/enterprise data, at a publicly discussable level), not as cloud SIEM experience.
