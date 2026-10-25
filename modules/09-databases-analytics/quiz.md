# 09 Quiz — Databases and analytics

1. In a managed database (Cloud SQL, RDS, Azure SQL Database), name three things the provider handles and three the customer still owns.
<details><summary>Answer</summary>

Provider: servers/OS, engine patching, automated backups/replication/failover infrastructure (also default encryption at rest). Customer: network exposure (public vs private IP, authorized networks/firewall), database users and authentication, IAM/data access, schema and data, backup retention/PITR/deletion-protection settings. It's PaaS on module 01's sliding line.
</details>

2. Match the workload to a Google Cloud database: (a) an existing PostgreSQL app being migrated; (b) a mobile app with flexible JSON records; (c) millions of sensor writes per second; (d) a single relational database serving users on three continents with strong consistency; (e) a session cache.
<details><summary>Answer</summary>

(a) Cloud SQL for PostgreSQL (or AlloyDB if performance demands it); (b) Firestore; (c) Bigtable; (d) Spanner; (e) Memorystore.
</details>

3. What's the difference between OLTP and OLAP, and which is BigQuery?
<details><summary>Answer</summary>

OLTP: many small, fast reads/writes with transactions (an order system). OLAP: fewer, very large analytical scans and aggregations (three years of logs). BigQuery is an OLAP data warehouse.
</details>

4. How does BigQuery on-demand pricing work, and what's free?
<details><summary>Answer</summary>

Charged by bytes processed by queries — $6.25 per TiB in the US — with the first 1 TiB per month free, plus 10 GiB of storage free per month. Minimum 10 MB billed per table referenced. Alternatively, editions bill for slot capacity.
</details>

5. Name four ways to keep a BigQuery query from being expensive.
<details><summary>Answer</summary>

Select only needed columns (not `SELECT *`); filter on partitioned columns (usually date) and use clustering; dry-run to see estimated bytes; set maximum bytes billed so over-budget queries fail; set project/user custom query quotas.
</details>

6. What are the BigQuery sandbox's terms?
<details><summary>Answer</summary>

No billing account or credit card; 10 GiB storage over the project's lifetime; 1 TiB of queries per month; tables, views, and partitions expire after 60 days; no streaming, DML, or Data Transfer Service.
</details>

7. Spot the misconfiguration: "Our Cloud SQL instance has a public IP with authorized network `0.0.0.0/0` so contractors can connect from anywhere; the passwords are strong."
<details><summary>Answer</summary>

The database port is reachable from the entire internet; strong passwords don't stop credential theft (infostealers) or engine vulnerabilities. Use private IP (Private Service Connect is Google's recommended option), or the Cloud SQL Auth Proxy with IAM authorization and IAM database authentication, and narrow allowlists. Network exposure is the customer's responsibility.
</details>

8. Which BigQuery feature lets a team query a curated slice of a dataset without having any access to the source dataset?
<details><summary>Answer</summary>

An authorized view. (Row-level security limits rows; column-level access control with policy tags and data masking limits columns.)
</details>

9. BigQuery Data Access audit logs vs Cloud Storage Data Access audit logs — what's the default for each?
<details><summary>Answer</summary>

BigQuery's are on by default and can't be disabled. Cloud Storage's are off by default (module 08). Admin Activity logs are always on for both.
</details>

10. Scenario: a CISO wants to keep three years of audit logs from 300 projects and let analysts hunt with SQL, cheaply. Sketch a Google Cloud design.
<details><summary>Answer</summary>

An organization-level aggregated log sink (including child resources) routing Admin Activity plus selected Data Access logs to a central security project — either a BigQuery dataset with day-partitioned tables and partition expiration at ~3 years, or a log bucket upgraded to Observability Analytics with a linked BigQuery dataset. IAM: sink writer only to that dataset; analysts get dataViewer + jobUser; authorized views for app owners. Cost controls: partition filters, maximum bytes billed, quotas. Use Community Security Analytics queries as a starting point; consider Google SecOps if they need full SIEM capabilities.
</details>

11. What were the three enabling conditions in the 2024 UNC5537 campaign against Snowflake customers, and was Snowflake itself breached?
<details><summary>Answer</summary>

No MFA on accounts; stolen (infostealer-harvested) credentials that had never been rotated, some from 2020; no network allowlists. Mandiant found no evidence of a breach of Snowflake's own enterprise environment — all traced to customer credentials.
</details>

12. Name the security data lake offering on AWS and on Azure.
<details><summary>Answer</summary>

AWS: Amazon Security Lake (data in S3 in your account, normalized to OCSF). Azure: Microsoft Sentinel data lake.
</details>
