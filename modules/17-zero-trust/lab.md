# 17 Lab — Put an identity-aware proxy in front of an app (no VPN, no public access)

**Cost:** $0. Core IAP for Google Cloud resources is free; the Cloud Run service uses Google's prebuilt sample image (no build) and stays far inside Cloud Run's monthly free tier; a few IAP Data Access log entries are well under Cloud Logging's 50 GiB/month free allotment. AWS and Azure parts are **read-only tours** — AWS Verified Access bills about $0.27 per app-hour with no free tier, and Entra Private Access / Conditional Access need paid Entra licenses, so you won't create either. · **Time:** 60–75 min · **Clouds:** GCP (required), AWS and Azure (optional, read-only)

## Goal

1. Deploy a private Cloud Run service and put **Identity-Aware Proxy** directly in front of it.
2. Grant yourself access with a **time-limited IAM Condition** — a per-request, context-aware decision.
3. See an anonymous request turned away and your signed-in request allowed.
4. Turn on IAP **Data Access audit logs** and read the grant/deny decisions.
5. Revoke access and watch the decision change — no network change involved.
6. Map AWS Verified Access and Microsoft's Conditional Access + Global Secure Access onto the same NIST roles.

## Prerequisites

- Modules 00–16 done; budget alerts active.
- Cloud Shell, lab project selected. You're signed in to the console with the same Google account.
- Optional: a second Google account (e.g., a spare Gmail) to test a denied user. Use a private/incognito browser window for it.

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
ME=$(gcloud config get-value account)
REGION=us-central1
SVC=lab17-app
gcloud services enable run.googleapis.com iap.googleapis.com
```

---

## Part A — Google Cloud

### A1. A private Cloud Run service (CLI)

```bash
gcloud run deploy $SVC --image=us-docker.pkg.dev/cloudrun/container/hello \
  --region=$REGION --no-allow-unauthenticated --max-instances=1 --labels=lab=17
URL=$(gcloud run services describe $SVC --region=$REGION --format="value(status.url)"); echo $URL
curl -s -o /dev/null -w "%{http_code}\n" $URL
```

**What you should see:** `403` — module 07's invoker IAM check. The service is private, but only to *callers who can present a Google ID token*; browsers can't do that on their own. IAP adds the human sign-in flow, per-request policy, and decision logging.

### A2. Turn on IAP (console first — recommended for a project with no organization)

Google recommends doing the **first** IAP enablement in a project without an organization from the console, because it walks you through the OAuth setup.

1. Console → **Cloud Run → Services → `lab17-app` → Security** tab.
2. Under authentication, keep **Require authentication** and select **Identity-Aware Proxy (IAP)**.
3. If prompted to configure OAuth (likely on a personal project): follow **Configure in IAP → Configure consent screen**. Choose audience **External**, fill in an app name (`lab17`) and your email, and choose **Auto generate credentials**. (An **Internal** audience only works for users inside an organization.)
4. **View diff & redeploy → Deploy changes.**

Then check from Cloud Shell:

```bash
gcloud run services describe $SVC --region=$REGION | grep -i iap
gcloud run services get-iam-policy $SVC --region=$REGION
```

**What you should see:** `Iap Enabled: true`, and the IAP service agent `service-PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com` holding `roles/run.invoker`. IAP — not the user — is now the only caller Cloud Run trusts.

**CLI equivalent** (for later services in the same project, once OAuth is configured):

```bash
# gcloud run services update SERVICE --region=REGION --iap
# gcloud run services add-iam-policy-binding SERVICE --region=REGION \
#   --member=serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com --role=roles/run.invoker
```

If enabling fails with "Setting IAM permissions failed," Google documents re-enabling IAP or adding the invoker binding above manually.

### A3. Try it before you're authorized (browser)

Open `$URL` in your normal browser (signed in as `$ME`).

**What you'll probably see:** Google sign-in (if needed), then an IAP page saying you don't have access. IAP knows exactly who you are — and your identity has no IAP role on this resource. Being project Owner is about *managing* the project; reaching the app through IAP is a separate permission. (If the app loads anyway, run `gcloud iap web get-iam-policy --region=$REGION --resource-type=cloud-run --service=$SVC` and note what grants you access — then continue.)

### A4. Grant access — with a time limit (CLI)

```bash
EXP=$(date -u -d "+60 min" +%Y-%m-%dT%H:%M:%SZ)
gcloud iap web add-iam-policy-binding --region=$REGION --resource-type=cloud-run --service=$SVC \
  --member="user:$ME" --role=roles/iap.httpsResourceAccessor \
  --condition="expression=request.time < timestamp('$EXP'),title=lab17-60min,description=Lab access for one hour"
gcloud iap web get-iam-policy --region=$REGION --resource-type=cloud-run --service=$SVC
```

Reload the page (allow a minute or two to propagate). **What you should see:** the Cloud Run "hello" page. Read the binding out loud: "this one person may reach this one app, through IAP, until 60 minutes from now." No VPN, no IP allowlist, no firewall change — that's the zero-trust shift.

**Optional deny test:** open `$URL` in an incognito window signed in as your second Google account. Expect the IAP access-denied page.

Anonymous, from Cloud Shell:

```bash
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" $URL
```

**What you should see:** a redirect toward Google sign-in (HTTP 302) rather than the app ⚠️ exact status code may differ. The app never sees the request.

### A5. Log the decisions (console, then CLI)

1. Console → **IAM & Admin → Audit Logs**. Filter for **Cloud Identity-Aware Proxy API**. Check **Data Read** → **Save**. (These are Data Access logs — off by default. Module 18 explains why.)
2. Reload the app in your browser a couple of times; try the incognito account again if you have one.
3. Read the decisions:

```bash
sleep 60
gcloud logging read 'protoPayload.serviceName="iap.googleapis.com"' --freshness=30m --limit=10 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail,protoPayload.authorizationInfo[0].granted,protoPayload.requestMetadata.callerIp)"
```

**What you should see:** entries with your email and `granted` = `True`, and (if you tested) the second account with `False`. Each line is a **policy decision record** — who, what, from where, allowed or not. ⚠️ If nothing appears after a few minutes, open **Logs Explorer** with the same filter; the exact method name for Cloud Run IAP requests wasn't confirmed this run.

### A6. Revoke — and watch the decision change (CLI)

```bash
gcloud iap web remove-iam-policy-binding --region=$REGION --resource-type=cloud-run --service=$SVC \
  --member="user:$ME" --role=roles/iap.httpsResourceAccessor \
  --condition="expression=request.time < timestamp('$EXP'),title=lab17-60min,description=Lab access for one hour"
