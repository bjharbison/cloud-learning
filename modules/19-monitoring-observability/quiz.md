# 19 Quiz — Monitoring and observability

1. Define metrics, logs, and traces in one line each, with an example.
<details><summary>Answer</summary>

Metric: a number over time (CPU 85%, requests/s). Log: a timestamped record of one event (an audit entry for `SetIamPolicy`). Trace: one request's path across services with timing per hop (spans), e.g., frontend → API → database latency breakdown.
</details>

2. What's the difference between monitoring and observability?
<details><summary>Answer</summary>

Monitoring watches known signals for known failure conditions. Observability is the ability to ask new questions of rich telemetry (metrics, logs, traces) to understand unexpected failures.
</details>

3. Define SLI, SLO, SLA, and error budget. Compute the error budget for a 99.9% SLO over 30 days with 5,000,000 requests.
<details><summary>Answer</summary>

SLI: measured ratio of good events to total. SLO: target for the SLI over a window. SLA: a customer promise with consequences, usually looser than the SLO. Error budget: 1 − SLO. Here 0.001 × 5,000,000 = 5,000 bad requests.
</details>

4. What are the four golden signals, and which should usually page a human?
<details><summary>Answer</summary>

Latency, traffic, errors, saturation. Page on user-visible symptoms — error rate and latency (ideally as SLO burn rate) — rather than every cause like a single CPU spike.
</details>

5. Why use burn-rate alerts instead of alerting when the SLO is breached?
<details><summary>Answer</summary>

A breach alert fires after the budget is gone. Burn-rate alerts fire when budget is being consumed too fast — e.g., a fast-burn (~10× over 1–2 hours) and slow-burn (~2× over ~24 hours) pair, per Google's guidance.
</details>

6. Which metrics need an agent inside a VM on all three clouds, and what's each agent called?
<details><summary>Answer</summary>

Guest-OS metrics such as memory and disk usage. Google Ops Agent, Amazon CloudWatch agent, Azure Monitor Agent.
</details>

7. As of October 2026, which cloud doesn't yet charge for alerting policies, and when might that change?
<details><summary>Answer</summary>

Google Cloud. Announced charges ($0.35/month per metric referenced plus query charges) begin no sooner than September 1, 2027. AWS bills alarms beyond 10 free alarm metrics; Azure bills metric and log search alert rules (activity log alerts are free).
</details>

8. Spot the problem: a production alerting policy's only notification channel is an SMS number belonging to an engineer who left last month.
<details><summary>Answer</summary>

Alerts go nowhere. Use at least two channel types (e.g., email/Pub/Sub plus paging), team-owned destinations, periodic channel tests, and alerting on changes to policies and channels.
</details>

9. Give three ways operational and security monitoring overlap.
<details><summary>Answer</summary>

Any three: log-based alerts on audit events (IAM changes, human secret access) built in ops tools; AWS Security Hub CloudWatch.1–14 metric-filter alarms on CloudTrail events; resource hijacking (T1496.001) showing as CPU/instance/cost spikes; DoS (T1499) showing as SLO burn; metric-absence alerts catching disabled telemetry (T1685.002); access changes causing outages.
</details>

10. Scenario: an agency workload sits inside an Assured Workloads boundary with IL4 requirements. Can you use an uptime check? What would you do instead?
<details><summary>Answer</summary>

No — Google says not to use uptime checks or synthetic monitors (public or private) where Assured Workloads data-residency or IL4 requirements apply. Measure availability with request-based SLIs from platform metrics and with probes or synthetic traffic run inside the boundary.
</details>

11. Compare the "notify someone" building block on each cloud.
<details><summary>Answer</summary>

Google: notification channels (email, SMS, Slack, PagerDuty, webhook, Pub/Sub…) attached to alerting policies. AWS: SNS topics as alarm actions. Azure: action groups attached to alert rules.
</details>

12. In the lab, removing `allUsers` from the service caused 403s that a "non-5xx" SLI ignored. What does that teach about SLI design?
<details><summary>Answer</summary>

SLI definitions encode what "good" means; excluding 4xx hides failures caused by misconfiguration or access changes. Combine request-based SLIs with black-box checks (uptime/synthetics), and define SLIs from the user's perspective.
</details>
