# 12 Quiz — Load balancing, DNS, CDN, WAF, and DDoS protection

1. What's the difference between a proxy and a passthrough load balancer, and which one lets the backend see the real client IP in the packet?
<details><summary>Answer</summary>

A proxy load balancer terminates the client's connection and opens a new one to the backend (the client IP travels in a header such as `X-Forwarded-For`). A passthrough load balancer forwards packets unchanged, so the backend sees the real client IP and replies directly. On Google Cloud, passthrough Network Load Balancers preserve client IP.
</details>

2. Name, in order, the Google Cloud components a request passes through on a global external Application Load Balancer.
<details><summary>Answer</summary>

Forwarding rule (IP:port) → target HTTP(S) proxy → URL map → backend service (with health checks, Cloud Armor, CDN) → backends (instance groups, NEGs such as a serverless NEG, or backend buckets).
</details>

3. An agency wants one global HTTPS entry point for a web app running in two regions. What would you use on each cloud?
<details><summary>Answer</summary>

Google: a global external Application Load Balancer (one anycast IP, Premium tier) with backends in both regions. AWS: regional ALBs fronted by CloudFront (or Global Accelerator / Route 53 latency routing). Azure: Front Door Standard/Premium over the regional backends. Google's is a single global service; AWS and Azure layer a global edge over regional load balancers.
</details>

4. Why did the lab's load balancer need to be deleted promptly, even with almost no traffic?
<details><summary>Answer</summary>

Forwarding rules bill hourly whether or not traffic flows ($0.025/hour for each of the first five, about $18/month for one). Load balancers are on the "bills while idle" list along with static IPs and NAT gateways.
</details>

5. Spot the misconfiguration: "Cloud Armor blocks SQL injection on our load balancer, and the Cloud Run service is deployed with default settings."
<details><summary>Answer</summary>

Default Cloud Run ingress is `all` and the `run.app` URL is enabled, so attackers can skip the load balancer and Cloud Armor entirely (origin bypass). Restrict ingress to internal and Cloud Load Balancing and disable the default URL.
</details>

6. What does Cloud Armor preview mode do, and why use it?
<details><summary>Answer</summary>

The rule is evaluated and logged (`previewSecurityPolicy` in load balancer logs) but not enforced. It lets you find false positives before blocking real users. Preview rules still incur per-request charges.
</details>

7. Which DDoS protection do you get without paying extra on each cloud, and what's the paid tier called?
<details><summary>Answer</summary>

Google: always-on L3/L4 protection for global external Application LBs, classic ALBs, and external proxy Network LBs; paid tier Cloud Armor Enterprise (Paygo or Annual). AWS: Shield Standard; paid Shield Advanced ($3,000/month, 1-year commitment). Azure: DDoS infrastructure protection on every public IP; paid DDoS IP Protection or DDoS Network Protection.
</details>

8. What is a dangling DNS record, and why is it a security problem?
<details><summary>Answer</summary>

A DNS record (often a CNAME) still pointing at a cloud resource that's been deleted. An attacker who re-creates a resource with that name takes over your subdomain — useful for phishing, cookie theft, or getting valid TLS certificates. Fix: remove DNS records as part of decommissioning; use alias records and domain verification where available.
</details>

9. Match the ATT&CK technique: (a) a botnet sends millions of realistic HTTP search requests; (b) attackers change an agency's NS records at the registrar; (c) a UDP reflection flood.
<details><summary>Answer</summary>

(a) T1499.003 Endpoint Denial of Service: Application Exhaustion Flood. (b) T1584.002 Compromise Infrastructure: DNS Server — the DNS hijacking ED 19-01 responded to. (c) T1498.002 Network Denial of Service: Reflection Amplification.
</details>

10. What did CISA's Emergency Directive 19-01 require federal agencies to do?
<details><summary>Answer</summary>

Audit public DNS records, change passwords on DNS management accounts, add MFA to those accounts, and monitor Certificate Transparency logs for unexpected certificates. (Issued January 2019; now closed.)
</details>

11. Your WAF blocks SQL injection, but a login page is being hit with 50,000 credential-stuffing attempts an hour from many IPs. What Cloud Armor features help, and what doesn't?
<details><summary>Answer</summary>

Signature WAF rules won't catch valid-looking login attempts. Use rate limiting (per IP, or keyed on headers/fingerprints like JA4), reCAPTCHA-based bot management, and Adaptive Protection (full feature on Cloud Armor Enterprise). Back it with MFA on the application — the WAF only slows the attack.
</details>

12. Cloud DNS private zone vs public zone — what's the difference, and what homelab concept does it match?
<details><summary>Answer</summary>

A public zone is authoritative for internet queries (once delegated). A private zone answers only for the VPC networks you authorize. It's split-horizon DNS — like Pi-hole or Unbound answering internal names on your LAN while the internet sees nothing.
</details>
