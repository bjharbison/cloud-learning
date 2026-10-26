# 12 — Load balancing, DNS, CDN, WAF, and DDoS protection

> **In one sentence:** you'll be able to pick the right load balancer on each cloud, explain how DNS, CDN, WAF, and DDoS protection stack up at the edge, and tell an agency which of those layers the provider runs for free and which ones they must configure and pay for.

**Prereqs:** modules 00–11 (module 07 for Cloud Run; modules 10–11 for VPCs and firewalls) · **Time:** ~3.5 hours incl. lab · **Phase:** 3

## Learning objectives

- Explain **Layer 4 vs Layer 7**, **proxy vs passthrough**, and **global vs regional** load balancing, and choose among Google's Application and Network Load Balancers, AWS ELB, and Azure's four options.
- Describe the parts of a Google load balancer: **forwarding rule → target proxy → URL map → backend service → backends**.
- Explain authoritative vs private DNS on each cloud, and why DNS is both critical infrastructure and an attack surface.
- Describe what a **CDN** does and where it sits.
- Compare **Cloud Armor**, **AWS WAF + Shield**, and **Azure WAF + DDoS Protection**: what's free, what's paid, what each actually stops.

## Why this matters for the target roles

- **Customer engineer / architect:** every public-facing agency app — benefits portals, grant systems, public data sites — sits behind this stack. "Which load balancer?" is a standard architecture question, and Google's global anycast front end is a real differentiator.
- **Cloud security:** the edge is where most internet attacks land first. WAF and DDoS policy are customer-configured.
- **CTI:** DDoS (hacktivist and state-aligned), DNS hijacking, subdomain takeover, and web-app exploitation all show up in the logs this module introduces.

---

## Concepts

### Why load balance at all

**Plain version:** a **load balancer** is one stable front door that spreads requests across many back-end servers, skips the unhealthy ones, and lets you add or remove servers without users noticing.

You met the need in module 10: cloud VPCs have no Layer 2, so VRRP/keepalived failover doesn't work. The cloud-native answer is a managed load balancer plus **health checks**.

**Homelab bridge:** if you've put HAProxy or Traefik in front of Docker containers, you've run a Layer 7 reverse proxy. A cloud load balancer is that, run by the provider, with no VM to patch — and on Google, spread across its global edge.

### Three questions that pick the load balancer

