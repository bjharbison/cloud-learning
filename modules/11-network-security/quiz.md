# 11 Quiz — Network security controls

1. Compare AWS security groups and network ACLs on four dimensions.
<details><summary>Answer</summary>

Attachment: SG on an instance's network interface; NACL on a subnet. Rules: SG allow-only; NACL allow and deny. Evaluation: SG considers all rules together; NACL processes numbered rules lowest-first, first match wins. State: SG stateful; NACL stateless (return traffic must be allowed explicitly). AWS recommends SGs as the primary control.
</details>

2. Are Google VPC firewall rules and Azure NSGs stateful or stateless? What's each cloud's default for egress?
<details><summary>Answer</summary>

Both stateful. Egress is allowed by default everywhere: Google's implied allow-egress rule; AWS security groups' default allow-all outbound; Azure NSGs' `AllowInternetOutBound` default rule.
</details>

3. A folder admin creates a VPC firewall rule allowing RDP from `0.0.0.0/0`, but the organization has a hierarchical firewall policy denying it. What happens?
<details><summary>Answer</summary>

The traffic is denied. Hierarchical policies are evaluated first, and lower-level rules can't override a higher-level rule; they only see traffic the higher policy passes down with `goto_next`.
</details>

4. Why does Google recommend targeting firewall rules by service account or secure tag rather than network tag?
<details><summary>Answer</summary>

Anyone who can edit a VM can add a network tag and inherit the rules attached to it. Service-account targets and secure tags are controlled through IAM, so applying them requires specific permissions.
</details>

5. What is Azure Virtual Network Manager's security admin rule, and how does it relate to NSGs?
<details><summary>Answer</summary>

A centrally defined rule applied to VNets in a network group, evaluated before NSGs. Actions: Allow (NSGs still evaluate), Always allow (skip NSGs), Deny (blocked). It lets a central team, e.g., block 22/3389/445 everywhere regardless of app teams' NSGs — Azure's closest analog to Google's hierarchical firewall policies.
</details>

6. An internal-only VM (no external IP, no NAT) has IAM rights to a bucket but can't read it. What's missing, and what are the two special domains you can use?
<details><summary>Answer</summary>

Private Google Access on the subnet (or a Private Service Connect endpoint). Domains: `private.googleapis.com` (199.36.153.8/30) for most Google APIs, and `restricted.googleapis.com` (199.36.153.4/30), which serves only APIs supported by VPC Service Controls. Using either requires private DNS records pointing the API names at the VIP.
</details>

7. Spot the misconfiguration: "We created an Azure Private Endpoint for our storage account, so it's no longer exposed."
<details><summary>Answer</summary>

Unless public network access is disabled on the storage account, it's still reachable over its public endpoint; the private endpoint just adds a private path. Microsoft's guidance is to turn off public access after configuring the private endpoint (and get private DNS right).
</details>

8. Gateway endpoint vs interface endpoint on AWS — services, cost, reach.
<details><summary>Answer</summary>

Gateway endpoints: S3 and DynamoDB only, implemented as a route-table prefix-list route, no charge, not PrivateLink, not reachable from on-prem. Interface endpoints (PrivateLink): ENIs with private IPs for many AWS and partner services, hourly plus per-GB charges, reachable from on-prem over VPN/Direct Connect.
</details>

9. An attacker steals a service-account key and calls `storage.objects.get` from a laptop. Why doesn't a firewall stop it, and what Google Cloud control does?
<details><summary>Answer</summary>

The call goes to Google's public API endpoint over HTTPS with a valid credential — it never crosses the customer's VPC firewall. VPC Service Controls: with Cloud Storage restricted inside a perimeter, requests from outside are denied (unless an access level or ingress rule allows them) and recorded in Policy Denied audit logs.
</details>

10. What is dry-run mode in VPC Service Controls, and why use it?
<details><summary>Answer</summary>

It evaluates a perimeter and logs would-be violations (Policy Denied entries with `dryRun: true`) without blocking anything. It lets you discover legitimate traffic that needs ingress/egress rules or access levels before enforcement, avoiding outages.
</details>

11. Scenario: an agency wants to ensure analysts in a BigQuery project can't copy data to buckets in personal projects, and that leaked credentials are useless from outside agency networks. Recommend a design.
<details><summary>Answer</summary>

Put the analytics projects (and their storage projects) in a VPC Service Controls perimeter restricting BigQuery and Cloud Storage; access levels for agency egress IP ranges/managed devices; narrowly scoped ingress/egress rules for necessary partners; roll out in dry run, then enforce. Keep least-privilege IAM. Internal-only VMs use Private Google Access with `restricted.googleapis.com`. Monitor Policy Denied logs. Explain it complements IAM, not replaces it.
</details>

12. What would AWS and Azure use for a comparable data-exfiltration boundary?
<details><summary>Answer</summary>

AWS: the data perimeter pattern — SCPs, RCPs, resource-based policies, and VPC endpoint policies with conditions like `aws:PrincipalOrgID`, `aws:ResourceOrgID`, `aws:SourceVpce`. Azure: Private Endpoints (mapped to specific resources) with public access disabled, plus network security perimeter around PaaS resources.
</details>
