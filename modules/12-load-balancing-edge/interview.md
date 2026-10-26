# 12 Interview Prep — Load balancing, DNS, CDN, WAF, and DDoS protection

## Likely questions

### Q1. "How would you choose a load balancer on Google Cloud?"

**Answer outline:**
- Three questions: L7 or L4? Proxy or passthrough? Global or regional, external or internal?
- HTTP(S) apps → Application Load Balancer (global external for internet users worldwide; regional or internal for regional/private apps).
- Non-HTTP TCP → proxy Network LB; need the client IP, UDP, or other protocols → passthrough Network LB.
- Then: backends (instance groups, NEGs, serverless NEG for Cloud Run, buckets), health checks, Cloud Armor, CDN.

**Strong signal:** naming the client-IP trade-off and the Premium-tier requirement for global.
**Avoid:** "just use the HTTP one."

### Q2. "How does Google's load balancing differ from AWS and Azure?"

**Answer outline:**
- Google's global external Application Load Balancer: one anycast IP, served from Google's edge, backends in many regions — one service.
- AWS: ALB/NLB/GWLB are regional; global comes from CloudFront, Global Accelerator, or Route 53 routing.
- Azure: Front Door (global L7 + CDN + WAF), Application Gateway (regional L7), Load Balancer (L4), Traffic Manager (DNS).
- Trade-off: simpler global config vs familiar regional building blocks; both work.

### Q3. "An agency's public benefits site was knocked offline by a DDoS. What would you design?"

**Answer outline:**
- Put the site behind a proxy load balancer at the provider edge — L3/L4 floods hit the provider's edge, not the app (Google always-on protection, Shield Standard, Azure infrastructure protection).
- L7: Cloud Armor rate limits on expensive endpoints (search, login), WAF rules, bot management; Adaptive Protection or a paid tier (Cloud Armor Enterprise / Shield Advanced / Azure DDoS Network Protection) if the risk justifies it — those add response teams and cost protection.
- CDN to absorb static content; lock the origin so it can't be hit directly.
- Logging and a runbook; CISA/FBI/MS-ISAC DDoS guidance for the response side.

**Strong signal:** "origin bypass" and "L7 floods need different controls than L3/L4."
**Avoid:** "the cloud handles DDoS for you."

### Q4. "What are the security risks in DNS for a cloud customer?"

**Answer outline:**
- Registrar and DNS-admin account takeover → hijacking (T1584.002); CISA ED 19-01's actions: audit records, rotate passwords, MFA, watch Certificate Transparency.
- Dangling records → subdomain takeover.
- DNSSEC for authenticity of answers.
- Private zones for internal names; DNS query logs as hunting data; DNS-layer filtering (Route 53 Resolver DNS Firewall, Cloud DNS response policies).

### Q5. "How do you roll out a WAF without breaking the application?"

**Answer outline:**
- Start with managed rule sets (OWASP CRS-based) in preview/detection mode.
- Review logs for false positives; tune sensitivity or add exclusions.
- Enforce rule by rule; keep monitoring; add rate limits and custom rules for the app's real abuse cases.
- Remember a WAF doesn't fix vulnerable code — it buys time.

## 60-second executive explanation

"Every public website we run has a front door. In the cloud, that front door is a managed service run by the provider at the edge of its global network — so when someone tries to flood us with junk traffic, it hits the provider's enormous capacity first, not our servers. Behind that door we add a filter that recognizes common attacks and limits how fast any one source can knock. The provider gives us basic flood protection automatically; the filtering rules, what's exposed, and making sure nobody can sneak around the front door are our job. We can also buy premium protection that comes with an expert response team and protection against surprise bills from an attack."

## Whiteboard prompt

Draw a public grant-application portal on Google Cloud: Cloud DNS (DNSSEC) → global external Application Load Balancer with HTTPS and a managed certificate → Cloud CDN for static files from a bucket → Cloud Armor (WAF rules, rate limit on `/login` and `/search`, geo rule if required) → serverless NEG → Cloud Run with restricted ingress and no default URL. Then draw the same design on AWS (Route 53 → CloudFront + AWS WAF → ALB) and Azure (Azure DNS → Front Door Premium with WAF → backend). Mark the free DDoS baseline and where logs go.

## What you can honestly claim

- **After reading + quiz:** "I've studied cloud load balancing, DNS, CDN, WAF, and DDoS protection across Google Cloud, AWS, and Azure, and can explain how to choose a load balancer and layer edge protections for a public-facing service."
- **After completing the lab:** "In a personal lab I built a Google Cloud global external Application Load Balancer in front of Cloud Run, restricted the service so the load balancer was the only path in, and configured Cloud Armor WAF and rate-limiting rules, validating them in preview mode through load balancer logs before enforcing." Add the DNS, AWS, or Azure sentences only if you did those parts.
- **Still requires (cert / production experience / clearance):** operating production load balancers, tuning a WAF against live traffic, or responding to a real DDoS. Don't claim "DDoS mitigation experience" from this lab. HTTPS with managed certificates on a real domain is a natural next step you could do yourself. The Google Professional Cloud Network Engineer ⚠️ (not covered in `reference/certifications.md`) and Professional Cloud Security Engineer exams test this material.