```

Wait a minute or two, then reload. **What you should see:** access denied again. (If you skip this step, the condition expires the access on its own at `$EXP`.) Access ended by policy, not by network.

### A7. (Optional — needs an organization) Add context: an access level

On a personal project with no organization, **skip this** — Access Context Manager policies live at the organization, and device attributes need Chrome Enterprise Premium. With an organization, the next step would be a basic access level allowing only your home IP range or country, attached to the IAP binding:

```yaml
# level.yaml — basic access level (example only)
- ipSubnetworks:
  - 203.0.113.0/24
```

```bash
# gcloud access-context-manager levels create lab17_home --title="lab17 home" \
#   --basic-level-spec=level.yaml --policy=POLICY_ID
```

Read it as the NIST picture: IAM + access level = **policy engine**; IAP = **policy enforcement point**.

---

## Part B — AWS (optional, read-only, $0)

Do **not** create a Verified Access instance — it bills per app-hour from creation. In CloudShell:

```bash
aws ec2 describe-verified-access-instances --query 'VerifiedAccessInstances[].VerifiedAccessInstanceId' 2>&1 | head -5
```

Expect an empty list. Then console → **VPC → Verified Access** (left menu). Note the objects you'd create: **trust providers** (identity: IAM Identity Center or OIDC; device: e.g., CrowdStrike, Jamf), an **instance**, **groups** with **Cedar** policies, and **endpoints** (load balancer, network interface, or — since 2025 — TCP/SSH/RDP targets). Write down which object is the PDP and which is the PEP.

## Part C — Microsoft (optional, read-only, $0)

Entra admin center as your sign-up identity (break-glass) or `labadmin`:

1. **Protection → Conditional Access → Policies → New policy from template.** Browse the "Zero Trust" templates (don't create — Conditional Access needs P1). Note signals (users, apps, locations, device platforms, risk) and controls (MFA strength, compliant device).
2. **Global Secure Access** (left menu). Note **Private Access** (per-app TCP/UDP, Quick Access) and **Internet Access**. Read the licensing banner.
3. Map: Conditional Access = **policy engine**; Global Secure Access client and cloud edge = **enforcement point**; Entra sign-in logs = **decision log**.

---

## Verify it worked

| Check | Expected |
|---|---|
| Service without IAP | `403` to anonymous curl |
| IAP enabled | `Iap Enabled: true`; IAP service agent has `run.invoker` |
| Before grant | IAP access-denied page for your identity |
| After conditional grant | App loads in browser |
| Anonymous curl | Redirect to sign-in, not the app |
| IAP Data Access logs | Entries with principal and `granted` true/false |
| After revoke | Access denied again |
| (B) AWS | No Verified Access instance created |

## What to notice (reflection questions)

1. What did you change to grant and revoke access? What did you *not* change? Compare with how you'd do it with a VPN and firewall.
2. Which NIST SP 800-207 component was IAM, which was IAP, and where's the decision log?
3. The app received a signed `x-goog-iap-jwt-assertion` header. Why should the app verify it rather than trust `x-goog-authenticated-user-email`?
4. For Compute Engine behind a load balancer, IAP can be bypassed if a firewall allows direct traffic. Which module 11 control prevents that, and whose responsibility is it?
5. Map this lab to the CISA ZTMM: which pillars did you touch, and roughly which maturity stage would a single IAP-protected app represent?

## Cleanup

**Google Cloud**

```bash
gcloud run services delete $SVC --region=$REGION --quiet
gcloud run services list --region=$REGION --filter="metadata.name~lab17" || true
```

1. **IAM & Admin → Audit Logs → Cloud Identity-Aware Proxy API** → uncheck **Data Read** → **Save** (restore the default).
2. **Google Auth Platform → Clients**: if IAP auto-generated an OAuth client for this lab (⚠️ exact name may vary), you may delete it — or keep it for future IAP labs. With no IAP-protected resources it grants nothing and costs nothing. Leave the branding/consent screen.

**AWS / Azure:** nothing created.

**Final check — nothing billable or exposed remains:** no `lab17-app` Cloud Run service; IAP Data Access logging back to default; lab OAuth client deleted or intentionally kept; no AWS Verified Access instance. (Logs already written stay in `_Default` for 30 days at no charge within the free allotment.)

## Write-up prompt

> On [date] I placed Google Cloud Identity-Aware Proxy directly in front of a private Cloud Run service in a personal lab, configured the OAuth consent flow for a project without an organization, and confirmed the IAP service agent was the service's only invoker. I granted myself access through IAP with an IAM Condition that expired after one hour, verified that unauthenticated requests were redirected to sign-in, enabled IAP Data Access audit logs and reviewed grant/deny decisions by principal and source IP, and revoked access without any network change. I mapped the design to NIST SP 800-207's policy engine and enforcement point, and compared it with AWS Verified Access and Microsoft Conditional Access with Global Secure Access. I deleted all resources afterward.
