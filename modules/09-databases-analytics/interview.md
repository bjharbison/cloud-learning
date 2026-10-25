# 09 Interview Prep — Databases and analytics

## Likely questions

### Q1. "A customer asks which Google Cloud database they should use. How do you run that conversation?"

**Answer outline:**
- Discovery first: data shape (tables vs documents vs time-series), transaction needs, scale and geography, latency, existing engines and skills, licensing (SQL Server, Oracle).
- Map to families: Cloud SQL (lift-and-shift relational), AlloyDB (demanding PostgreSQL), Spanner (global, strongly consistent, horizontal scale), Firestore (documents), Bigtable (high-throughput wide-column), Memorystore (cache).
- Analytics is a separate question → BigQuery.
- Close with operations and security: private connectivity, IAM-based auth, backups/PITR.

**Strong signal:** asking two good discovery questions before naming a product.
**Avoid:** jumping to Spanner because it's impressive.

### Q2. "What makes BigQuery different from Redshift or Synapse?"

**Answer outline:**
- Serverless: no cluster to size; storage and compute separated.
- Two pricing models: on-demand by bytes scanned (first 1 TiB/month free) or capacity via editions (slots).
- Redshift has provisioned clusters and Redshift Serverless; Athena for SQL on S3. Azure has Synapse dedicated SQL pools and Fabric Data Warehouse, with Microsoft publishing Synapse-to-Fabric migration guidance.
- Honest caveat: on-demand needs cost guardrails — partitioning, maximum bytes billed, quotas.

### Q3. "How would a security team use BigQuery?"

**Answer outline:**
- Org-level aggregated log sink → central dataset (partitioned, with expiration) or Observability Analytics with a linked dataset.
- SQL hunting at long retention; joins with asset inventory and threat-intel tables; scheduled queries for alerting; Community Security Analytics as a starter set.
- Access: dataset IAM, authorized views, row/column policies; BigQuery data-access logs are always on, so analysts' own queries are audited.
- When they need detections, case management, and curated intel: Google SecOps.
- Peers: Amazon Security Lake (OCSF on S3), Microsoft Sentinel data lake.

**Strong signal:** mentioning cost control and partitioning unprompted — that's the thing that bites real deployments.

### Q4. "What are the biggest security risks with managed databases and warehouses?"

**Answer outline:**
- Public endpoints with wide allowlists; password-only logins without MFA.
- Over-broad dataset access; sensitive data copied into unprotected projects.
- No PITR/deletion protection → destructive attacks are permanent.
- Case study: UNC5537 vs Snowflake customers — infostealer credentials, no MFA, no allowlists, ~165 orgs notified, no platform breach.

### Q5. "An agency is worried BigQuery costs are unpredictable. What do you say?"

**Answer outline:**
- Explain both models; recommend editions/commitments for steady analytic workloads, on-demand for exploratory.
- Guardrails: custom quotas, maximum bytes billed, partition-required tables, budgets and alerts (module 04).
- Visibility: `INFORMATION_SCHEMA.JOBS` and billing export by project and label.

## 60-second executive explanation

"Think of our databases in two groups. The first runs the applications — case management, forms, sensor feeds — and the cloud provider operates those engines for us, so our team stops patching servers and focuses on the data. The second is the analytics warehouse, where we bring years of records together to ask big questions. With BigQuery there's no hardware to size; we pay for the questions we ask, and we put limits on that so spending stays inside the budget. For security, we use the same warehouse to keep years of audit logs searchable in seconds — and every search an analyst runs is itself recorded. The part that stays ours, always, is who can log in and from where. The biggest data thefts from cloud warehouses in recent years didn't break the technology; they used stolen passwords on accounts without multi-factor authentication."

## Whiteboard prompt

Draw a security data lake for a 300-project agency on Google Cloud: org → folders → projects; an aggregated log sink at the org; a `sec-logs` project with a partitioned BigQuery dataset; the sink's writer identity; SOC analysts with `dataViewer` + `jobUser`; an authorized view for app owners; cost guardrails (quota, maximum bytes billed). Then add one hunt as a box ("password spraying: one IP, many users, all failures") and show where its alert goes.

## What you can honestly claim

- **After reading + quiz:** "I've studied managed relational and NoSQL databases and data warehouses across Google Cloud, AWS, and Azure, including BigQuery's pricing and security model and how it's used as a security data lake."
- **After completing the lab:** "In a personal lab I used the BigQuery sandbox to query public datasets, applied dry runs and maximum-bytes-billed limits to control cost, loaded synthetic authentication logs and wrote SQL hunts for password spraying and suspicious sign-ins, and audited query history through INFORMATION_SCHEMA and audit logs." Add the DynamoDB and Azure SQL sentences only if you did those parts.
- **Still requires (cert / production experience / clearance):** administering production databases, designing data models or migrations at scale, operating a production security data lake or SIEM, and working with real agency data. Don't claim "data engineer" or "DBA." Splunk experience you already have is claimable *at the level you actually used it* (homelab vs professional, plus your Splunk Core User cert) and transfers — say so precisely, and say BigQuery is studied plus lab. The Google Professional Data Engineer exam (⚠️ not checked this run) and the Associate Cloud Engineer are claimable milestones.
