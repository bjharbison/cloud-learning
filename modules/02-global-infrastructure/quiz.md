# 02 Quiz — Global infrastructure

1. In one line each: region, zone, edge location.
<details><summary>Answer</summary>

Region: a geographic area with several separate data-center sites. Zone: one of those sites, an isolated failure domain. Edge location: a smaller site near users for caching, DNS, and traffic entry.
</details>

2. Classify as zonal, regional, or global on Google Cloud: a Compute Engine VM; a VPC network; a regional managed instance group; an IAM policy.
<details><summary>Answer</summary>

VM: zonal. VPC network: global. Regional MIG: regional. IAM policy: global.
</details>

3. What's the biggest networking difference between Google Cloud and the other two clouds at the regional level?
<details><summary>Answer</summary>

Google Cloud VPC networks are global (subnets in many regions, one network). AWS VPCs and Azure VNets are regional and need peering or a hub to connect regions.
</details>

4. Your AWS account and a partner's account both deploy to `us-east-1a`. Are you guaranteed to be in the same facility? How do you check?
<details><summary>Answer</summary>

No — in some older Regions, AZ names map to different physical zones per account (accounts created from November 2025 get a uniform mapping). Compare AZ IDs (e.g., `use1-az1`) with `aws ec2 describe-availability-zones`.
</details>

5. Define RTO and RPO. A system can be down 4 hours but lose at most 15 minutes of data. Which number is which?
<details><summary>Answer</summary>

RTO = max time offline (4 hours). RPO = max data loss measured in time (15 minutes).
</details>

6. An agency needs near-zero RTO for a citizen-facing service during a regional outage. Cold, warm, or hot — and what's the trade-off?
<details><summary>Answer</summary>

Hot (active-active across regions). Trade-off: highest cost and complexity (data replication, consistency, running two full stacks).
</details>

7. Compute Engine promises ≥ 99.99% for instances in multiple zones. Roughly how much downtime per month is that, and what do you get if Google misses it?
<details><summary>Answer</summary>

About 4.4 minutes per month. If missed, a financial credit (10%, 25%, or 100% of the affected service's monthly bill depending on how far uptime fell), claimed within 60 days. Not uptime.
</details>

8. Your app calls service X (99.95%) and service Y (99.99%); both must work. What's the best composite availability?
<details><summary>Answer</summary>

About 99.94% (0.9995 × 0.9999). Chaining lowers availability; redundancy raises it.
</details>

9. Single-instance compute SLA: which is higher, Google Compute Engine or Amazon EC2, and by how much?
<details><summary>Answer</summary>

Google: ≥ 99.9% for most families (99.95% for memory-optimized). AWS: 99.5% instance-level. Google's single-VM promise is higher.
</details>

10. Spot the gap: "We only use us-east-1, so we turned on CloudTrail and GuardDuty there." What's the risk and the fix?
<details><summary>Answer</summary>

Attackers can operate in unmonitored regions (ATT&CK T1535). Fix: monitor all regions, and block unused regions with policy (AWS SCP on requested region; Google resource-location org policy; Azure Policy "Allowed locations").
</details>

11. Does an Azure region pair give you disaster recovery automatically?
<details><summary>Answer</summary>

No. Microsoft says pairing doesn't automatically make your app more resilient. It gives recovery prioritization, staggered updates, and residency within a geography; you still design and test DR.
</details>

12. Compare how AWS, Azure, and Google Cloud approach U.S. government workloads at the infrastructure level.
<details><summary>Answer</summary>

AWS: separate GovCloud (US) Regions. Azure: Azure Government, a physically isolated instance. Google: Assured Workloads control packages (residency, personnel, service restrictions) on commercial regions, plus Google Distributed Cloud for disconnected needs.
</details>
