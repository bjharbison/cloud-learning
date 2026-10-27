# 19 — Monitoring and observability: metrics, alerting, dashboards, SLOs (Cloud Monitoring, CloudWatch, Azure Monitor)

> **In one sentence:** you'll be able to explain metrics, logs, and traces; build uptime checks, alerting policies, and dashboards; express reliability as SLIs, SLOs, and error budgets; and show where operational monitoring and security monitoring meet — on all three clouds.

**Prereqs:** modules 00–18 (module 18 for logs and log-based alerting; module 07 for Cloud Run; module 05 for VMs) · **Time:** ~3.5 hours incl. lab · **Phase:** 5

## Learning objectives

- Distinguish **metrics, logs, and traces**, and **monitoring** from **observability**.
- Configure **uptime checks**, **alerting policies**, **notification channels**, and **dashboards**.
- Define **SLI, SLO, SLA**, and **error budget** in plain language and do the arithmetic.
- Compare **Google Cloud Observability**, **Amazon CloudWatch**, and **Azure Monitor**, including managed **Prometheus** and **OpenTelemetry**.
- Separate **operational** from **security** monitoring and design alerts that serve both.

## Why this matters for the target roles

- **Customer engineer / architect:** "How will we know it's working — and when it isn't?" is part of every architecture review. SLOs are the language Google uses for reliability conversations.
- **Cloud security:** many security alerts (IAM change, logging disabled, cryptomining CPU spike) are built with the same alerting tools as ops alerts.
- **CTI:** resource hijacking and denial of service show up first as *operational* anomalies. Knowing where the metrics live is how you find them.

---

## Concepts

### Metrics, logs, traces — the three signals

| Signal | Plain meaning | Example | Best for |
|---|---|---|---|
| **Metric** | A number measured over time | CPU 85%, 120 requests/s, 2% 5xx | Trends, thresholds, cheap long retention |
| **Log** | A timestamped record of one event | "user X called SetIamPolicy" | Detail, investigation, audit (module 18) |
| **Trace** | One request's path across services, with timing per hop (**spans**) | Frontend 20 ms → API 180 ms → DB 900 ms | Finding *where* latency or errors come from |

**Monitoring** watches known signals for known failures ("alert if 5xx > 1%"). **Observability** is the ability to ask *new* questions of your telemetry when something unexpected breaks. In practice: collect all three signals, correlate them, and alert on symptoms.

**OpenTelemetry (OTel)** is the vendor-neutral standard for generating and shipping all three signals (it **graduated** in the CNCF in May 2026). All three clouds accept OTel data — Google via its Telemetry API (OTLP) ⚠️ GA status not confirmed, AWS natively in CloudWatch, Azure via Application Insights. Instrument once with OTel; avoid lock-in to a vendor SDK.

**Homelab bridge:** you've already built this. MQTT → InfluxDB → Grafana is a metrics pipeline; a Grafana alert to your phone is an alerting policy; Splunk is your log store. Cloud monitoring is the same pattern with the collection agents and storage run for you — plus metrics from every managed service, free, from the moment it exists.

### What you get for free vs what you add

- **Platform metrics** are collected automatically from managed services and VMs: Google Cloud system metrics (free), AWS basic monitoring (EC2 at 5-minute resolution), Azure platform metrics (free, kept 93 days).
- **Inside the guest OS** (memory, disk use, processes) needs an **agent**: Google **Ops Agent** (Fluent Bit + OpenTelemetry Collector), **CloudWatch agent**, **Azure Monitor Agent** (the older Log Analytics agent retired in 2024).
- **Custom metrics** from your apps or **log-based metrics** (counting matching log entries) are chargeable beyond free allotments.

### Google Cloud Observability

The umbrella name is **Google Cloud Observability**: **Cloud Monitoring**, **Cloud Logging**, **Cloud Trace**, **Error Reporting**, **Cloud Profiler**, and **Managed Service for Prometheus**.

