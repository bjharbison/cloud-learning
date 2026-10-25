# 11 Interview Prep — Network security controls

## Likely questions

### Q1. "Explain VPC Service Controls to a customer's security officer."

**Answer outline:**
- IAM decides *who*; firewalls decide *which packets*. Neither stops a valid credential used from the wrong place, or an insider copying data to an outside project — those are just API calls.
- VPC Service Controls draws a perimeter around projects and restricted services: requests from outside are denied (unless an access level or ingress rule allows them), and data can't move to resources outside without an egress rule.
- Roll out in dry run; watch Policy Denied logs; then enforce.
- Honest limits: complements IAM, doesn't replace it; not designed for comprehensive metadata control; needs careful exception management.
- AWS: data perimeter pattern with endpoint and resource policies. Azure: Private Endpoints + network security perimeter.

**Strong signal:** using the stolen-key and insider-copy scenarios, and naming dry run.
**Avoid:** "it makes data exfiltration impossible."

### Q2. "Compare network security controls across Google Cloud, AWS, and Azure."

**Answer outline:**
- Google: stateful VPC firewall rules and network firewall policies (target by service account/secure tag), hierarchical policies at org/folder that lower levels can't override; Cloud NGFW tiers up to IPS.
- AWS: stateful allow-only security groups (can reference other SGs) + stateless subnet NACLs; Firewall Manager and Network Firewall for central/L7.
- Azure: stateful NSGs on subnet/NIC with ASGs and service tags; Virtual Network Manager security admin rules evaluated first; Azure Firewall.
- Common: default egress allow — design egress deliberately.

### Q3. "How do you let private workloads use cloud services without internet access?"

**Answer outline:**
- Google: Private Google Access per subnet (optionally `restricted.googleapis.com` with VPC-SC); Private Service Connect endpoints for Google APIs and published services like Cloud SQL.
- AWS: gateway endpoints (S3/DynamoDB, free) and interface endpoints (PrivateLink); endpoint policies restrict which resources.
- Azure: Private Endpoints (one specific resource, preferred) or service endpoints.
- Then disable the public endpoint and fix DNS.

### Q4. "A customer's VMs all have allow-all egress. Why care, and what would you do?"

**Answer outline:**
- Egress is how C2 and exfiltration work (T1071, T1048), and how data moves to attacker accounts (T1537).
- Remove public IPs (org policy), central NAT, deny-by-default egress with explicit allows, FQDN filtering for necessary internet destinations, API-level perimeter for cloud-to-cloud copying.
- Log denied egress — it's high-signal telemetry.

### Q5. "How would you detect someone tampering with network controls?"

**Answer outline:**
- Admin Activity / CloudTrail / Activity Log events for firewall rules, policies, security groups, NSGs, and perimeters — alert on `0.0.0.0/0` ingress and on changes by unusual principals (T1562.007).
- Firewall Rules Logging on deny rules; VPC Flow Logs for traffic patterns.
- VPC-SC Policy Denied logs for credential misuse from outside.
- Preventive: hierarchical policies / AVNM admin rules so a single compromised project admin can't open the org.

## 60-second executive explanation

"Think of our cloud security in layers. At the outer layer, our central security team sets rules for the whole organization — for example, no system anywhere may accept remote logins from the internet — and individual projects can't override them. Inside that, each team controls exactly which systems can talk to each other. We also stop systems from reaching out to the internet unless there's a reason, because that's how stolen data and malware usually travel. Finally, on Google Cloud we draw a boundary around our sensitive data services themselves: even someone holding a valid password or key can't pull data out from outside our environment, and insiders can't copy it somewhere unauthorized. All of these settings are ours to configure — the cloud provides the tools, and we're accountable for using them."

## Whiteboard prompt

Draw an agency analytics environment on Google Cloud: an org-level hierarchical firewall policy (deny 22/3389 from the internet, `goto_next` for IAP), a Shared VPC with internal-only VMs, Private Google Access via `restricted.googleapis.com`, deny-by-default egress, and a VPC Service Controls perimeter around the BigQuery and Cloud Storage projects with an access level for agency IP ranges. Then draw three attacks — open RDP rule, leaked service-account key used from home, insider copying to a personal bucket — and mark which control stops each and which log shows it.

## What you can honestly claim

- **After reading + quiz:** "I've studied network security controls across Google Cloud, AWS, and Azure — firewall rules and policies, security groups and NACLs, NSGs, private service access, egress control — and VPC Service Controls as an API-level data-exfiltration boundary."
- **After completing the lab:** "In a personal lab I secured an internal-only VM with a Google Cloud network firewall policy allowing only IAP SSH, enabled Private Google Access, implemented deny-by-default egress with a narrow allow to Google's private API range, and analyzed allowed and denied traffic in firewall logs." Add "and configured a VPC Service Controls perimeter in dry-run mode and analyzed its Policy Denied audit logs" only if you completed A7; add the AWS/Azure sentences only if you did them.
- **Still requires (cert / production experience / clearance):** designing, enforcing, and operating VPC Service Controls perimeters or org-wide firewall policy in production; implementing TIC or agency network-security requirements; network security engineering roles. Don't claim "implemented VPC Service Controls" from a dry-run lab. The Google Professional Cloud Security Engineer exam covers these controls and is a claimable milestone.
