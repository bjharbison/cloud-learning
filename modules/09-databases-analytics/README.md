# 09 — Databases and analytics: managed SQL and NoSQL, data warehouses, BigQuery as a security data lake

> **In one sentence:** you'll be able to steer a customer to the right managed database family in a five-minute conversation, explain why BigQuery isn't "just a database," and sketch how a security team uses it to hunt across years of logs.

**Prereqs:** modules 00–08 (module 08 for object storage; module 04 for billing) · **Time:** ~3 hours incl. lab · **Phase:** 2

## Learning objectives

- Explain what "managed database" means on the shared responsibility line — what the provider runs and what you still own.
- Place a workload in the right family: **relational**, **document**, **wide-column**, **key-value/in-memory**, **globally distributed**.
- Compare the database lineups on Google Cloud, AWS, and Azure.
- Explain **data warehouses** — columnar storage, separation of storage and compute, pay-per-query — and compare **BigQuery**, **Redshift**, and Azure's options.
- Describe **BigQuery as a security data lake**: logs in, SQL hunting out, cost controls, and fine-grained access.

## Why this matters for the target roles

- **Customer engineer / architect:** "Which database?" comes up in nearly every first meeting. You need the decision tree, not DBA internals. BigQuery is one of Google Cloud's flagship differentiators.
- **Cloud security:** an exposed database or a warehouse login without MFA is a direct path to bulk data theft — the 2024 Snowflake-customer campaign is the case study.
- **CTI:** analysts increasingly hunt in SQL over petabyte-scale log stores. Knowing how BigQuery bills and secures data makes you useful on day one.

---

## Concepts

### What "managed" means for a database

**Plain version:** the provider installs, patches, backs up, replicates, and fails over the database engine. You design the schema, write the queries, and decide who can connect.

On module 01's sliding line, a managed database is PaaS:

| Provider runs | You still own |
|---|---|
| Servers, storage, OS, engine patching | **Who can connect** — network path (public IP or private) and firewall/authorized networks |
| Automated backups, replicas, failover | **Database users and authentication** — passwords vs IAM/Entra-based login |
| Encryption at rest by default | Key choice (default vs customer-managed, module 16) |
| Monitoring plumbing | Schema, data, queries, and data classification |
| | Backup retention settings, deletion protection, point-in-time recovery |

**Bridge to your homelab:** it's the difference between running InfluxDB in a Docker container you patch yourself and paying someone to run it — you still decide who gets a login and which VLAN can reach port 8086.

### Database families — the five-minute decision tree

