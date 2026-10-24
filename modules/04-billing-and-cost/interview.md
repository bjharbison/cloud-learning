# 04 Interview Prep — Billing, quotas, and cost governance

## Likely questions

### Q1. "Our agency has a fixed budget. How do we make sure cloud spend doesn't exceed it?"

**Answer outline:**
- Be honest first: no major cloud offers a native hard cap on a paid account. Budgets alert; they don't stop spend.
- Layer controls: quotas sized to the funded ceiling; autoscaling with explicit maximums; budgets with forecast-based alerts set early; anomaly detection.
- Automated response that **freezes** rather than kills: AWS Budgets actions (deny SCP/IAM), or a Pub/Sub- or action-group-triggered function that blocks new resources.
- Labels by program/CLIN so finance sees consumption against each funding line.

**Strong signal:** naming the Antideficiency Act and explaining why "freeze, don't kill" protects mission data.
**Avoid:** "set a budget and it'll stop at the limit."

### Q2. "How would you do chargeback across 15 programs on Google Cloud?"

**Answer outline:**
- Structure first: folders/projects per program (module 03) — the strongest cost boundary.
- A required label set (`program`, `env`, `cost-center`), enforced by policy and checked in CI (module 20).
- Billing export to BigQuery; reports grouped by project and label; untagged spend reviewed weekly.
- Showback before chargeback, so teams trust the numbers.

**Strong signal:** "projects are the primary boundary; labels are the second axis."

### Q3. "What's the difference between a CUD and a Savings Plan? Should we buy one?"

**Answer outline:**
- Both trade a 1- or 3-year commitment for a discount. Resource-based (specific capacity) vs spend-based (flexible dollar amount) exists on all three clouds in some form.
- Google also gives automatic sustained use discounts on eligible machine series.
- Buy only for a stable baseline, after a few months of usage data.
- Public sector: check the contract — many government contracts don't allow 3-year commitments.

**Avoid:** quoting a specific discount percentage without checking the current pricing page.

### Q4. "How does billing data help security?"

**Answer outline:**
- A spend spike on unfamiliar SKUs or regions is a classic sign of credential compromise (T1496.001 compute hijacking; T1496.004 cloud service hijacking, e.g., AI APIs).
- Anomaly detection on all three clouds, routed to the SOC as well as finance.
- Quotas and region restrictions limit what a thief can launch.
- Limitation: billing data lags hours to a day — it's a backstop, not primary detection (that's audit logs, module 18).

**Strong signal:** treating billing as a collection source with known latency.

### Q5. "What's a quota and why would we ever want it lower?"

**Answer outline:**
- A cap on how much of a resource a project/account/subscription can use.
- Low quotas in unused regions and on GPUs are a cheap brake on cryptojacking and runaway automation.
- Request increases before launches; trial accounts often can't.

## 60-second executive explanation

"Cloud is billed like a utility: you pay for what runs, and the meter reading arrives a day later. That's great for flexibility and hard for a fixed appropriation. The tools the providers give us — budgets and alerts — are smoke detectors, not sprinklers: they tell us we're approaching the limit, but they don't stop spending on their own. So we combine several things. We tag every resource to the program that pays for it, so finance sees spending by funding line. We set hard ceilings on how much infrastructure can exist. We alert early, because adding funds takes weeks. And if we do hit the limit, the automated response freezes new spending instead of shutting down the mission. The result is that cloud stays inside the appropriation, and you hear about pressure on it in days, not at the end of the quarter."

## Whiteboard prompt

Draw a federal program's Google Cloud setup: billing account → folders by program → projects by environment. Add labels (`program`, `clin`, `env`). Show the flow: usage → billing export → BigQuery → showback dashboard. Add a budget per program that publishes to Pub/Sub, and a function that applies a "deny new resources" guardrail at 95% forecast. Mark where quotas sit. Circle the one step that could cause data loss if designed as a kill switch.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud billing and cost governance on Google Cloud, AWS, and Azure — budgets, quotas, cost allocation labels, commitment discounts, and FinOps practices — and how they interact with federal appropriations."
- **After completing the lab:** "In personal lab accounts I configured cost allocation labels and tags, budgets with programmatic Pub/Sub notifications on Google Cloud, AWS cost allocation tags and anomaly monitoring, and Azure resource-group budgets and anomaly alerts." Say that the lab spend was effectively zero — that's the honest scale.
- **Still requires (cert / production experience / clearance):** managing a real organization's cloud budget, buying or managing commitments, building a production chargeback model, or working within an actual appropriation and contract vehicle. Don't claim "FinOps experience" or "managed cloud spend." The FinOps Foundation offers practitioner certifications (⚠️ current names and terms not verified this run), and the Google Associate Cloud Engineer exam covers billing setup at a claimable level.
