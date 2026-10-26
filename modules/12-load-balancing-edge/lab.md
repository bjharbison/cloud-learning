# 12 Lab — Put a global load balancer and Cloud Armor in front of Cloud Run

**Cost:** about **$0.05–$0.15** of Free Trial credits if you finish and clean up within an hour; $0 out of pocket while credits last. What bills: one global forwarding rule (**$0.025/hour, billed even when idle**), load balancer data processing ($0.008/GiB — a few MB here), one Cloud Armor Standard policy (~$0.0068/hour) with three rules (~$0.0014/hour each) plus $0.75 per million requests, and a reserved global IP while it's attached to the forwarding rule. Cloud Run stays inside its free tier. Optional Cloud DNS zone: $0.20/month prorated hourly (well under $0.01). **Do not skip Cleanup** — an idle load balancer costs about $18/month. AWS and Azure parts are read-only listings plus one Azure DNS zone (cents ⚠️ price not confirmed). · **Time:** 75–90 min · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Deploy a Cloud Run service that **only** accepts traffic from a Google Cloud load balancer.
2. Build a **global external Application Load Balancer** piece by piece: IP → forwarding rule → proxy → URL map → backend service → serverless NEG.
3. Attach a **Cloud Armor** policy: a SQL-injection rule (preview first, then enforced) and a **rate limit**.
4. Read the load balancer request logs to see which rule fired.
5. Prove the origin can't be reached **around** the load balancer.
6. (Optional) See an authoritative DNS answer from Cloud DNS. Compare WAF/DDoS options on AWS and Azure.

## Prerequisites

- Modules 00–11 done; budget alerts active.
- Set a phone timer for 60 minutes. When it goes off, run Cleanup even if you're not finished.

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
gcloud services enable run.googleapis.com compute.googleapis.com dns.googleapis.com
```

---

## Part A — Google Cloud

### A1. A Cloud Run service with no side door (CLI)

```bash
gcloud run deploy lab12-app \
  --image=us-docker.pkg.dev/cloudrun/container/hello \
  --region=$REGION \
  --ingress=internal-and-cloud-load-balancing \
  --no-invoker-iam-check \
  --no-default-url \
  --max-instances=2 \
  --labels=lab=12
```

What each flag does:

- `--ingress=internal-and-cloud-load-balancing` — the internet can't call the service directly; only a Google Cloud load balancer (or internal traffic) can.
- `--no-invoker-iam-check` — the load balancer forwards anonymous public requests, so the IAM invoker check (module 07) is turned off. **That's only safe because ingress is locked to the load balancer.** In production you'd often add **IAP** on the backend service to require sign-in.
- `--no-default-url` — removes the `run.app` URL entirely, so there's no second front door that skips Cloud Armor.
- `--max-instances=2` — a cost ceiling.

### A2. Build the load balancer (console view, then CLI)

Console tour first (don't create anything here): **Network services → Load balancing → Create load balancer → Application Load Balancer (HTTP/S) → Public facing → Global**. Note the three sections — **Frontend configuration**, **Backend configuration**, **Routing rules** — then cancel. The CLI below creates the same parts one at a time so you can see each piece.

```bash
# 1. A reserved global anycast IP (Premium tier)
gcloud compute addresses create lab12-ip --global --ip-version=IPV4
LB_IP=$(gcloud compute addresses describe lab12-ip --global --format="value(address)"); echo $LB_IP

# 2. Serverless NEG pointing at the Cloud Run service
gcloud compute network-endpoint-groups create lab12-neg \
  --region=$REGION --network-endpoint-type=serverless --cloud-run-service=lab12-app

# 3. Backend service with request logging on (100% sampling for the lab)
gcloud compute backend-services create lab12-backend \
  --global --load-balancing-scheme=EXTERNAL_MANAGED \
  --enable-logging --logging-sample-rate=1.0
gcloud compute backend-services add-backend lab12-backend \
  --global --network-endpoint-group=lab12-neg --network-endpoint-group-region=$REGION

