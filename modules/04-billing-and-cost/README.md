# 04 — Billing, quotas, and cost governance (FinOps basics)

> **In one sentence:** you'll be able to explain where a cloud bill comes from, why a budget can't stop it, how labels turn one bill into many, and why elastic spend is a hard fit for fixed government appropriations.

**Prereqs:** modules 00–03 · **Time:** ~3 hours incl. lab · **Phase:** 1

## Learning objectives

- Trace a charge from a running resource to an invoice on each cloud.
- Explain why budgets are **alarms, not circuit breakers**, and describe the three ways to build something closer to a cap.
- Use labels/tags for **showback** and **chargeback**, and name the gotchas on each cloud.
- Distinguish **quotas** from budgets, and explain why a quota is also a security control.
- Compare commitment discounts (CUDs, Savings Plans, reservations) at a concept level.
- Describe the FinOps loop (Inform → Optimize → Operate) and how it collides with the Antideficiency Act.

## Why this matters for the target roles

- **Customer engineer / architect:** every public-sector deal hits "how do we keep this inside the appropriation?" A CE who can answer with budgets, quotas, commitments, and labels — honestly, including what they *can't* do — is trusted.
- **Cloud security:** a bill spike is often the first visible sign of a compromise. Billing data is telemetry.
- **CTI:** cryptojacking and AI-model abuse turn stolen credentials into someone else's invoice. You'll see this in reporting constantly.

---

## Concepts

### How a cloud bill is built

**Plain version:** every resource has a meter. The provider multiplies usage by a price, adds it up per billing period, subtracts credits and discounts, and invoices whoever owns the billing relationship.

**Practitioner vocabulary:**

- **SKU** — the individual priced item (e.g., "E2 instance core running in Americas"). One VM generates several SKUs: vCPU, memory, disk, network.
- **Metering** — measuring usage per SKU, usually per second or per hour for compute, per GB-month for storage, per GB for network egress.
- **Billing period** — usually a calendar month.
- **Credits and discounts** — free-trial credit, free-tier allowances, commitment discounts, negotiated rates.

