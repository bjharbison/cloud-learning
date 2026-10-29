# 25 Interview Prep — Attack-path lab (purple team)

## Likely questions

### Q1. "How would you validate that a customer's cloud detections actually work?"

**Answer outline:**
- Start from threat reporting relevant to them (module 24) → prioritized ATT&CK techniques.
- Run emulation in a **dedicated** project/account that mirrors production logging, under written ROE.
- Use a recognized open-source tool (Stratus Red Team for cloud control-plane techniques; Atomic Red Team for others).
- For each technique: was it logged, did a rule fire, how fast, with what context?
- Deliver a scorecard and a backlog; re-run whenever logging or rules change.

**Strong signal:** naming the logging prerequisite (Data Access / data events) and the ROE. **Avoid:** "we'd run a pen test."

### Q2. "What are the risks of running attack tools in the cloud, and how do you control them?"

**Answer outline:**
- Blast radius: tools can affect real resources — isolate in a throwaway project/account.
- Some techniques share resources with external accounts by default — read each technique, exclude those.
- Cost: compute or GPU techniques — exclude or cap.
- Credentials: the emulation identity is powerful — use short-lived credentials, never reuse.
- Leftovers: tool cleanup can fail — delete the whole project/account.

### Q3. "Tell me about a gap you found."

**Answer outline (from your lab, if you did it):**
- "A rule watching project-level IAM changes missed a role grant on a service account itself, because that's a different API and resource."
- "Service-account impersonation and secret reads were invisible until I enabled Data Access logs."
- What you'd do: add resource-level IAM rules; scope Data Access logging to high-value services.

**Strong signal:** concrete and honest about scale — a personal lab, five techniques.

### Q4. "How is cloud emulation different from endpoint emulation?"

**Answer outline:** cloud techniques are API calls to the control plane, not processes on a host; telemetry is audit logs, not EDR; the identity, not the machine, is the actor; cleanup is deleting resources; provider policies govern what's allowed.

### Q5. "What would you test first for a federal civilian agency?"

**Answer outline:** identity-plane persistence (new keys, roles, federation, MFA methods), log tampering (T1685.002), and secrets access — drawn from CISA advisories like AA23-320A and the SVR cloud advisory; then data exfiltration paths. Tie each to a log the agency must have per OMB M-21-31 (module 18).

## 60-second executive explanation

"We spend a lot on security monitoring, but most organizations never check whether their alarms actually go off. A purple-team exercise does exactly that. In an isolated copy of our environment, a small team safely performs the same actions real attackers use — creating hidden admin accounts, stealing keys, turning off logging — and then checks whether our monitoring noticed, how fast, and with enough detail to act. The result is a simple scorecard: what we catch, what we'd only find by searching, and what we'd miss entirely. Each miss becomes a short, concrete fix. Run quarterly, it turns 'we think we're covered' into 'we've tested it.'"

## Whiteboard prompt

Draw a sandbox project with three lanes — **Red** (tool and five techniques), **Logs** (Admin Activity vs Data Access), **Blue** (rules, alerts, hunts). Draw an arrow for each technique to the log it lands in and the rule that should catch it. Mark the two that vanish if Data Access is off, and the one rule gap (resource-level IAM). Add the ROE box and the "delete project" exit.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud purple teaming and adversary emulation — rules of engagement, Stratus Red Team's lifecycle, and how to score detection coverage against ATT&CK."
- **After completing the lab:** "In a personal lab I ran a purple-team exercise in a dedicated Google Cloud project: I emulated five cloud techniques with Stratus Red Team, found each in the audit logs, tested log-based detections mapped to ATT&CK, scored coverage, and identified gaps."
- **Still requires (cert / production experience / clearance):** red-team, purple-team, or detection-engineering work in a production or customer environment, under a real authorization. A lab exercise is not an operational assessment. Certifications such as a GIAC cloud or purple-team credential ⚠️ (check current offerings) or the Google Professional Cloud Security Engineer would add a claimable credential.
