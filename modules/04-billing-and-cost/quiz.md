# 04 Quiz — Billing, quotas, and cost governance

1. True or false: a Google Cloud budget set to $10 will stop resources when spend reaches $10.
<details><summary>Answer</summary>

False. Budgets alert; they don't cap usage. Stopping spend requires code you build (e.g., Pub/Sub notification → function), and even then billing data lags actual usage.
</details>

2. Name the native mechanism on each cloud for *doing something* when a budget threshold is crossed.
<details><summary>Answer</summary>

Google Cloud: programmatic notifications to a Pub/Sub topic (you write the response). AWS: Budgets actions (apply an IAM policy or SCP, or stop specific EC2/RDS instances). Azure: an action group on the budget, which can trigger automation such as a function or webhook. Only AWS has built-in response actions.
</details>

3. What does Google warn can happen if you use its "disable billing" pattern to cap costs?
<details><summary>Answer</summary>

Disabling billing stops all services in the project, including free-tier ones, and resources might be irretrievably deleted. It's a kill switch, not a pause button.
</details>

4. Define showback and chargeback.
<details><summary>Answer</summary>

Showback reports each team's share of cost to them (informational). Chargeback actually bills each team's budget for its share. Both depend on consistent labels/tags.
</details>

5. A team tagged every AWS resource with `cost-center` last month, but Cost Explorer can't group by it. What's the most likely cause?
<details><summary>Answer</summary>

The tag key was never **activated** as a cost allocation tag in Billing. User-defined tags must be activated (they can take up to 24 hours to appear and up to another 24 to activate).
</details>

6. What's the difference between a quota and a budget? Why does a security team care about quotas?
<details><summary>Answer</summary>

A quota caps how much of a resource can exist or be used (e.g., vCPUs per region); a budget only measures spend and alerts. Quotas limit an attacker's blast radius — stolen credentials can launch only as many GPUs as the quota allows.
</details>

7. Compare: Google spend-based CUD, AWS Compute Savings Plan, Azure savings plan for compute.
<details><summary>Answer</summary>

All three are 1- or 3-year commitments to a level of spend (hourly, or monthly for Google's Flexible Savings Plans) in exchange for discounts across a range of compute services, rather than one specific instance type. Google's flexible commitments cover Compute Engine, GKE, and Cloud Run; AWS's covers EC2 across families/Regions plus Fargate and Lambda (up to 66%); Azure's applies across eligible compute in all regions. Google additionally applies sustained use discounts automatically on eligible machine series.
</details>

8. Name the three FinOps phases.
<details><summary>Answer</summary>

Inform, Optimize, Operate — repeated as a loop.
</details>

9. Scenario: an agency program has a fixed $2M appropriation. Engineering wants autoscaling with no maximum. What do you recommend, and what law is the comptroller worried about?
<details><summary>Answer</summary>

The Antideficiency Act (31 U.S.C. § 1341) bars obligating or spending beyond the appropriation. Recommend: autoscaling with an explicit maximum, quotas sized to the funded ceiling, labels by program/CLIN for showback, budgets with early forecast-based alerts routed to both engineering and finance, anomaly detection, and a *freeze*-style response (deny new resources) rather than a kill switch that could delete mission data. Commitments only if the contract permits the term.
</details>

10. Spot the misconfiguration: "Our Google Cloud trial budget is $10, includes credits, and alerts the engineer who set it up."
<details><summary>Answer</summary>

Two problems. Including credits means net cost stays $0 during the trial, so alerts never fire. And alerts go to one person — if they leave or miss the email, nobody knows. Exclude credits and send to a monitored group or channel.
</details>

11. Your Azure anomaly alert didn't fire for a spike that started this morning. Is something broken?
<details><summary>Answer</summary>

Probably not. Azure evaluates anomalies daily, 36 hours after the end of each UTC day. Google's standard anomalies arrive next-day and AWS says alerts may start within 24 hours of monitor creation. None of them are real-time.
</details>

12. Which ATT&CK sub-technique covers attackers running up a victim's AI model API bill, and what billing signal would you look for?
<details><summary>Answer</summary>

T1496.004 Resource Hijacking: Cloud Service Hijacking (often called "LLMjacking" in vendor reporting). Look for spend on AI/ML SKUs or regions the organization doesn't normally use.
</details>