# 4. URL map → HTTP proxy → forwarding rule (the billable piece starts here)
gcloud compute url-maps create lab12-urlmap --default-service=lab12-backend --global
gcloud compute target-http-proxies create lab12-proxy --url-map=lab12-urlmap --global
gcloud compute forwarding-rules create lab12-fr \
  --global --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM \
  --address=lab12-ip --target-http-proxy=lab12-proxy --ports=80
```

> **HTTP only, on purpose.** HTTPS needs a certificate, and a Google-managed certificate needs a domain you control pointing at this IP. In production you'd use a target **HTTPS** proxy with a managed certificate and an SSL policy that refuses old TLS versions — and redirect port 80 to 443.

Wait 3–5 minutes for the configuration to reach Google's edge, then:

```bash
for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "%{http_code}\n" http://$LB_IP/; sleep 20; done
curl -s http://$LB_IP/ | head -20
```

**What you should see:** a few `404`s or `502`s while it propagates, then `200` and the Cloud Run "hello" page HTML. One anycast IP — the same address is served from Google edge locations worldwide.

### A3. Cloud Armor: WAF rule in preview, then enforced (CLI)

```bash
gcloud compute security-policies create lab12-armor --description="lab12 WAF + rate limit"

# SQL injection rule from the OWASP CRS 4.22-based set — PREVIEW first (log only)
gcloud compute security-policies rules create 1000 \
  --security-policy=lab12-armor \
  --expression="evaluatePreconfiguredWaf('sqli-v422-stable', {'sensitivity': 1})" \
  --action=deny-403 --preview \
  --description="SQLi (preview)"

gcloud compute backend-services update lab12-backend --global --security-policy=lab12-armor
```

Wait about a minute, then send a request that looks like SQL injection:

```bash
sleep 60
curl -s -o /dev/null -w "%{http_code}\n" "http://$LB_IP/?id=1%27%20OR%20%271%27=%271"
```

**What you should see:** `200`. Preview mode only **logs** what the rule would have done. Check:

```bash
sleep 60
gcloud logging read 'resource.type="http_load_balancer" AND jsonPayload.previewSecurityPolicy.outcome="DENY"' \
  --limit=3 --freshness=15m \
  --format="table(timestamp,httpRequest.requestUrl,jsonPayload.previewSecurityPolicy.priority,jsonPayload.previewSecurityPolicy.outcome)"
```

You should see your request, matched by rule priority `1000`, with outcome `DENY` — "would have blocked." ⚠️ If the table is empty, wait another minute (log delivery lags), or open **Logging → Logs Explorer**, choose resource **Application Load Balancer**, and expand an entry to find `previewSecurityPolicy`.

Now enforce it:

```bash
gcloud compute security-policies rules update 1000 --security-policy=lab12-armor --no-preview
sleep 60
curl -s -o /dev/null -w "%{http_code}\n" "http://$LB_IP/?id=1%27%20OR%20%271%27=%271"   # expect 403
curl -s -o /dev/null -w "%{http_code}\n" "http://$LB_IP/?id=42"                         # expect 200
```

**This is the real workflow:** new WAF rules go in preview, you read the logs for false positives, then you enforce.

### A4. Rate limiting — a basic L7 flood defense (CLI)

```bash
gcloud compute security-policies rules create 2000 \
  --security-policy=lab12-armor \
  --src-ip-ranges="*" \
  --action=throttle \
  --rate-limit-threshold-count=20 --rate-limit-threshold-interval-sec=60 \
  --conform-action=allow --exceed-action=deny-429 \
  --enforce-on-key=IP \
  --description="max 20 req/min per client IP"
sleep 60
for i in $(seq 1 35); do curl -s -o /dev/null -w "%{http_code} " http://$LB_IP/; done; echo
```

**What you should see:** roughly 20 `200`s, then `429`s ("Too Many Requests"). Your Cloud Shell's IP hit the limit; everyone else is unaffected. Rate limits on login and search endpoints are the cheapest defense against application-exhaustion floods (T1499.003) and credential stuffing. (The count isn't exact — enforcement is distributed across Google's edge.)

Look at the policy as a whole:

```bash
gcloud compute security-policies describe lab12-armor \
  --format="table(rules.priority,rules.action,rules.preview,rules.description)"