- **Metrics scope:** one **scoping project** can view metrics from many projects (375 officially supported); alerting policies, dashboards, and uptime checks live there. Most Google Cloud and custom metrics are kept **24 months**; some (including log-based metrics) six weeks.
- **Uptime checks:** HTTP, HTTPS, or TCP probes from at least three checker regions every 1, 5, 10, or 15 minutes; **private uptime checks** reach internal IPs via **Service Directory** (Google's registry of service endpoints). Limit 100 per metrics scope. Google says **not to use uptime checks or synthetic monitors at all** where Assured Workloads data-residency or IL4 controls apply. **1 million executions free per project per month**, then $0.30 per 1,000.
- **Alerting policies:** conditions on **metric threshold**, **metric absence**, **forecast**, **PromQL**, **log match** (log-based alerts), or SQL (Preview). Up to 6 conditions per metric policy. **Notification channels:** email, SMS (Google says not fully reliable — pair it), mobile app, Slack, PagerDuty, webhooks, **Pub/Sub** (for automation), Google Chat (Preview).
- **Log-based metrics:** counter or distribution metrics from a log filter — not backfilled; charged as custom metrics.
- **Dashboards:** predefined per service, custom, or JSON-defined (`gcloud monitoring dashboards create --config-from-file`).
- **Managed Service for Prometheus:** Prometheus-compatible collection (managed collectors on by default for new GKE clusters) stored in **Monarch** (Google's internal planet-scale time-series database), the same backend as Cloud Monitoring; query with **PromQL**; 24-month retention included.

**Pricing to know (October 2026):** Google Cloud system metrics free; chargeable metrics **$0.258/MiB** after **150 MiB free per billing account**; Prometheus **$0.06 per million samples**, no free allotment; Trace **2.5 million spans free**, then $0.20 per million. **Alerting is still free** — Google has announced charges ($0.35/month per metric referenced in a policy plus query charges) starting **no sooner than September 1, 2027**.

### Amazon CloudWatch

- **Metrics** (classic and OpenTelemetry), **alarms** (static threshold, **anomaly detection** bands, Metrics Insights, PromQL, log alarms, **composite** alarms) with actions to SNS, Auto Scaling, EC2 stop/reboot/recover, and Systems Manager.
- **CloudWatch Logs** and **Logs Insights**; **Synthetics** canaries (uptime and scripted checks); **Application Signals** with built-in **SLOs**; RUM.
- **X-Ray** SDKs and daemon entered **maintenance mode** (February 2026); AWS recommends OpenTelemetry. **Amazon Managed Service for Prometheus** and **Amazon Managed Grafana** are the open-source-compatible options.
- **Free tier:** 10 custom/detailed metrics, **10 alarm metrics**, **3 dashboards** (up to 50 metrics each), 5 GB logs, 1 million API requests, 100 canary runs. Beyond that: standard alarm $0.10 per metric/month, custom metric $0.30/month, dashboard $3/month.
- Memory metrics on EC2 need the CloudWatch agent.

### Azure Monitor

- **Platform metrics** (free, 1-minute, 93 days), **Log Analytics** (module 18), **Application Insights** (APM; workspace-based — Microsoft has been migrating classic resources), **managed Prometheus** (18-month retention), and Grafana (free built-in Azure Monitor dashboards with Grafana, or paid **Azure Managed Grafana**).
- **Alert rules:** metric, log search, Prometheus, **activity log** (incl. Service Health), smart detection; **action groups** define who/what is notified.
- **Availability tests:** **standard tests** are current; the older URL ping tests now retire **September 30, 2028** (extended from 2026).
- Metric alerts bill per monitored time series and log search alerts are billed ⚠️ (current dollar amounts not confirmed); **activity log alerts are free**.

### SLIs, SLOs, and error budgets — plainly

From Google's **Site Reliability Engineering** book:

- **SLI (service level indicator):** a measured number about the service, as a ratio of good events to total. *"Proportion of requests that return non-5xx in under 300 ms."*
- **SLO (objective):** the target for that SLI over a window. *"99.5% over 28 days."*
- **SLA (agreement):** a promise to a customer **with consequences** (credits, refunds) — usually looser than the internal SLO. Module 02 covered reading SLAs.
- **Error budget:** `1 − SLO`. At 99.5% over 28 days with 2,000,000 requests, you may "spend" **10,000 bad requests**. Budget left → ship features; budget gone → prioritize reliability.

**The four golden signals** to monitor for any user-facing service: **latency, traffic, errors, saturation**. Alert on **symptoms users feel** (errors, latency), not every cause (one CPU spike).

**Burn-rate alerting:** instead of "alert when SLO is breached" (too late), alert when you're spending budget too fast. Google's guidance: a **fast-burn** alert (around 10× normal over 1–2 hours) and a **slow-burn** alert (around 2× over about 24 hours).

**In Cloud Monitoring:** **service monitoring** supports SLOs automatically for App Engine and **Cloud Service Mesh**/Istio on GKE (a service mesh is a sidecar or proxy layer that handles service-to-service traffic and telemetry), and for **custom services** you define; SLIs are **request-based** or **windows-based**, over rolling or calendar periods ⚠️ (automatic Cloud Run support not confirmed this run). AWS has SLOs in **Application Signals**; Azure has SLO capabilities ⚠️ not verified this run — Azure teams often compute them from Application Insights data.

**Bridge to your intel background:** an SLO is a readiness standard. "Ninety-five percent of tasked collection delivered within 24 hours" is an SLI with an SLO. The error budget is the agreed tolerance for misses — spend it knowingly, and stop new tasking when it's gone.

### Operational vs security monitoring — where they meet

| | Operational monitoring | Security monitoring |
|---|---|---|
| Asks | Is it up, fast, correct, affordable? | Is someone doing something they shouldn't? |
| Main signals | Metrics, traces, app logs | Audit logs, sign-in logs, flow logs, threat findings |
| Owner | SRE / ops | SOC / security engineering |
| Tools | Cloud Monitoring, CloudWatch, Azure Monitor | SIEM, Security Command Center, GuardDuty, Defender (modules 21–22) |

**Where they overlap — and you should build alerts for both teams:**

1. **Security events through ops tooling.** Google documents **log-based alerts** on audit logs, e.g., a *human* accessing a Secret Manager secret or decrypting with Cloud KMS. AWS's **Security Hub CSPM controls CloudWatch.1–14** check for CIS-style metric filters and alarms on CloudTrail events: root usage, unauthorized API calls, console sign-in without MFA, IAM policy changes, CloudTrail config changes, disabling or deleting KMS keys, security group and route changes. Azure documents an alert on privileged **role assignment writes**.
2. **Attacks that look like ops problems.** **Cryptomining** (T1496.001 Compute Hijacking) appears as CPU saturation, new instances in unused regions, and cost spikes (module 04). **Denial of service** (T1499) appears as latency and error SLO burn.
3. **Ops changes that are security events.** An uptime check failing because a service's public access was removed — or *added*. The lab shows this.
4. **Watching the watchers.** Alert when telemetry stops: metric-absence conditions on log volume or heartbeat metrics catch a disabled agent or sink (T1685.002, module 18).

> **Shared responsibility — say it plainly:** providers collect platform metrics and run the monitoring services. **Deciding what to monitor, installing agents in guests, defining SLOs, building alerts and routing them to a human, protecting notification channels, and responding are always the customer's.** An alert nobody receives is not a control.

---

## Text diagram — one service, ops and security views

```
                 ┌──────────── Cloud Run service lab19-web ────────────┐
 Uptime check ──►│ HTTPS / from 3+ regions every 5 min                 │
 (black-box)     │ Platform metrics: request_count by code class,      │── Cloud Monitoring (free)
                 │                    latencies, instance count        │
                 └──────────────┬──────────────────────────────────────┘
                                │ request logs / audit logs (module 18)
                                ▼
   Log-based metric: count of SetIamPolicy  ─┐
   Log-based alert: DeleteSink / human secret access ─┤
   Uptime-failure alert ──────────────────────┤──► Alerting policies ──► Email + Pub/Sub ──► SOC / on-call
   SLO: 99.5% non-5xx over 28 d; burn-rate alerts ┘                                │
                                                                                   ▼
   Dashboard (JSON in git): golden signals + security counters    Incident / ticket / automation
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Umbrella | **Google Cloud Observability** | **Amazon CloudWatch** (+ X-Ray, maintenance mode) | **Azure Monitor** | |
| Free platform metrics | Google Cloud system metrics | Basic monitoring (5-min EC2) | Platform metrics (1-min, 93 d) | |
| Guest agent | Ops Agent | CloudWatch agent | Azure Monitor Agent | Memory needs an agent on all three |
| Uptime / synthetic checks | Uptime checks (1M free/project/month); synthetic monitors | CloudWatch Synthetics canaries (100 free runs) | Standard availability tests (billed) | |
| Alerting | Alerting policies (free until ≥ Sept 2027) | CloudWatch alarms (10 free) | Alert rules + action groups (activity log alerts free; metric and log search alerts billed) | Google charges nothing for alerting until at least Sept 2027 |
| Notifications | Notification channels (email, Slack, PagerDuty, Pub/Sub, webhook…) | SNS topics | Action groups | |
| Log-based alerting | Log-based alerts / metrics | Metric filters + alarms; log alarms | Log search alerts | |
| Dashboards | Custom/JSON dashboards (free) | 3 free, then $3/month | Workbooks; Grafana dashboards (free built-in) | |
| SLOs | Service monitoring SLOs + burn-rate alerts | Application Signals SLOs | ⚠️ not verified this run | Google wrote the SRE book |
| Managed Prometheus | Managed Service for Prometheus (Monarch) | Amazon Managed Service for Prometheus | Azure Monitor managed Prometheus | |
| Tracing | Cloud Trace (OTel) | X-Ray → OpenTelemetry | Application Insights (OTel) | All converging on OpenTelemetry |

## Administer and monitor it

- **Notification hygiene:** at least two channel types per critical policy (Google itself warns SMS and some integrations share failure modes); test channels; route security alerts to the SOC, not just ops.
- **Alert fatigue:** every page should be urgent, actionable, and tied to user impact or a security signal.
- **Dashboards as code** (JSON in git) and **policies as code** (module 20).
- **Monitor the monitoring:** metric-absence alerts on heartbeats and log volume; audit-log alerts on changes to policies and channels (they're Admin Activity events).
- **Cost:** watch chargeable metric volume, Prometheus samples, and log-based metric cardinality.

## Security angle

1. **Notification channels pointing to a departed employee's email** — alerts fire into the void.
2. **Webhook channels to public endpoints** carrying sensitive alert content.
3. **Ops-only routing** of security-relevant alerts (IAM changes, logging disabled).
4. **No absence alerting** — an attacker disables an agent or sink and dashboards quietly flatline.
5. **Over-broad Monitoring Editor** — someone can mute or delete the alerts that would catch them.
6. **Uptime checks** against systems with residency constraints — Google says not to use them with Assured Workloads data-residency or IL4 requirements.

## Threat intel angle

| Technique | ATT&CK | Monitoring signal |
|---|---|---|
| Cryptomining on stolen compute | **T1496.001 Resource Hijacking: Compute Hijacking** (also .004 Cloud Service Hijacking) | CPU/GPU saturation, new instances in unused regions, mining-pool connections, billing anomalies (module 04) |
| Application or service flood | **T1499 Endpoint Denial of Service** (.002 Service Exhaustion, .003 Application Exhaustion) | Latency/error SLO burn, request spikes, WAF metrics (module 12) |
| Disabling telemetry | **T1685.002 Disable or Modify Cloud Log** (ATT&CK v19; module 18) | Metric-absence alerts; Admin Activity on alert-policy or sink deletion |
| Valid accounts used oddly | **T1078.004** | Log-based metrics on sign-ins or IAM changes outside hours |

Google's **Threat Horizons** reports have repeatedly found that compromised cloud instances are most often used for **cryptocurrency mining** ⚠️ (exact current statistics not re-verified this run — check the latest report). That's why "unexpected CPU and spend" is a security signal, not just an ops one.

**Bridge to your OT work:** in ICS you learned that process anomalies (a pump cycling oddly) can be the first sign of compromise, and that safety and security monitoring have to talk. Cloud is the same: the SRE dashboard and the SOC console should share alerts where the signals overlap.

## Public sector notes

- Google says **not to use uptime checks or synthetic monitors** where Assured Workloads data-residency or **IL4** requirements apply — measure availability from request-based SLIs on platform metrics and probes run inside the boundary.
- Federal SLAs and **mission SLOs** often come from operational requirements (availability for a 24×7 watch floor); translate them into SLIs you can measure.
- Monitoring and alerting configurations are evidence for **continuous monitoring** in an ATO (module 26).

## Key takeaways

- Three signals: **metrics** (numbers over time), **logs** (events), **traces** (request paths). Standardize on **OpenTelemetry**.
- Platform metrics are free; guest metrics need an agent; custom and log-based metrics cost beyond free tiers.
- Google: uptime checks, alerting policies (free until at least Sept 2027), notification channels, JSON dashboards, Managed Service for Prometheus on Monarch. AWS: CloudWatch alarms/SNS, Synthetics, Application Signals. Azure: alert rules/action groups, availability tests, managed Prometheus.
- **SLI → SLO → error budget**; alert on **burn rate** and the four golden signals.
- Ops and security monitoring meet at audit-log alerts, resource hijacking, DoS, and absence-of-telemetry alerts.
- What to monitor, who gets alerted, and responding are **always the customer's**.

## Sources

- [Google Cloud — Observability documentation](https://docs.cloud.google.com/stackdriver/docs), [Observability pricing](https://cloud.google.com/products/observability/pricing), [Ops Agent](https://docs.cloud.google.com/stackdriver/docs/solutions/agents/ops-agent), [Monitoring quotas and retention](https://docs.cloud.google.com/monitoring/quotas), [Metrics scopes](https://docs.cloud.google.com/monitoring/settings)
- [Google Cloud — Alerting overview](https://docs.cloud.google.com/monitoring/alerts), [notification options](https://docs.cloud.google.com/monitoring/support/notification-options), [channels via API](https://docs.cloud.google.com/monitoring/alerts/using-channels-api), [log-based alerts](https://docs.cloud.google.com/logging/docs/alerting/log-based-alerts), [log-based metrics](https://docs.cloud.google.com/logging/docs/logs-based-metrics)
- [Google Cloud — Uptime checks](https://docs.cloud.google.com/monitoring/uptime-checks/introduction), [private uptime checks](https://docs.cloud.google.com/monitoring/uptime-checks/private-checks), [SLO monitoring](https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring), [burn-rate alerts](https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring/alerting-on-budget-burn-rate), [Managed Service for Prometheus](https://docs.cloud.google.com/stackdriver/docs/managed-prometheus), [managed collection](https://docs.cloud.google.com/stackdriver/docs/managed-prometheus/setup-managed), [Telemetry (OTLP) API](https://docs.cloud.google.com/stackdriver/docs/reference/telemetry/overview), [dashboards API](https://cloud.google.com/monitoring/api/ref_v3/rest/v1/projects.dashboards)
- [Google SRE book — Service level objectives](https://sre.google/sre-book/service-level-objectives/), [Embracing risk](https://sre.google/sre-book/embracing-risk/), [Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [AWS — What is CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html), [alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Alarms.html), [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/), [X-Ray SDK/daemon timeline](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html), [Managed Service for Prometheus](https://docs.aws.amazon.com/prometheus/latest/userguide/what-is-Amazon-Managed-Service-Prometheus.html), [Managed Grafana](https://docs.aws.amazon.com/grafana/latest/userguide/what-is-Amazon-Managed-Service-Grafana.html), [EC2 detailed monitoring](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-detailed-monitoring.html), [Security Hub CloudWatch controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cloudwatch-controls.html), [put-metric-alarm](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/put-metric-alarm.html), [SNS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-services-sns.html)
- [Microsoft — Azure Monitor platform metrics](https://learn.microsoft.com/en-us/azure/azure-monitor/metrics/data-platform-metrics), [alert types](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-types), [availability tests](https://learn.microsoft.com/en-us/azure/azure-monitor/app/availability), [classic Application Insights migration](https://learn.microsoft.com/en-us/azure/azure-monitor/app/convert-classic-resource), [Grafana options](https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/visualize-grafana-overview), [Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/), [alert on privileged role assignments](https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments-alert), [az monitor action-group](https://learn.microsoft.com/en-us/cli/azure/monitor/action-group?view=azure-cli-latest), [az monitor activity-log alert](https://learn.microsoft.com/en-us/cli/azure/monitor/activity-log/alert?view=azure-cli-latest)
- [OpenTelemetry — signals](https://opentelemetry.io/docs/concepts/signals/), [graduation announcement (2026)](https://opentelemetry.io/blog/2026/otel-grad-now-what/)
- [MITRE ATT&CK — T1496.001](https://attack.mitre.org/techniques/T1496/001/), [T1499](https://attack.mitre.org/techniques/T1499/), [T1685.002](https://attack.mitre.org/techniques/T1685/002/)

Verified: 2026-10-27
