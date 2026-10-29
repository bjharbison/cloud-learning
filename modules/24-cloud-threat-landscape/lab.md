# 24 Lab — From threat report to hunt: turn public reporting into cloud collection and detections

**Cost:** $0. Read-only queries against audit logs you already have (Google Cloud Admin Activity, AWS CloudTrail Event history, Microsoft Entra portal views). The STIX step runs a free Python library in Cloud Shell. Nothing is created in any cloud. · **Time:** 2 hours · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

Work like a cloud CTI analyst on a small team:

1. **Extract** cloud and identity techniques from a primary advisory into an intel-to-detection matrix.
2. **Map** each technique to the log event that would show it on Google Cloud, AWS, and Azure.
3. **Hunt** your own lab history for those events.
4. **Package** atomic indicators as a **STIX 2.1** bundle, the format Sentinel and many SIEMs ingest.
5. **Write** a one-page CTI product for an agency CISO.

## Prerequisites

- Modules 00–23 done (modules 18 and 22 especially).
- Read README case 4 (Scattered Spider) and open CISA **AA23-320A** with its July 2025 update: <https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a>.
- Google Cloud Shell, lab project selected.

```bash
PROJECT_ID=$(gcloud config get-value project)
mkdir -p ~/lab24 && cd ~/lab24
```

**Rules of engagement:** this lab only *reads* your own logs. Use public reporting only — no employer or non-public material.

---

## Part A — Google Cloud

### A1. Build the intel-to-detection matrix (your notes)

Create `~/lab24/matrix.md`. From AA23-320A, pull **at least six** cloud or identity behaviors. For each, fill in one row:

| Behavior (from report) | ATT&CK ID | Google Cloud log event | AWS CloudTrail event | Azure / Entra event | Logged by default? |
|---|---|---|---|---|---|

Starter rows — check each against the advisory, then add your own:

```bash
cat > matrix.md <<'EOF'
| Behavior | ATT&CK | Google Cloud | AWS | Azure/Entra | Default? |
|---|---|---|---|---|---|
| Creates cloud VMs for persistence | T1578.002 | compute.instances.insert (Admin Activity) | RunInstances | Microsoft.Compute/virtualMachines/write (Activity Log) | Yes |
| Adds credentials to an identity | T1098.001 | google.iam.admin.v1.CreateServiceAccountKey | CreateAccessKey | "Update application – Certificates and secrets management" (Entra audit) | Yes |
| Grants a role | T1098.003 | SetIamPolicy | AttachUserPolicy / PutRolePolicy | roleAssignments/write | Yes |
| Registers a new MFA method | T1098.005 (per advisory) | Workspace/Cloud Identity admin & login audit ⚠️ | CreateVirtualMFADevice / EnableMFADevice | "User registered security info" (Entra audit) | Yes |
| Adds a federated IdP | T1484.002 (per advisory) | Cloud Identity SSO profile change ⚠️ | CreateSAMLProvider / CreateOpenIDConnectProvider | "Set domain authentication" (Entra audit) | Yes |
| Bulk reads from storage | T1530 | storage.objects.get (Data Access) | GetObject (data events) | StorageRead (resource logs) | **No** |
EOF
cat matrix.md
```

The ⚠️ rows are on purpose: Google Workspace/Cloud Identity events live in a different audit stream than Cloud Audit Logs. Note which ones you'd have to confirm in a real engagement — that's a **collection gap**, and naming it is part of the product.

### A2. Hunt your own history (CLI)

Your earlier labs created several of these events. Search 30 days of Admin Activity logs:

```bash
FILTER_BASE="logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\""

# T1098.001 — new service-account keys
gcloud logging read "$FILTER_BASE AND protoPayload.methodName=\"google.iam.admin.v1.CreateServiceAccountKey\"" \
  --freshness=30d --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.requestMetadata.callerIp)"

# T1578.002 — VM creation
gcloud logging read "$FILTER_BASE AND protoPayload.methodName:\"compute.instances.insert\"" \
  --freshness=30d --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.resourceName)"

# T1098.003 — IAM policy changes, with the user agent (module 20 trick)
gcloud logging read "$FILTER_BASE AND protoPayload.methodName=\"SetIamPolicy\"" \
  --freshness=30d --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.requestMetadata.callerSuppliedUserAgent)"
```

**What you should see:** events from earlier labs (for example, VMs from labs 05 and 23, IAM changes from labs 14 and 22). Possibly no key-creation events — module 23 deliberately used impersonation instead of keys. Every hit is benign. For each, ask the analyst question: *what context would distinguish this from Scattered Spider doing the same thing?* (Known pipeline identity? Expected IP? Change ticket?)

### A3. Find the behavioral pattern (CLI)

Single events are noisy. Scattered Spider's pattern is a **sequence**: new identity or credential, then compute or discovery from the same principal. Count Admin Activity actions per principal per day to see your own baseline:

```bash
gcloud logging read "$FILTER_BASE" --freshness=30d --limit=1000 \
  --format="value(timestamp,protoPayload.authenticationInfo.principalEmail)" \
  | awk '{print substr($1,1,10), $2}' | sort | uniq -c | sort -rn | head -15
```

**What you should see:** a short list of principals — you and a few service accounts — with daily counts. A new principal appearing in this list, or a known one with a spike, is the kind of anomaly that starts a hunt. Write down your baseline: *how many distinct principals act in this project in a normal week?*

### A4. Package indicators as STIX 2.1 (CLI)

Atomic indicators are a small part of cloud CTI, but you need to know the format. Use the open-source `stix2` Python library (OASIS CTI TC) to build a bundle. The values below are **documentation examples** (RFC 5737 test IP and the reserved `example` domain), not real indicators:

```bash
pip install --user --quiet stix2
cat > make_bundle.py <<'EOF'
from stix2 import Indicator, ThreatActor, Relationship, Bundle
actor = ThreatActor(name="Example cluster (lab)", description="Lab-only placeholder actor")
ind_ip = Indicator(name="Lab test IP", pattern="[ipv4-addr:value = '192.0.2.10']",
                   pattern_type="stix", indicator_types=["malicious-activity"])
ind_dom = Indicator(name="Lab test domain", pattern="[domain-name:value = 'helpdesk-login.example']",
                    pattern_type="stix", indicator_types=["malicious-activity"])
rels = [Relationship(i, "indicates", actor) for i in (ind_ip, ind_dom)]
print(Bundle(actor, ind_ip, ind_dom, *rels).serialize(pretty=True))
EOF
python3 make_bundle.py > bundle.json && head -30 bundle.json
```

**What you should see:** a JSON bundle with `threat-actor`, `indicator`, and `relationship` objects, each with a `type--UUID` ID. This is what a TAXII server would serve to Sentinel's TAXII connector, or what you'd push with Sentinel's upload API. Note the `pattern` syntax — it's how STIX describes an observable.

**Reflection:** UNC3944 and APT29 used residential proxies and short-lived infrastructure. How long would an IP indicator in this bundle stay useful? Add a `valid_until` you'd defend.

### A5. Write the product (your notes)

In `~/lab24/brief.md`, write a one-page product for a fictional agency CISO who runs Google Cloud and Microsoft 365. Structure:

1. **BLUF** (two sentences).
2. **Key judgments**, each with a source and confidence word ("CISA and partners assess…").
3. **Why it matters to us** — three exposures in *our* environment (help-desk resets, MFA methods, federation).
4. **Collection gaps** from your matrix (the ⚠️ and "No" rows).
5. **Recommended actions** — three, each tied to a detection or control from modules 15, 18, or 22.

Keep it under 400 words. Estimative language, no unattributed claims.

---

## Part B — AWS (optional): hunt CloudTrail Event history

AWS CloudShell, as `labadmin`. Event history is free and covers 90 days of management events.

```bash
for EV in RunInstances CreateAccessKey CreateLoginProfile AttachUserPolicy CreateSAMLProvider EnableMFADevice; do
  echo "== $EV"
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=$EV \
    --max-results 5 --query 'Events[].[EventTime,Username]' --output text
done
```

**What you should see:** a few hits from earlier labs (for example, `CreateAccessKey` from lab 23) and empty results for the rest. Add the AWS column findings to your matrix. Scattered Spider also used **Systems Manager** for discovery — which `ssm.amazonaws.com` event names would you add? (Look them up in the CloudTrail and SSM docs rather than guessing.)

## Part C — Azure (optional): the APT29 checks in the Entra portal

Signed in as your lab admin at <https://entra.microsoft.com>. These are read-only views.

1. **Enterprise applications → All applications** → open any app → **Permissions**. Are any **application** (app-only) permissions granted? Midnight Blizzard's key step was an app with app-only mail access.
2. **Monitoring & health → Audit logs**, filter **Category: ApplicationManagement** and **UserManagement**. Find consent grants and "security info" (MFA method) registrations from earlier labs.
3. **Monitoring & health → Sign-in logs** → add the **Authentication requirement** column. Any successful sign-ins with **single-factor** authentication?

Free tenants keep sign-in and audit logs only a short time (module 18), so you may see little. Record that as a collection gap too.

---

## Verify it worked

| Check | Expected |
|---|---|
| Matrix | ≥ 6 behaviors, each with ATT&CK ID and a log event per cloud; gaps marked |
| Hunt | Admin Activity results for keys / VMs / IAM changes (or explained empties) |
| Baseline | Principal-per-day counts and a written "normal" |
| STIX | `bundle.json` with indicator, actor, relationship objects |
| Product | `brief.md` under 400 words, attributed judgments, gaps, actions |

## What to notice (reflection questions)

1. Which of AA23-320A's techniques can't you see at all with default logging on each cloud?
2. Your baseline showed *N* principals. How would an attacker who creates a new service account or federated identity stand out — and how could they blend in?
3. In the Storm-0558 case the customer's only control was visibility. What's the equivalent provider-side risk for Google Cloud, and what would you ask Google about it?
4. How does writing "Microsoft assesses with moderate confidence" change how a CISO should act compared with "China hacked Microsoft"?
5. Which deliverable from today would a SOC actually use — the IOC bundle or the matrix? Why?

## Cleanup

Nothing was created in any cloud.

```bash
# Download matrix.md, brief.md, bundle.json first (Cloud Shell ⋮ → Download) — they're your evidence.
pip uninstall -y stix2 stix2-patterns 2>/dev/null || true
rm -rf ~/lab24
```

**Final check — nothing billable remains:** no resources were created; Event history and Entra views are free. Confirm in each billing console that no new charges appeared today.

## Write-up prompt

> On [date] I practiced cloud threat-intelligence analysis in a personal lab. I extracted cloud and identity techniques from CISA advisory AA23-320A (Scattered Spider), mapped each to MITRE ATT&CK and to the specific audit-log events on Google Cloud, AWS, and Microsoft Entra ID, and identified collection gaps. I hunted 30 days of my own Google Cloud Admin Activity logs for those events, built a per-principal activity baseline, packaged example indicators as a STIX 2.1 bundle, and wrote a one-page attributed intelligence brief with recommended detections. [Optional: I hunted AWS CloudTrail Event history and reviewed Entra ID app permissions, audit logs, and sign-in authentication requirements.]
