# 19 Interview Prep — Monitoring and observability

## Likely questions

### Q1. "How would you monitor a new mission application on Google Cloud?"

**Answer outline:**
- Start from users: define SLIs (availability, latency) and SLOs with the mission owner; error budget and burn-rate alerts.
- Golden signals from free platform metrics; Ops Agent or OpenTelemetry for guest and app telemetry; Cloud Trace for latency breakdown.
- Black-box checks: uptime checks for ordinary workloads — but not inside Assured Workloads data-residency/IL4 boundaries, where Google says not to use them; there, rely on request-based SLIs and in-boundary probes.
- Alert routing: two channel types, owned by teams; Pub/Sub for automation.
- Security overlap: log-based alerts on IAM and logging changes routed to the SOC; metric-absence alerts on telemetry.
- Dashboards and policies as code.

**Strong signal:** starting with SLOs and user impact, then naming the security alerts. **Avoid:** "turn on all the default dashboards."

### Q2. "Explain SLOs and error budgets to me."

**Answer outline:**
- SLI = measured good/total; SLO = target over a window; SLA = external promise with penalties.
- Error budget = 1 − SLO; spend it on change, stop shipping features when it's gone.
- Alert on burn rate, not on breach.
- Worked example with numbers (99.5% of 2M requests = 10,000 bad requests per 28 days).

### Q3. "How do CloudWatch and Azure Monitor compare with Google Cloud Monitoring?"

**Answer outline:**
- All three: free platform metrics, agents for guest metrics, alerting, dashboards, managed Prometheus, OpenTelemetry support.
- AWS: alarms + SNS, Synthetics canaries, Application Signals SLOs; X-Ray SDKs in maintenance mode → OTel; free tier of 10 alarms/3 dashboards.
- Azure: alert rules + action groups, Application Insights, standard availability tests; Log Analytics/KQL shared with security.
- Google: SLO-native service monitoring, Managed Service for Prometheus on Monarch; alerting still unbilled until at least Sept 2027.

### Q4. "Where does operational monitoring stop and security monitoring start?"

**Answer outline:**
- Different questions (healthy vs. hostile), different owners, often different tools (monitoring vs SIEM/CSPM).
- Overlaps: audit-log alerts built in monitoring tools; Security Hub CloudWatch.1–14; cryptomining as saturation and spend (T1496.001); DoS as SLO burn (T1499); telemetry-absence alerts (T1685.002).
- Design: shared alert taxonomy, dual routing where signals overlap, and protect the monitoring config itself.

**Strong signal:** a concrete example where one event matters to both teams.

### Q5. "What is OpenTelemetry and why does it matter to a customer?"

**Answer outline:**
- Vendor-neutral CNCF standard (graduated May 2026) for traces, metrics, logs; OTLP protocol.
- Instrument once, send anywhere — Google, AWS, Azure, or self-hosted; reduces lock-in and eases multi-cloud.
- AWS steering X-Ray users to it; Google's Ops Agent and Telemetry API use it.

## 60-second executive explanation

"Monitoring tells us whether our systems are doing their job for the people who depend on them — and warns us before they stop. We agree with the mission owner on a measurable target, like '99.5% of requests succeed within a second,' and we track how much of our allowance for failure we're using. If we're burning through it, the team is paged and new changes pause until it's fixed. The same tools also watch for warning signs of an attack — someone changing who has access, logging being switched off, or computers suddenly running flat out, which often means someone is using our cloud to mine cryptocurrency. One system, two audiences: operations and security."

## Whiteboard prompt

For a public-facing benefits-claims service on Cloud Run with a Cloud SQL database: draw the SLIs (availability, latency) and SLOs, the uptime checks, burn-rate alert pair, the dashboard's four golden signals, and three security alerts built in Cloud Monitoring (IAM change, Secret Manager access by a human, sink deletion). Show which alerts go to SRE, which to the SOC, and which to both. Add the AWS and Azure equivalents in a side column.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud monitoring and observability on Google Cloud, AWS, and Azure — metrics, logs, traces, uptime checks, alerting, dashboards, managed Prometheus, OpenTelemetry, and SLO/error-budget practice — and how operational and security monitoring overlap."
- **After completing the lab:** "In a personal lab I configured Google Cloud Monitoring uptime checks, notification channels, metric and log-based alerting policies, a log-based metric, and a JSON-defined dashboard, and calculated SLIs, SLOs, and error budgets from service metrics." Add the CloudWatch heartbeat alarm and Azure activity log alert only if you did them.
- **Still requires (cert / production experience / clearance):** running on-call or SRE practice for production services, setting SLOs with real stakeholders, or operating monitoring at scale. Your homelab Grafana/InfluxDB/MQTT monitoring and Splunk alerting are genuine and claimable as what they are — personal infrastructure and enterprise log analysis — not as cloud production monitoring. Google Associate Cloud Engineer (monitoring is in scope) is the next claimable step.