```

Note the **default rule** at priority `2147483647` (allow everything else). In production you'd decide deliberately whether the default is allow or deny.

### A5. Prove there's no way around the edge (CLI)

```bash
gcloud run services describe lab12-app --region=$REGION \
  --format="yaml(metadata.annotations,status.url)"
```

**What you should see:** ingress annotation `internal-and-cloud-load-balancing`, and no usable `run.app` URL (the default URL is disabled). With both settings, the only public path is the load balancer — and Cloud Armor sits on it. This is the **origin bypass** fix from the README's security list. On AWS the equivalent is CloudFront **Origin Access Control** or ALB-only security groups; on Azure, Front Door with Private Link origins or access restrictions on the backend.

### A6. (Optional) An authoritative DNS answer from Cloud DNS (CLI)

Cloud DNS will host a zone for a name you don't own; it just won't be reachable from the public DNS tree until the domain's registrar delegates to it. That's fine for seeing how authoritative DNS works.

```bash
gcloud dns managed-zones create lab12-zone \
  --dns-name="lab12-$RANDOM.example.com." --visibility=public \
  --description="lab12 test zone" --labels=lab=12
ZONE_DNS=$(gcloud dns managed-zones describe lab12-zone --format="value(dnsName)")
gcloud dns record-sets create "app.$ZONE_DNS" --zone=lab12-zone --type=A --ttl=300 --rrdatas=$LB_IP
NS=$(gcloud dns managed-zones describe lab12-zone --format="value(nameServers[0])"); echo $NS
dig +short @$NS "app.$ZONE_DNS" A
dig +short "app.$ZONE_DNS" A        # via the normal resolver — expect nothing
```

**What you should see:** asking Google's assigned name server directly returns your load balancer IP; asking a normal resolver returns nothing, because no registrar delegates that name to Google. Delegation (NS records at the registrar) is the step attackers target in DNS hijacking — and the step ED 19-01 told agencies to audit. ⚠️ If zone creation is refused for the `example.com` subdomain, skip A6; it's optional.

---

## Part B — AWS (optional, read-only, $0)

CloudShell, `us-east-1`.

```bash
aws wafv2 list-available-managed-rule-groups --scope REGIONAL \
  --query "ManagedRuleGroups[?VendorName=='AWS'].Name" --output table
aws shield describe-subscription 2>&1 | head -3
aws elbv2 describe-ssl-policies --query "SslPolicies[].Name" --output text | tr '\t' '\n' | head -10
```

**What you should see:** AWS managed rule groups (look for `AWSManagedRulesCommonRuleSet`, `AWSManagedRulesSQLiRuleSet`, `AWSManagedRulesKnownBadInputsRuleSet`, and Bot Control); a `ResourceNotFoundException` from Shield — meaning you have **Shield Standard** (free, automatic) but not Shield Advanced; and the TLS policies an ALB/NLB can enforce. Nothing was created.

## Part C — Azure (optional, cents)

Azure Cloud Shell (Bash).

```bash
az group create --name rg-lab12 --location eastus --tags lab=12
az network dns zone create -g rg-lab12 -n "lab12-$RANDOM.example.com" --tags lab=12
az network dns zone list -g rg-lab12 --query "[].{zone:name,ns:nameServers}" -o json
```

**What you should see:** a public zone and its four assigned Azure DNS name servers — the same delegation model as Cloud DNS and Route 53. (Azure's always-on DDoS infrastructure protection already covers every public IP you create; you'd see paid **DDoS Protection plans** under **DDoS protection plans** in the portal, but don't create one — they bill monthly.)

---

## Verify it worked

| Check | Expected |
|---|---|
| `curl http://$LB_IP/` | 200, Cloud Run hello page |
| SQLi in preview | 200, plus a log entry with `previewSecurityPolicy.outcome = DENY` |
| SQLi enforced | 403; benign request still 200 |
| Rate limit | ~20 × 200, then 429s |
| Cloud Run | ingress `internal-and-cloud-load-balancing`, no `run.app` URL |
| (A6) `dig @NS` | LB IP returned by Cloud DNS |
| (B) Shield | Not subscribed → Standard only |