Who pays, on each cloud (module 00 introduced this; here's the money view):

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Billing relationship | **Cloud Billing account**, linked to one or more projects | The **account**; in AWS Organizations, the **management account** pays for all members | **Billing account**; under a Microsoft Customer Agreement, broken into billing profiles and invoice sections; subscriptions roll up to it |
| Isolation unit that accrues cost | Project | Account | Subscription |
| Unlink = stop | Unlinking billing from a project stops its paid services | Closing the account | Disabling/cancelling the subscription |

**Bridge:** think of the power meter on your homelab rack feeding InfluxDB. Every device draws watts; the utility multiplies kWh by a rate. Cloud is the same, with thousands of meters and a different rate on each.

### What actually drives cost

Four things cause most surprise bills:

1. **Running compute** — VMs, nodes, and instances bill while they run, busy or not.
2. **Things that bill while idle** — static IPs, load balancers, NAT gateways, managed Kubernetes control planes, disks and snapshots, database instances (from [`reference/lab-safety.md`](../../reference/lab-safety.md)).
3. **Network egress** — data leaving a region or going to the internet. Ingress is usually free; egress usually isn't.
4. **Per-request services at scale** — cheap per call, expensive per billion calls.

**Billing data lags.** Azure says cost data is typically available within 8–24 hours, and budgets are evaluated every 24 hours. Google says budget notifications can lag actual usage. Plan for a day of blindness.

### Budgets vs hard caps

You set up budgets in module 00. Now the important part: **a budget notifies; it does not stop anything.**

- **Google Cloud:** an alerts-only budget doesn't cap usage. Budgets can also send **programmatic notifications** to a **Pub/Sub** topic "multiple times per day," with JSON fields like `costAmount`, `budgetAmount`, and `alertThresholdExceeded`. Code can act on them.
- **AWS:** **AWS Budgets actions** can run automatically or after your approval when a threshold is crossed. Options: apply an **IAM policy** or an **SCP** (e.g., deny new EC2 launches), or target specific **EC2 or RDS instances** (stop them).
- **Azure:** budgets don't affect resources. A budget at subscription or resource-group scope can call an **action group**, which can trigger automation (a function, webhook, or runbook) that you write.

So there are three ways to get closer to a cap:

| Approach | Example | Risk |
|---|---|---|
| **Kill switch** | Google's documented pattern: budget → Pub/Sub → Cloud Run function that **disables billing** on the project | Google warns resources "might be irretrievably deleted." Stops *everything*, including free-tier services. |
| **Freeze new spend** | AWS Budgets action applying a deny SCP or IAM policy | Running resources keep billing; only new creation is blocked |
| **Targeted stop** | AWS action stopping tagged EC2/RDS; Azure action group → runbook that deallocates VMs | Only covers what you thought to target |

**Exception:** Azure's free account has a **spending limit** that disables services when credit runs out (module 00). It only exists on credit-based offers and is removed when you upgrade.

**Bridge to your OT background:** a budget is an alarm on the HMI. A kill switch is a trip. Nobody wires a trip without asking what it shuts down, and in what order. Same here: a billing kill switch on a production mission system is a self-inflicted outage.

### Labels and tags: one bill, many owners

A **label** (Google) or **tag** (AWS, Azure) is a key-value pair on a resource, like `cost-center=intel-ops` or `env=prod`. The billing system carries them through, so you can split one bill by owner.

- **Showback** — reporting each team's share of cost back to them. Informational.
- **Chargeback** — actually billing each team's budget for its share.

Gotchas on each cloud:

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Name | **Labels** (cost); **tags** are a separate feature for policy | **Cost allocation tags** | **Tags** |
| Limits | Up to 64 labels per resource; keys and values up to 63 characters; lowercase letters, numbers, `_`, `-` | ⚠️ limits not verified this run — check the Billing docs | ⚠️ limits not verified this run |
| Must you turn them on for billing? | No — labels flow to billing reports and the BigQuery billing export automatically | **Yes.** User-defined tags must be **activated** in Billing. Keys can take up to 24 hours to appear, then up to another 24 to activate | No, but **tag inheritance** (Cost Management setting) can copy subscription/RG tags onto usage records without changing the resources |
| Policy use | Labels **can't** drive policy conditions; Google **tags** can | Tags can appear in IAM conditions (module 14) | Azure Policy can require or append tags (module 20) |

Google detail worth knowing: when you filter a billing breakdown by label key, labels applied to the **project** itself can't be selected. Label the resources.

**Bridge to your intel background:** labels are your **caveats and dissemination markings**. A document without markings can't be routed correctly; a resource without labels can't be billed to the right program. And like markings, they only work if everyone applies them consistently — enforce them with policy (module 20).

### Quotas: the other kind of limit

A **quota** caps how much of a resource you *can* use, regardless of cost.

- **Google Cloud:** quotas are adjustable; **system limits** are fixed. Types: **allocation** (how many VMs you can hold), **rate** (requests per minute), **concurrent** (simultaneous operations). Free Trial accounts can't request increases and may have lower values; values rise for most services once billing is upgraded. Google says quotas exist to protect the community of users and keep services available.
- **AWS:** **Service Quotas** console and API; defaults per account per Region; request increases there.
- **Azure:** per-subscription, per-region quotas, notably **vCPUs per VM family**. View and request in the portal's **Quotas** page or with `az vm list-usage`.

**Why a quota is a security control:** an attacker with stolen keys can only launch as many GPUs as your quota allows. Low quotas in regions you don't use are a cheap brake on cryptojacking. That's a side effect — quotas aren't designed as cost controls — but it's a real one.

### Paying less: commitments and spare capacity

Three pricing models exist on every cloud:

1. **On-demand** — pay the list rate, no commitment.
2. **Commitment** — promise to use or spend a certain amount for 1 or 3 years; get a discount.
3. **Spare capacity** — deep discount on capacity the provider can reclaim with short notice (**Spot**).

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Automatic discount | **Sustained use discounts** — automatic on eligible machine series once a resource runs more than 25% of a month; up to 30% net for a full month | — | — |
| Resource commitment | **Resource-based CUDs** — commit to vCPUs, memory, GPUs, etc. in a region (Compute Engine only) | **Reserved Instances**; **EC2 Instance Savings Plans** (one family in one Region, up to 72%) | **Reservations** — a specific VM size/family in a region |
| Spend commitment | **Spend-based CUDs** — commit to hourly or monthly spend at the billing-account level, 1 or 3 years; flexible versions cover Compute Engine, GKE, and Cloud Run | **Compute Savings Plans** — any family, Region, Fargate, Lambda (up to 66%) | **Savings plan for compute** — fixed hourly spend across eligible compute, 1 or 3 years |
| Spare capacity | Spot VMs | Spot Instances | Spot VMs |

Microsoft's own guidance captures the trade-off: reservations save the most for stable, unchanging workloads; savings plans suit workloads that move between sizes or regions. AWS notes Savings Plan terms can't be changed after purchase.

**The catch:** a commitment is a contract. If the mission ends early, you still pay. That matters a lot in government (see below).

### FinOps in one loop

**FinOps** is the practice of making engineering, finance, and leadership share responsibility for cloud spend. The FinOps Foundation describes three repeating phases:

- **Inform** — get cost, usage, and efficiency data in front of the people who cause it.
- **Optimize** — find improvements: rightsize, schedule, delete idle, buy commitments.
- **Operate** — make it routine, with shared accountability, then loop back.

**Bridge:** it's the intelligence cycle applied to money. Collection (billing export) → processing (labels) → analysis (anomalies, unit cost) → dissemination (showback) → feedback (owners act).

### Anomaly detection

All three clouds now flag unusual spend automatically, but none in real time:

- **Google Cloud:** **cost anomalies** across projects on a billing account, by email or Pub/Sub. Standard anomalies come through next-day channels.
- **AWS:** **Cost Anomaly Detection** needs at least one **cost monitor**; alerts may start within 24 hours; individual alerts go through SNS, or daily/weekly email summaries.
- **Azure:** anomaly insights in Cost analysis smart views and **anomaly alerts** at subscription scope. Evaluation runs 36 hours after the end of each UTC day. Microsoft says this isn't available for Azure Government.

---

## Text diagram

```
 RESOURCES (labeled)          METERING              BILLING ACCOUNT            PEOPLE
 VM  lab=04 cc=ops ──┐                                                     ┌─► Email (threshold)
 Disk lab=04 ───────┼──► usage × SKU price ──► costs − credits − CUDs ──┼─► Pub/Sub / SNS / action group
 Bucket cc=intel ───┘    (lags hours)            │      │                 │      └─► code: freeze / stop / kill
                                                 │      └─► export (BigQuery / Cost Explorer / exports)
 QUOTAS cap how much can exist ─┐                │              └─► showback / chargeback by label
 (blast-radius brake)           │                ▼
                                └──────► BUDGET (alarm, not breaker) ──► ANOMALY DETECTION (next day)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Who pays | Cloud Billing account (linked to projects) | Account / Organizations management account | Billing account → profiles/sections → subscriptions | Google separates billing from resources most cleanly |
| Budget alerts | Budgets & alerts (actual and forecast thresholds) | AWS Budgets | Cost Management budgets (actual or forecast) | All alert-only by default |
| Built-in automated response | Pub/Sub notifications → your code | **Budgets actions**: IAM/SCP deny, stop EC2/RDS | Action group → your automation | Only AWS has native "do something" actions |
| Hard cap | None (kill-switch pattern you build) | None | Spending limit on credit offers only | No cloud offers a native hard cap on paid accounts |
| Cost labels | Labels (automatic in billing) | Cost allocation tags (**must activate**) | Tags (+ optional tag inheritance) | AWS's activation step catches people out |
| Quotas | Cloud Quotas (allocation/rate/concurrent) | Service Quotas | Subscription/region quotas (vCPU per family) | Free trials limit increases |
| Commitments | Resource- and spend-based CUDs; automatic SUDs | Savings Plans; Reserved Instances | Reservations; savings plan for compute | Only Google has an automatic usage discount |
| Anomaly detection | Cost anomalies (next day) | Cost Anomaly Detection (needs a monitor) | Anomaly alerts (subscription scope; not in Azure Government) | None are real-time |

## Administer and monitor it

Weekly-ish routine for a small environment:

- **Look at the bill by SKU and by label.** Google: Billing → Reports (group by SKU, filter by label). AWS: Cost Explorer. Azure: Cost Management → Cost analysis.
- **Export for real analysis.** Google exports billing data (labels included) to **BigQuery**; AWS and Azure have their own export features (⚠️ AWS/Azure export products not re-verified this run — check current names).
- **Review untagged spend.** Anything without a `cost-center` label is a finding.
- **Check quotas before a launch**, not during it.
- **Know who holds billing roles.** On Google, **Billing Account Administrator** can unlink billing from projects — that's an outage button.

## Security angle

- **Billing admin is a privileged role.** Whoever can unlink a billing account or apply a budget-action SCP can stop a mission. Treat billing roles like org admin: few holders, phishing-resistant MFA, alerting.
- **Budget recipients matter.** Alerts going to a departed employee's inbox are no alerts at all. Use a group or a monitored channel.
- **Kill switches are availability risks.** Google's own warning on its disable-billing pattern is that resources might be permanently deleted. Use freeze-style controls for production; reserve kill switches for sandboxes.
- **Low quotas in unused regions** blunt cryptojacking.
- **Shared responsibility:** the provider meters accurately and gives you budget, quota, and alerting tools. **Setting budgets, wiring responses, labeling resources, granting billing roles, and cleaning up are all the customer's job.** A leaked key that mines crypto for a week is the customer's bill.

## Threat intel angle

- **T1496.001 Resource Hijacking: Compute Hijacking** — the classic: stolen credentials, GPU instances, crypto-miners. Your first signal is often a budget email.
- **T1496.004 Resource Hijacking: Cloud Service Hijacking** — abusing a victim's paid cloud services, including AI model APIs (often called "LLMjacking" in vendor reporting). Spend shows up on AI/ML SKUs you never use.
- **T1578.002 Create Cloud Instance** and **T1535 Unused/Unsupported Cloud Regions** — new instances in regions you never use. Quotas and region restrictions (module 02) limit the damage.
- **Detection idea:** treat a spend anomaly on an unfamiliar SKU or region as a security event, not just a finance one — route it to the SOC as well as the budget owner.

**Bridge to your CTI work:** billing data is an unusual collection source — low fidelity, high latency, but nearly impossible for an intruder to suppress. It's the cloud equivalent of noticing a facility's power draw spike at 0300.

## Public sector notes

This is where cloud billing gets genuinely hard.

- **The law:** the **Antideficiency Act** bars federal employees from obligating or spending more than an appropriation provides, or obligating before funds are appropriated (31 U.S.C. § 1341). Violations must be reported to the President and Congress, and carry administrative and potentially criminal penalties (GAO).
- **The collision:** cloud is elastic and billed after the fact; appropriations are fixed and must be obligated first. An autoscaling workload or a compromised account can consume past the funded amount — and a budget alert doesn't stop it.
- **What practitioners do** (from the FinOps Foundation's U.S. Public Sector playbook):
  - Fund cloud on contracts structured by **CLIN** (contract line item) and line of accounting, so each program tracks its own consumption.
  - Use showback/chargeback internally even when the contract rolls up to one line — and note that inconsistent tagging makes those reports worse over time.
  - Set alerts **early**, because adding funds takes longer than engineers expect.
  - Be careful with commitments: the playbook notes most government contracts don't permit 3-year commitments, and some restrict 1-year commitments to certain periods.
- **Architecture consequence:** for regulated, fixed-budget customers, prefer controls that **freeze** (deny SCPs, quotas, policy) over ones that **kill**, and design so that hitting a ceiling degrades gracefully instead of deleting mission data.

**Interview-ready point:** "Cloud doesn't remove the appropriation; it changes when you find out you've exceeded it. My job is to move that moment earlier with labels, budgets, anomaly alerts, and quotas, and to make sure the response to a ceiling is a freeze, not data loss."

## Key takeaways

- A bill is usage × SKU price, minus credits and discounts, and the data lags by hours.
- **Budgets alert; they don't stop spend.** Caps are things you build: kill switch (risky), freeze (AWS Budgets actions), or targeted stop.
- Labels/tags make showback and chargeback possible. AWS tags must be **activated** before they appear in billing.
- Quotas limit what can exist — a useful brake on cryptojacking.
- Commitments trade flexibility for discount; Spot trades reliability for discount.
- FinOps = Inform → Optimize → Operate, with shared accountability.
- In government, elastic spend meets the Antideficiency Act. Alert early, freeze rather than kill, and fund by CLIN.
- Budgets, labels, billing roles, and cleanup are **always the customer's** responsibility.

## Sources

- [Google Cloud — Disable billing usage with notifications](https://docs.cloud.google.com/billing/docs/how-to/disable-billing-with-notifications)
- [Google Cloud — Set up programmatic budget notifications](https://docs.cloud.google.com/billing/docs/how-to/budgets-programmatic-notifications)
- [Google Cloud — View and manage cost anomalies](https://docs.cloud.google.com/billing/docs/how-to/manage-anomalies)
- [Google Cloud — Labels overview](https://docs.cloud.google.com/resource-manager/docs/labels-overview)
- [Google Cloud — Quotas overview](https://docs.cloud.google.com/docs/quotas/overview)
- [Google Cloud — Committed use discounts](https://docs.cloud.google.com/docs/cuds)
- [Google Cloud — Sustained use discounts](https://docs.cloud.google.com/compute/docs/sustained-use-discounts)
- [AWS — Configuring budget actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)
- [AWS — Activating user-defined cost allocation tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html)
- [AWS — Getting started with Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html)
- [AWS — Savings Plans types](https://docs.aws.amazon.com/savingsplans/latest/userguide/plan-types.html)
- [Microsoft — Create and manage budgets](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
- [Microsoft — Manage costs with budgets (automation scenario)](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/cost-management-budget-scenario)
- [Microsoft — Identify anomalies and unexpected changes in cost](https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/analyze-unexpected-charges)
- [Microsoft — Group and allocate costs using tag inheritance](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/enable-tag-inheritance)
- [Microsoft — Decide between a savings plan and a reservation](https://learn.microsoft.com/en-us/azure/cost-management-billing/savings-plan/decide-between-savings-plan-reservation)
- [FinOps Foundation — FinOps phases](https://www.finops.org/framework/phases/)
- [FinOps Foundation — U.S. Public Sector FinOps Playbook v1.0 (PDF)](https://www.finops.org/wp-content/uploads/2022/10/FinOps-Foundation_US-Gov-Playbook.pdf)
- [GAO — Antideficiency Act resources](https://www.gao.gov/legal/appropriations-law/resources)
- [MITRE ATT&CK — T1496.004 Cloud Service Hijacking](https://attack.mitre.org/techniques/T1496/004/), [T1496.001](https://attack.mitre.org/techniques/T1496/001/), [T1578.002](https://attack.mitre.org/techniques/T1578/002/), [T1535](https://attack.mitre.org/techniques/T1535/)

Verified: 2026-10-24