| If the customer needs… | Family | Plain meaning | Homelab / intel bridge |
|---|---|---|---|
| Tables, joins, transactions, existing SQL apps | **Relational (OLTP)** | Rows and columns, strict schema, ACID transactions | Any app backed by PostgreSQL or MySQL |
| Flexible JSON-like records for web/mobile apps | **Document** | Each record is a nested document; schema can vary | A case file where every record has different fields |
| Massive write throughput, time-series, IoT | **Wide-column** | Huge sparse tables keyed for fast lookup by row key | Your MQTT → InfluxDB sensor pipeline, at millions of writes per second |
| Sub-millisecond cache or session store | **Key-value / in-memory** | Lookup by key, held in RAM | Redis in front of a slow app |
| One relational database across regions with strong consistency | **Globally distributed relational** | SQL semantics, horizontal scale, multi-region | — (this is where Google's Spanner is unusual) |
| Analytics over huge history | **Data warehouse (OLAP)** | Columnar, scan billions of rows for aggregates | Splunk — but SQL, and storage separated from compute |

**OLTP vs OLAP:** **OLTP** (online transaction processing) is many small reads and writes — "update this order." **OLAP** (online analytical processing) is few, huge reads — "count failed logins by country for three years." Different engines win at each.

### Google Cloud's lineup

- **Cloud SQL** — managed MySQL, PostgreSQL, and SQL Server. The default answer for lift-and-shift of a conventional app database.
- **AlloyDB for PostgreSQL** — PostgreSQL-compatible, built for demanding transactional and mixed analytical workloads. (AlloyDB Omni runs outside Google Cloud.)
- **Spanner** — globally consistent relational database with horizontal scale and up to a 99.999% availability SLA. The architectural standout.
- **Firestore** — serverless document database (also offered with MongoDB compatibility).
- **Bigtable** — wide-column NoSQL for high-throughput, low-latency workloads (time-series, IoT, ad tech).
- **Memorystore** — managed in-memory service for Valkey, Redis, and Memcached.
- Also: Oracle Database@Google Cloud, Bare Metal Solution for Oracle, and MongoDB Atlas via the marketplace — relevant when a migration involves Oracle.

### Data warehouses and why BigQuery is different

**Plain version:** a warehouse is a database built for asking big questions of a lot of history. **Columnar storage** stores each column together, so a query reading 3 columns out of 100 reads ~3% of the data.

**BigQuery** adds two ideas:

1. **Serverless and separated.** No cluster to size. Storage and compute scale independently; you don't provision nodes.
2. **Pay per query (on-demand) or per capacity.** On-demand pricing charges by **bytes scanned** — $6.25 per TiB in the US, with the **first 1 TiB per month free** (plus 10 GiB of storage free). Each query is billed at least 10 MB per table referenced. Alternatively, **editions** (Standard, Enterprise, Enterprise Plus) bill by **slots** — units of compute capacity.

Cost consequences you must say out loud to a customer:

- `SELECT *` on a wide table scans every column. Select only what you need.
- **Partitioning** (by date, usually) and **clustering** let BigQuery skip data. A partition filter can cut a scan by orders of magnitude.
- **Dry runs** estimate bytes before you run; **maximum bytes billed** makes a query fail rather than overspend; project-level custom quotas cap daily scanning.
- Storage not modified for 90 days drops to the cheaper **long-term** rate automatically.

**AWS:** **Amazon Redshift** (provisioned clusters or **Redshift Serverless**) is the warehouse; **Athena** runs serverless SQL directly over files in S3. **Azure:** **Azure Synapse Analytics** (dedicated SQL pools) and **Microsoft Fabric**'s **Fabric Data Warehouse**; Microsoft publishes migration guidance and a migration assistant from Synapse dedicated SQL pools to Fabric.

**Bridge:** BigQuery's on-demand model is Splunk's licensing turned inside out. Splunk charges for what you ingest; BigQuery charges mainly for what you *scan*. Retaining years of logs is cheap; careless queries over them are not.

### BigQuery as a security data lake

This is the use case to know cold for a security-minded CE conversation.

**The pattern Google documents for security log analytics:**

1. **Enable the logs** — Admin Activity is always on; turn on Data Access audit logs for sensitive services (module 08 showed why).
2. **Route them centrally** — an **organization-level aggregated log sink** captures every project's logs into one destination.
3. **Analyze with SQL** — either in a BigQuery dataset (day-partitioned tables, with partition expiration matching your retention requirement), or in a Cloud Logging bucket upgraded to **Observability Analytics** with a **linked BigQuery dataset** (no BigQuery ingestion or storage cost; you pay for queries). Google's open-source **Community Security Analytics** project supplies starter detection queries.

**Why customers like it:** long retention at storage prices, SQL that analysts already know, joins against asset inventories, threat-intel feeds, or HR data, and no index to size. Google's own SIEM, **Google Security Operations** (module 22), is the purpose-built option when a team needs detection rules, case management, and curated threat intel on top.

**The peers:**

- **AWS:** **Amazon Security Lake** collects security data from AWS, SaaS, on-prem, and other clouds into S3 buckets in your own account, normalized to the **Open Cybersecurity Schema Framework (OCSF)**; you query with Athena or partner tools.
- **Azure:** **Microsoft Sentinel data lake** (announced generally available in September 2025) gives Sentinel a low-cost, long-retention tier alongside the analytics tier.

**Bridge to your Splunk background:** an aggregated sink is your universal forwarder fleet; the BigQuery dataset is the index; partitioning is your time-bounded search; `INFORMATION_SCHEMA.JOBS` is `_audit` — who searched what, and how much it cost.

### Securing BigQuery (and warehouses generally)

| Layer | BigQuery control |
|---|---|
| Who can see a dataset or table | IAM on project, dataset, or table (`roles/bigquery.dataViewer`, `dataEditor`, `jobUser`) |
| A curated slice without exposing the source | **Authorized views** — viewers query the view; they have no access to the underlying dataset |
| Which rows a user sees | **Row-level security** (row access policies) |
| Which columns a user sees | **Column-level access control** with **policy tags**; **dynamic data masking** |
| Who queried what | BigQuery **Data Access audit logs** — on by default and **can't be disabled** — plus `INFORMATION_SCHEMA.JOBS` views |
| Data leaving the boundary | VPC Service Controls (module 11) |

Note the contrast with module 08: Cloud Storage object reads are *not* logged by default; BigQuery data access always is.

> **Shared responsibility:** the provider runs the engines, storage, replication, and patching. **Network exposure (public vs private IP, authorized networks), database users and authentication, IAM on datasets, row/column policies, backup and deletion-protection settings, and what data goes where — always the customer's.**

---

## Text diagram — BigQuery as a security data lake

```
 Org: agency.gov
   ├─ Folder: Prod ── projects … ┐
   ├─ Folder: Dev  ── projects … ├─► Aggregated log sink (org level, include children)
   └─ Folder: Sec  ─────────────┘         │  Admin Activity + chosen Data Access logs
                                           ▼
            Project sec-logs ── BigQuery dataset audit_logs (US, day-partitioned, 400-day partition expiry)
                 │   IAM: sink writer SA → dataEditor on dataset only
                 │   IAM: soc-analysts group → dataViewer + jobUser
                 │   Authorized view → app owners see only their projects' rows
                 ▼
     SQL hunts (CSA queries) · scheduled queries → alerts · join with threat-intel table
                 │
     Every query itself logged (BigQuery Data Access logs, always on) + INFORMATION_SCHEMA.JOBS
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Managed MySQL/PostgreSQL/SQL Server | Cloud SQL | Amazon RDS | Azure Database for MySQL/PostgreSQL (flexible server); Azure SQL Database / SQL Managed Instance | Azure's SQL Server heritage shows: several SQL Server flavors |
| High-performance PostgreSQL-compatible | AlloyDB for PostgreSQL | Amazon Aurora (PostgreSQL/MySQL-compatible) | Azure Database for PostgreSQL ⚠️ (Azure's Cosmos DB for PostgreSQL not compared this run) | |
| Globally distributed relational | Spanner (up to 99.999% SLA) | Amazon Aurora DSQL (serverless distributed SQL, GA May 2025) | Cosmos DB (multi-model, not relational in the same sense) | Spanner is the long-standing reference design |
| Document | Firestore | Amazon DocumentDB ⚠️; DynamoDB (key-value/document) | Azure Cosmos DB | |
| Wide-column / high-throughput NoSQL | Bigtable | DynamoDB; Amazon Keyspaces ⚠️ | Cosmos DB (Cassandra API) ⚠️ | |
| In-memory | Memorystore (Valkey, Redis, Memcached) | Amazon ElastiCache ⚠️ | Azure Cache for Redis ⚠️ | Products in flux industry-wide after Redis licensing changes |
| Data warehouse | BigQuery (serverless; on-demand per TiB or editions/slots) | Redshift (provisioned or Serverless); Athena for SQL on S3 | Synapse Analytics dedicated SQL pools; Fabric Data Warehouse | BigQuery has no cluster to size |
| Security data lake | BigQuery / Observability Analytics + aggregated sinks; Google SecOps | Amazon Security Lake (S3 + OCSF) | Microsoft Sentinel data lake | |
| Free allowance | BigQuery: 1 TiB queries + 10 GiB storage/month; **sandbox** needs no billing account | Free-plan credits ⚠️ specific DB allowances not verified this run | Azure SQL Database free offer: up to 10 DBs × 100k vCore-s + 32 GB/month for the subscription's lifetime; Cosmos DB 1,000 RU/s + 25 GB always free | |
| Private connectivity to managed DB | Private Service Connect (recommended) or private services access | Private subnets / PrivateLink | Private Endpoint | Module 11 |

## Administer and monitor it

- **Day to day:** sizing (vCPU/memory or capacity units), maintenance windows, backups and **point-in-time recovery (PITR)**, read replicas, **deletion protection**, version upgrades.
- **Defaults to check:** DynamoDB PITR is **off** until you enable it (1–35 days). Cloud SQL and RDS deletion protection and backup retention should be confirmed per instance (⚠️ defaults vary by console vs CLI and weren't verified this run).
- **Logs:** instance changes are control-plane events (Cloud Audit Logs, CloudTrail, Activity Log). Database-level logs (logins, queries) need engine audit settings (e.g., pgAudit) or the service's data-access logging. BigQuery query logs are always on.
- **Cost:** BigQuery bytes scanned and slot usage (`INFORMATION_SCHEMA.JOBS`, billing export from module 04); idle database instances bill 24×7 — the classic forgotten lab resource.

## Security angle

1. **Database on a public IP with a wide-open authorized network or firewall** (`0.0.0.0/0` to 5432/3306/1433). Use private IP; if public is unavoidable, use the **Cloud SQL Auth Proxy** (IAM-authorized, encrypted) and narrow allowlists.
2. **Password-only logins, no MFA, no rotation** — exactly what enabled the Snowflake-customer thefts. Prefer IAM database authentication (Cloud SQL), IAM auth (RDS), or Entra-only authentication (Azure SQL).
3. **Over-broad dataset access** — `bigquery.dataViewer` on the whole project, or `allAuthenticatedUsers` on a dataset. Use dataset-level grants, authorized views, row/column policies.
4. **No PITR or deletion protection** — ransomware or a mistaken `DROP` becomes permanent.
5. **Cost as a weapon** — an attacker (or an intern) with `jobUser` can run expensive scans; set custom query quotas and maximum bytes billed.
6. **Sensitive data in the wrong place** — PII copied into a sandbox project or an unrestricted dataset.

## Threat intel angle

- **Case study — UNC5537 and Snowflake customers (Mandiant, June 2024).** Credentials stolen by infostealers (some dating back to 2020) were used to log in to customer Snowflake instances that lacked MFA, hadn't rotated passwords, and had no network allowlists; about 165 organizations were notified. Mandiant found no breach of Snowflake's own environment. Lesson for any warehouse: identity, MFA, and network allowlists are the customer's — and stolen-credential logins look like normal logins.
- **T1078.004 Valid Accounts: Cloud Accounts** — the entry point in that campaign.
- **T1530 Data from Cloud Storage** (module 08) and bulk export via warehouse queries or snapshots to attacker-controlled locations.
- **T1190 Exploit Public-Facing Application** — internet-exposed database ports are routinely scanned and attacked.
- **T1485 / T1486** — destruction or encryption of database contents; PITR and protected backups are the counter.

**Detection ideas:** query volume or bytes scanned far above a user's baseline; exports to buckets outside the org; logins from new geographies or hosting providers; new dataset IAM grants to external principals.

**Bridge to your CTI work:** the Snowflake campaign is a collection-management lesson — the adversary didn't need an exploit, just a source (infostealer logs) and an unguarded collection point. For your customers, credential-exposure monitoring is part of protecting the warehouse.

## Public sector notes

- **Authorization scope:** confirm each database and analytics service is in scope for the customer's FedRAMP level, IL, or Assured Workloads package before designing (modules 26–27).
- **Data location:** BigQuery datasets have a location (e.g., `US`, a region); keep sensitive data in the authorized one.
- **Budget predictability:** on-demand BigQuery is pay-per-scan; agencies with fixed appropriations often prefer capacity (editions/commitments) or strict query quotas (module 04).
- **Mission analytics:** fusing many sources (logs, sensor data, open-source event data) at scale is a genuine fit for a serverless warehouse — and every join raises the data-handling question of who may see the combined product.

## Key takeaways

- Managed database = PaaS: the provider runs the engine; you own network exposure, logins, IAM, backups settings, and the data.
- Match the family to the workload: relational (Cloud SQL/AlloyDB), global relational (Spanner), document (Firestore), wide-column (Bigtable), in-memory (Memorystore).
- Warehouses are columnar and built for big scans. BigQuery is serverless and bills by bytes scanned (first 1 TiB/month free) or by slots.
- Control BigQuery cost with column selection, partitioning, dry runs, maximum bytes billed, and quotas.
- BigQuery makes a strong security data lake: aggregated sinks in, SQL hunting out, data-access logs always on, fine-grained access with authorized views and row/column policies.
- The 2024 Snowflake-customer campaign: no exploit, just stolen passwords and no MFA. Identity is **always the customer's**.

## Sources

- [Google Cloud — Databases](https://cloud.google.com/products/databases)
- [Google Cloud — BigQuery pricing](https://cloud.google.com/bigquery/pricing)
- [Google Cloud — Try BigQuery using the sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox)
- [Google Cloud — BigQuery public datasets](https://docs.cloud.google.com/bigquery/public-data)
- [Google Cloud — Estimate and control costs (BigQuery)](https://docs.cloud.google.com/bigquery/docs/best-practices-costs)
- [Google Cloud — Authorized views](https://docs.cloud.google.com/bigquery/docs/authorized-views), [Row-level security](https://docs.cloud.google.com/bigquery/docs/row-level-security-intro), [Column-level access control](https://docs.cloud.google.com/bigquery/docs/column-level-security), [Data masking](https://docs.cloud.google.com/bigquery/docs/column-data-masking-intro)
- [Google Cloud — Enable Data Access audit logs (BigQuery can't be disabled)](https://docs.cloud.google.com/logging/docs/audit/configure-data-access)
- [Google Cloud Architecture Center — Security log analytics in Google Cloud](https://docs.cloud.google.com/architecture/security-log-analytics)
- [Google Cloud — Analyze logs using Logs Explorer and Observability Analytics](https://docs.cloud.google.com/logging/docs/log-analytics)
- [Google Cloud — Cloud SQL private IP](https://docs.cloud.google.com/sql/docs/postgres/private-ip) and [About the Cloud SQL Auth Proxy](https://docs.cloud.google.com/sql/docs/mysql/sql-proxy)
- [Google Cloud Threat Intelligence — UNC5537 targets Snowflake customer instances (Jun 2024)](https://cloud.google.com/blog/topics/threat-intelligence/unc5537-snowflake-data-theft-extortion)
- [Google Cloud — Free cloud features](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [AWS — Amazon Security Lake](https://aws.amazon.com/security-lake/)
- [AWS — Amazon Aurora DSQL is now generally available (May 2025)](https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-aurora-dsql-generally-available/)
- [AWS — What is Amazon Redshift Serverless?](https://docs.aws.amazon.com/redshift/latest/mgmt/serverless-whatis.html)
- [AWS — DynamoDB point-in-time recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html)
- [Microsoft — Try Azure SQL Database for free](https://learn.microsoft.com/en-us/azure/azure-sql/database/free-tier?view=azuresql)
- [Microsoft — Create a server with Microsoft Entra-only authentication](https://learn.microsoft.com/en-us/azure/azure-sql/database/authentication-azure-ad-only-authentication-create-server?view=azuresql)
- [Microsoft — Explore free Azure services](https://azure.microsoft.com/en-gb/pricing/free-services)
- [Microsoft Fabric — Migrating Azure Synapse dedicated SQL pools to Fabric](https://learn.microsoft.com/en-us/fabric/data-warehouse/migration-synapse-dedicated-sql-pool-warehouse)
- [Microsoft Security Blog — Microsoft Sentinel data lake is now generally available](https://techcommunity.microsoft.com/blog/microsoft-security-blog/microsoft-sentinel-data-lake-is-now-generally-available/4456342)
- [MITRE ATT&CK — T1078.004](https://attack.mitre.org/techniques/T1078/004/), [T1530](https://attack.mitre.org/techniques/T1530/), [T1190](https://attack.mitre.org/techniques/T1190/)

Verified: 2026-10-25