## What to notice (reflection questions)

1. Count the separate resources you created for one load balancer. Which one actually costs money while idle — and why does that matter for cleanup?
2. Why must `--no-invoker-iam-check` always travel together with restricted ingress and a disabled default URL?
3. What did preview mode let you learn before you blocked anything? What would you look for in a week of preview logs on a real agency site?
4. The rate limit keyed on client IP. How would an attacker using a residential-proxy botnet change that picture, and what Cloud Armor features (Adaptive Protection, reCAPTCHA bot management, JA4 keys) would you reach for?
5. Map each piece you built to its AWS and Azure equivalent.

## Cleanup

**Google Cloud** (order matters — each piece depends on the next):

```bash
gcloud compute forwarding-rules delete lab12-fr --global --quiet
gcloud compute target-http-proxies delete lab12-proxy --global --quiet
gcloud compute url-maps delete lab12-urlmap --global --quiet
gcloud compute backend-services delete lab12-backend --global --quiet
gcloud compute security-policies delete lab12-armor --quiet
gcloud compute network-endpoint-groups delete lab12-neg --region=$REGION --quiet
gcloud compute addresses delete lab12-ip --global --quiet
gcloud run services delete lab12-app --region=$REGION --quiet
```

If you did A6:

```bash
gcloud dns record-sets delete "app.$ZONE_DNS" --zone=lab12-zone --type=A
gcloud dns managed-zones delete lab12-zone --quiet
```

(If Cloud Shell restarted and `$ZONE_DNS` is empty, run `gcloud dns record-sets list --zone=lab12-zone`, delete the `A` record by name, then the zone.)

Confirm:

```bash
gcloud compute forwarding-rules list --global              # Listed 0 items (or none named lab12)
gcloud compute addresses list --global --filter="name=lab12-ip"   # Listed 0 items
gcloud compute backend-services list --global --filter="name=lab12-backend"
gcloud compute security-policies list --filter="name=lab12-armor"
gcloud compute network-endpoint-groups list --filter="name=lab12-neg"
gcloud run services list --region=$REGION --filter="metadata.name=lab12-app"
gcloud dns managed-zones list --filter="name=lab12-zone"
```

Every command should return no `lab12` items.

**AWS:** nothing was created.

**Azure**

```bash
az group delete --name rg-lab12 --yes
az group list --query "[?name=='rg-lab12']" -o table   # expect empty
```

**Final check — nothing billable remains:** no forwarding rule, reserved IP, backend service, Cloud Armor policy, NEG, Cloud Run service, or DNS zone named `lab12` on Google; no `rg-lab12` on Azure. Tomorrow, open Google **Billing → Reports**, filter to **Networking** and **Cloud Armor** services: expect a few cents at most, and nothing accruing after today.

## Write-up prompt

> On [date] I built a Google Cloud global external Application Load Balancer from its components (reserved anycast IP, forwarding rule, HTTP proxy, URL map, backend service, serverless NEG) in front of a Cloud Run service whose ingress was restricted to Cloud Load Balancing and whose default URL was disabled, so the load balancer was the only path in. I attached a Cloud Armor security policy, ran an OWASP CRS-based SQL-injection rule in preview mode and confirmed the would-be denial in load balancer logs before enforcing it, and added a per-client-IP rate limit that returned HTTP 429 above 20 requests per minute. [Optional: I created a Cloud DNS public zone and queried its authoritative name server directly.] [Optional: I reviewed AWS WAF managed rule groups and Shield status, and created an Azure DNS zone.] I deleted all resources afterward.