1. **Layer 4 or Layer 7?** **L4** sees IPs, ports, TCP/UDP. **L7** understands HTTP(S): paths, headers, cookies, host names. You need L7 for path-based routing, WAF rules, or a CDN.
2. **Proxy or passthrough?** A **proxy** load balancer terminates the client connection and opens a new one to the backend (the backend sees the proxy's IP; the original client IP goes in a header). A **passthrough** load balancer forwards packets as-is — the backend sees the **real client IP** and replies directly.
3. **Global or regional? External or internal?** Global means one anycast IP serving users from the nearest edge; regional means one region. External faces the internet; internal serves only your VPC (and connected networks).

### Google Cloud Load Balancing

Google groups its load balancers into two families:

| Family | Layer | Mode | Options |
|---|---|---|---|
| **Application Load Balancer** | L7 (HTTP/HTTPS) | Proxy | Global external · regional external · classic · regional internal · cross-region internal |
| **Network Load Balancer** | L4 | **Proxy** (TCP, optional SSL offload) | Global external · regional external · classic · regional internal · cross-region internal |
| | L4 | **Passthrough** (TCP/UDP and more; preserves client IP) | Regional external · regional internal (a global external passthrough option is in Preview) |

**Network tiers matter:** global external load balancers need the **Premium** network tier (traffic rides Google's backbone from the nearest edge). Some regional options also run on **Standard** tier.

**The building blocks** (you'll create each in the lab):

```
 client ─► forwarding rule (IP:port) ─► target proxy ─► URL map (host/path rules)
                                                            │
                                                  backend service (+ health check,
                                                  + Cloud Armor policy, + CDN)
                                                            │
                                 backends: instance groups │ NEGs (zonal, internet,
                                 hybrid, serverless → Cloud Run) │ backend buckets
```

- **Forwarding rule** — the frontend IP and port.
- **Target proxy** — terminates HTTP/HTTPS (holds the TLS certificate for HTTPS).
- **URL map** — routing rules: `/api/*` to one backend, `/static/*` to a bucket.
- **Backend service** — the pool definition, with health checks and attached policies.
- **NEG (network endpoint group)** — a list of endpoints; a **serverless NEG** points at a Cloud Run service, so you can put a global load balancer, Cloud Armor, and a custom domain in front of serverless.

**Cost reality:** forwarding rules bill **hourly whether or not traffic flows** — $0.025/hour for each of the first five (about $18/month for one), plus $0.008 per GiB processed. That's why the lab keeps the load balancer alive for under an hour.

### AWS Elastic Load Balancing

| Type | Layer | Use |
|---|---|---|
| **Application Load Balancer (ALB)** | L7 | HTTP/HTTPS routing, WAF attachment |
| **Network Load Balancer (NLB)** | L4 | TCP/UDP/TLS, static IPs, very high throughput |
| **Gateway Load Balancer (GWLB)** | L3 | Inserting third-party firewalls/IDS appliances transparently |
| **Classic Load Balancer** | L4/L7 | Legacy; AWS recommends migrating to ALB or NLB |

All are **regional**. For a global entry point, AWS pairs them with **CloudFront** (CDN), **Global Accelerator** (anycast IPs), or Route 53 DNS routing. Pricing is hourly plus capacity units (LCUs), billed per full or partial hour.

### Azure's four options

| Service | Layer | Scope |
|---|---|---|
| **Azure Load Balancer** (Standard; Basic SKU retired Sept 30, 2025) | L4 | Regional (plus a cross-region tier) |
| **Application Gateway v2** (v1 retired Apr 28, 2026) | L7, optional WAF | Regional |
| **Azure Front Door** Standard/Premium (classic retires Mar 31, 2027) | L7 + CDN + WAF | Global |
| **Traffic Manager** | DNS-based | Global |

Microsoft's own decision tree boils down to: global HTTP → Front Door; regional HTTP → Application Gateway; non-HTTP → Load Balancer; DNS-level failover → Traffic Manager.

**The real difference to say out loud:** Google's global external Application Load Balancer is *one* service with *one* anycast IP worldwide. AWS and Azure reach global by layering a global edge (CloudFront / Front Door) over regional load balancers. Both work; the operational shape differs.

### DNS: the phone book is critical infrastructure

**Plain version:** DNS turns names into IP addresses. An **authoritative** server holds the true answers for a domain; a **resolver** looks things up on a client's behalf.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Authoritative public DNS | **Cloud DNS** public zones | **Route 53** hosted zones | **Azure DNS** public zones |
| Private, VPC-only names | Cloud DNS **private zones** | Route 53 private hosted zones | Azure **Private DNS** zones |
| Hybrid resolution with on-prem | Forwarding zones, peering zones, **inbound/outbound server policies** | **Route 53 VPC Resolver** endpoints (renamed from "Route 53 Resolver") | **DNS Private Resolver** |
| DNS-layer filtering | Response policies; **DNS Armor** threat detection ⚠️ (GA status not confirmed) | **Route 53 Resolver DNS Firewall** | DNS security policy ⚠️ |
| DNSSEC signing | Managed DNSSEC | Supported (key in KMS) | Public zones ⚠️ (GA status not confirmed) |
| Traffic-steering policies | Geo, weighted, failover routing policies | Latency, weighted, failover, geolocation, geoproximity, IP-based, multivalue | Traffic Manager |
| Price (zones) | $0.20/zone/month (first 25), prorated | $0.50/hosted zone/month, not prorated | Per zone per month ⚠️ |

Google publishes a **100% availability** service level objective for Cloud DNS answering from at least one of its authoritative name servers.

**DNSSEC** signs DNS records so resolvers can detect forged answers. It provides authenticity, not secrecy.

**Bridge to your homelab:** you've run split-horizon DNS — Pi-hole or Unbound answering `grafana.home.lan` inside while the internet sees nothing. Private zones are exactly that, attached to specific VPCs.

### CDN: cache it close to the user

A **CDN** stores copies of static content (images, scripts, video, downloads) at edge locations near users. Benefits: speed, lower origin load, and absorbing traffic spikes.

- **Google:** **Cloud CDN** is a checkbox on a backend service or backend bucket behind a global external Application Load Balancer. **Media CDN** targets video streaming and large downloads.
- **AWS:** **CloudFront**. Always-free allotment of 1 TB transfer and 10 million requests a month on pay-as-you-go; since November 2025 there are also flat-rate plans (including a $0 Free plan) that bundle WAF and DDoS protection.
- **Azure:** **Front Door** is the CDN. Azure CDN from Edgio retired Jan 15, 2025; Azure CDN Standard from Microsoft (classic) retires Sept 30, 2027.

All three support **signed URLs/cookies** for content that shouldn't be public (module 08's bearer-token warning applies).

### WAF: Layer 7 rules in front of the app

A **web application firewall (WAF)** inspects HTTP requests and blocks known attack patterns — SQL injection, cross-site scripting, scanners — plus custom rules (geo, IP, header) and **rate limiting**.

Most managed WAF rule sets derive from the **OWASP ModSecurity Core Rule Set (CRS)**:

- **Google Cloud Armor** — security policies attached to backend services (or **edge security policies** that run before the CDN cache). Preconfigured WAF rules based on CRS 4.22 (recommended, e.g., `sqli-v422-stable`) and 3.3. Rules can run in **preview mode** — logged, not enforced. Inspects the first 64 KB of a request body.
- **AWS WAF** — **web ACLs** with your rules and AWS or vendor **managed rule groups**; attaches to ALB, CloudFront, API Gateway, and others. **Bot Control** is an add-on.
- **Azure WAF** — policies on Application Gateway or Front Door. **Default Rule Set 2.2** (based on CRS 3.3.4) recommended for new policies; **Bot Manager** rule sets.

**Bridge to your OT background:** a WAF is deep packet inspection for one protocol, like an industrial firewall that understands Modbus function codes. It's only as good as its rules and tuning — and like OT DPI, teams run it in detect-only mode far too long.

### DDoS protection: what's free, what's insurance

| | Always on, no charge | Paid tier | What the paid tier adds |
|---|---|---|---|
| **Google** | L3/L4 protection on global external Application LBs, classic ALBs, and external proxy Network LBs | **Cloud Armor Enterprise** (Paygo ~$200/month per project; Annual ~$3,000/month) | Full **Adaptive Protection** (ML-detected L7 attacks with suggested rules), threat-intel lists, DDoS response support and **bill protection** (Annual) |
| **AWS** | **Shield Standard** — automatic L3/L4 | **Shield Advanced** — $3,000/month per payer account, 1-year commitment | Shield Response Team (needs Business/Enterprise Support), cost protection, WAF fees waived on protected resources |
| **Azure** | **DDoS infrastructure protection** on every public IP | **DDoS IP Protection** (per IP) or **Network Protection** (covers 100 IPs) ⚠️ prices not confirmed | Rapid Response, cost protection, WAF discount (Network Protection) |

**Proxy load balancers absorb a lot by design:** a SYN flood against a Google global proxy load balancer hits Google's edge, not your VMs. Layer 7 floods — real-looking HTTP requests — are where WAF rate limiting and Adaptive Protection come in.

**Scale for perspective:** in August–September 2023 Google reported mitigating an HTTP/2 "Rapid Reset" attack (CVE-2023-44487) peaking at **398 million requests per second**.

> **Shared responsibility — say it plainly:** the provider runs the load balancers, the global edge, and baseline DDoS protection. **Which ports listen, which backends are exposed, TLS settings, WAF rules and their tuning, rate limits, DNS records, and whether the origin can be reached around the protection are the customer's.**

---

## Text diagram — a hardened public app on Google Cloud

```
 user ─► DNS (Cloud DNS, DNSSEC) ─► anycast IP 34.x.x.x (Premium tier, global)
          │
          ▼  Google edge (always-on L3/L4 DDoS absorption)
   Edge security policy (Cloud Armor) ─► Cloud CDN cache ─► hit? serve from edge
          │ miss
          ▼
   Global external Application LB: target HTTPS proxy (managed cert) ─► URL map
          ├─ /static/* ─► backend bucket (Cloud Storage)
          └─ /*        ─► backend service + Cloud Armor policy
                              (WAF sqli/xss · rate limit · geo rules · preview first)
                              └─ serverless NEG ─► Cloud Run
                                  ingress = internal + Cloud Load Balancing
                                  default run.app URL disabled  ◄── no bypass
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud | AWS | Azure | Notable difference |
|---|---|---|---|---|
| Global L7 load balancer | Global external **Application LB** (one anycast IP) | CloudFront / Global Accelerator in front of regional ALBs | **Front Door** Standard/Premium | Google's is a single global service |
| Regional L7 | Regional external / internal Application LB | **ALB** | **Application Gateway v2** | |
| L4 | Network LB (proxy or passthrough) | **NLB** | **Azure Load Balancer** | Passthrough preserves client IP |
| Appliance insertion | (no direct equivalent; Cloud NGFW Enterprise endpoints, module 11) | **Gateway LB** | Gateway Load Balancer SKU | |
| DNS | Cloud DNS (100% SLO) | Route 53 | Azure DNS + Traffic Manager | Route 53 zones aren't prorated |
| CDN | Cloud CDN, Media CDN | CloudFront (incl. flat-rate plans) | Front Door | |
| WAF | Cloud Armor policies (CRS 4.22/3.3) | AWS WAF web ACLs + managed rule groups | Azure WAF (DRS 2.2 = CRS 3.3.4) | |
| Free DDoS baseline | Always-on L3/L4 for global/external proxy LBs | Shield Standard | DDoS infrastructure protection | |
| Paid DDoS tier | Cloud Armor Enterprise | Shield Advanced ($3,000/mo) | DDoS Network / IP Protection | All three offer cost protection on the top tier |

## Administer and monitor it

- **Health checks** decide what gets traffic. Their probes come from published provider ranges — your firewall must allow them (module 11), or every backend looks dead.
- **Request logs:** Google load balancer logging (per backend service, sampling rate configurable) records each request and the **Cloud Armor rule** that matched; ALB access logs to S3; Application Gateway/Front Door diagnostic logs to Log Analytics.
- **Certificates:** managed certificates (Google-managed, AWS Certificate Manager, Front Door managed) renew automatically — if DNS still points at the load balancer.
- **DNS query logs:** Cloud DNS logging (VPC and public zones), Route 53 query logs, Azure DNS diagnostics. High-value for hunting.
- **Cost watch:** idle forwarding rules, ALBs, and Application Gateways all bill hourly. Tag them (module 04).

## Security angle

1. **Origin bypass.** WAF on the load balancer, but the backend still answers directly — a VM with a public IP, a Cloud Run `run.app` URL, an S3 origin without Origin Access Control. Lock the origin to the load balancer only.
2. **WAF stuck in preview/detection mode** forever, or default sensitivity never tuned.
3. **No rate limiting** on login and search endpoints — the cheap L7 DDoS and credential-stuffing targets.
4. **Health-check ranges opened too broadly** — "allow 0.0.0.0/0 so health checks pass."
5. **Dangling DNS** — a CNAME pointing at a deleted cloud resource that an attacker can re-register (subdomain takeover).
6. **DNS registrar/admin accounts without MFA** — the root of DNS hijacking.
7. **Weak TLS policy** — old protocol versions allowed on HTTPS frontends.

## Threat intel angle

- **T1498 Network Denial of Service** (T1498.001 Direct Network Flood, .002 Reflection Amplification) — absorbed mostly by the provider edge.
- **T1499 Endpoint Denial of Service**, especially **.002 Service Exhaustion Flood** and **.003 Application Exhaustion Flood** — the L7 floods WAF rate limits and Adaptive Protection target. Hacktivist DDoS against government sites is a recurring pattern; CISA, FBI, and MS-ISAC's joint guide *Understanding and Responding to Distributed Denial-of-Service Attacks* (updated March 2024) is the public reference.
- **T1190 Exploit Public-Facing Application** and **T1595 Active Scanning** — what WAF logs actually show you day to day.
- **T1584.002 Compromise Infrastructure: DNS Server** and **T1583.001 Acquire Infrastructure: Domains** — DNS hijacking and look-alike domains. CISA's **Emergency Directive 19-01, "Mitigate DNS Infrastructure Tampering"** (January 2019, now closed) ordered federal agencies to audit DNS records, change DNS account passwords, add MFA, and monitor Certificate Transparency logs.
- **Subdomain takeover** via dangling DNS — Microsoft documents the pattern and mitigations (alias records, domain verification, cleanup on decommission).
- **T1090.004 Proxy: Domain Fronting** — adversaries hiding C2 behind CDN domains; a reminder that "traffic to a big CDN" isn't automatically benign.

**Detection ideas:** sudden spikes in requests per client IP or per **JA3/JA4 fingerprint** (a hash of how a client negotiates TLS — it identifies the client software even when IPs rotate); Cloud Armor deny counts by rule; DNS record changes outside change windows; new CNAMEs to provider domains; Certificate Transparency entries for your domains that you didn't request.

**Bridge to your CTI work:** WAF logs are a running census of who's scanning you and with what. Correlate rule hits with threat-actor tooling the way you'd correlate SIGINT externals — the noise floor matters, and the anomaly is the story.

## Public sector notes

- **Public-facing agency services** are the classic hacktivist DDoS target; a provider's always-on edge protection plus WAF rate limiting is a strong, explainable story.
- **DNS discipline** is policy-driven for agencies (ED 19-01's lessons; `.gov` domain management through CISA ⚠️ details not covered here).
- **Authorization scope:** confirm each edge service is inside your required FedRAMP/IL boundary before designing with it — Google's CDN comparison page lists FedRAMP Moderate for Cloud CDN; scope for the other edge services wasn't verified this run (module 26).

## Key takeaways

- Pick a load balancer by layer (L4/L7), mode (proxy/passthrough), and scope (global/regional, external/internal).
- Google's global external Application Load Balancer gives one anycast IP worldwide; AWS and Azure get global reach by layering CloudFront/Front Door over regional load balancers.
- DNS is critical infrastructure: private zones for internal names, DNSSEC for authenticity, MFA on DNS accounts, and cleanup of dangling records.
- WAFs (Cloud Armor, AWS WAF, Azure WAF) run OWASP CRS-based rules plus rate limiting; start in preview, then enforce.
- Baseline L3/L4 DDoS protection is free on all three; paid tiers add response teams and cost protection.
- Lock origins so nobody can go around the edge. Ports, WAF rules, DNS records, and origin exposure are **always the customer's**.

## Sources

- [Google Cloud — Cloud Load Balancing overview](https://docs.cloud.google.com/load-balancing/docs/load-balancing-overview) and [pricing](https://cloud.google.com/load-balancing/pricing)
- [Google Cloud — Set up a global external Application Load Balancer with Cloud Run](https://docs.cloud.google.com/load-balancing/docs/https/setup-global-ext-https-serverless)
- [Google Cloud — Cloud DNS overview](https://docs.cloud.google.com/dns/docs/overview), [pricing](https://cloud.google.com/dns/pricing), [SLA](https://cloud.google.com/dns/sla), [DNS threat detection](https://docs.cloud.google.com/dns/docs/threat-detection)
- [Google Cloud — Cloud CDN overview](https://docs.cloud.google.com/cdn/docs/overview) and [Choose a CDN product](https://docs.cloud.google.com/cdn/docs/choose-cdn-product)
- [Google Cloud Armor — overview](https://docs.cloud.google.com/armor/docs/cloud-armor-overview), [security policies](https://docs.cloud.google.com/armor/docs/security-policy-overview), [preconfigured WAF rules](https://docs.cloud.google.com/armor/docs/waf-rules), [Enterprise](https://docs.cloud.google.com/armor/docs/armor-enterprise-overview), [pricing](https://cloud.google.com/armor/pricing)
- [Google Cloud blog — mitigating a 398 million rps DDoS attack](https://cloud.google.com/blog/products/identity-security/google-cloud-mitigated-largest-ddos-attack-peaking-above-398-million-rps/)
- [AWS — Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) and [Classic Load Balancer migration](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/migrate-classic-load-balancer.html)
- [AWS — Route 53 routing policies](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html), [Route 53 VPC Resolver](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html), [DNS Firewall](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-overview.html), [pricing](https://aws.amazon.com/route53/pricing/)
- [AWS — CloudFront FAQs](https://aws.amazon.com/cloudfront/faqs/) and [flat-rate pricing plans](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/flat-rate-pricing-plan.html)
- [AWS — WAF pricing](https://aws.amazon.com/waf/pricing/) and [Shield pricing](https://aws.amazon.com/shield/pricing/)
- [Microsoft — Load Balancer SKUs](https://learn.microsoft.com/en-us/azure/load-balancer/skus), [Application Gateway v1 retirement](https://learn.microsoft.com/en-us/azure/application-gateway/v1-retirement), [Front Door (classic) retirement FAQ](https://learn.microsoft.com/en-us/azure/frontdoor/classic-retirement-faq), [Azure CDN overview](https://learn.microsoft.com/en-us/azure/cdn/cdn-overview), [Traffic Manager](https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-overview)
- [Microsoft — Azure DNS DNSSEC](https://learn.microsoft.com/en-us/azure/dns/dnssec)
- [Microsoft — Azure WAF DRS rule groups](https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules)
- [Microsoft — DDoS Protection SKU comparison](https://learn.microsoft.com/en-us/azure/ddos-protection/ddos-protection-sku-comparison)
- [Microsoft — Prevent dangling DNS entries and avoid subdomain takeover](https://learn.microsoft.com/en-us/azure/security/fundamentals/subdomain-takeover)
- [CISA — ED 19-01 Mitigate DNS Infrastructure Tampering (closed)](https://www.cisa.gov/news-events/directives/ed-19-01-mitigate-dns-infrastructure-tampering-closed) and [joint DDoS guidance update (Mar 2024)](https://www.cisa.gov/news-events/alerts/2024/03/21/cisa-fbi-and-ms-isac-release-update-joint-guidance-distributed-denial-service-techniques)
- [MITRE ATT&CK — T1498](https://attack.mitre.org/techniques/T1498/), [T1499](https://attack.mitre.org/techniques/T1499/), [T1190](https://attack.mitre.org/techniques/T1190/), [T1584.002](https://attack.mitre.org/techniques/T1584/002/), [T1583.001](https://attack.mitre.org/techniques/T1583/001/), [T1090.004](https://attack.mitre.org/techniques/T1090/004/), [T1595](https://attack.mitre.org/techniques/T1595/)

Verified: 2026-10-26
