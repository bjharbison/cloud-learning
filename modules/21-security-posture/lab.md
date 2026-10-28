# 21 Lab — Scan your own cloud like an auditor, then turn one finding into a ticket and close it

**Cost:** $0 expected. The core of this lab uses **Prowler**, an open-source (Apache 2.0) posture scanner, from Cloud Shell; it makes read-only API calls, which are free. The seeded misconfigurations are a custom VPC with no subnets, one firewall rule, an empty bucket, and a service account — none of which bill. **Do not start trials you won't cancel:** Google's SCC Premium project trial converts to pay-as-you-go after 30 days, and AWS GuardDuty (paid-plan accounts only) starts a 30-day trial — this lab deletes the GuardDuty detector before you leave. Azure: Defender for Cloud **Foundational CSPM** is free; leave the paid plans off. · **Time:** 90–120 min (Prowler scans take several minutes) · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Seed three realistic misconfigurations in your lab project.
2. Run a **CIS-style posture scan** with Prowler and find them among the results.
3. **Triage** and write one finding up as a **ticket** with owner, severity, evidence, fix, and verification.
4. **Remediate** and **rescan** to prove it's fixed.
5. See the native tools: SCC (if you have an organization), GuardDuty sample findings (AWS paid plan), Defender for Cloud secure score (Azure).

## Prerequisites

- Modules 00–20 done; budget alerts active.
- Cloud Shell, lab project selected. Know your module 03 path (organization or not).

```bash
PROJECT_ID=$(gcloud config get-value project)
B=lab21-$PROJECT_ID-$RANDOM
gcloud services enable compute.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com \
  storage.googleapis.com serviceusage.googleapis.com
```

---

## Part A — Google Cloud

### A1. Seed three misconfigurations (CLI)

**1. An over-privileged service account** (module 14's classic):

```bash
gcloud iam service-accounts create lab21-sa --display-name="lab21 over-privileged SA"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:lab21-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/editor --condition=None
```

No keys are created and nothing runs as this account; it simply holds a role it shouldn't.

**2. A firewall rule allowing SSH from anywhere.** Read this before running it:

```bash
gcloud compute networks create lab21-vpc --subnet-mode=custom
gcloud compute firewall-rules create lab21-allow-ssh-any --network=lab21-vpc \
  --direction=INGRESS --action=ALLOW --rules=tcp:22 --source-ranges=0.0.0.0/0 \
  --target-tags=lab21-nothing
```

> ⚠️ **Why this is bad, and why it's safe here.** A rule allowing `tcp:22` from `0.0.0.0/0` exposes SSH to every scanner and password-sprayer on the internet (ATT&CK T1133/T1110) — it's one of the most common cloud findings. Here it can't expose anything: `lab21-vpc` has **no subnets and no VMs**, and the rule only targets a tag no instance has. The **safe pattern** you'll switch to in A5 is Google's IAP TCP-forwarding range `35.235.240.0/20` with OS Login (module 05), or no SSH at all. You'll delete the rule and network in Cleanup.

**3. A bucket with fine-grained (ACL) access instead of uniform bucket-level access:**

```bash
gcloud storage buckets create gs://$B --location=us-central1 \
  --no-uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://$B --update-labels=lab=21
```

Public access prevention stays **on**, so nothing can be made public. If the create **fails** with an org-policy error about uniform bucket-level access, your organization's security baseline is enforcing UBLA — a guardrail from module 20 doing its job. Note it and continue with two seeded findings.

### A2. Install and run Prowler (CLI)

Prowler uses Application Default Credentials (your user, here). Its docs list Viewer, Service Usage Consumer, and one storage IAM-read permission; as project Owner you already have them.

```bash
gcloud auth application-default login            # follow the link, paste the code
gcloud auth application-default set-quota-project $PROJECT_ID

python3 -m venv ~/venv-prowler && ~/venv-prowler/bin/pip install -q prowler
~/venv-prowler/bin/prowler -v
~/venv-prowler/bin/prowler gcp --list-compliance | head -20
~/venv-prowler/bin/prowler gcp --project-ids $PROJECT_ID --status FAIL
```

⚠️ Prowler needs Python 3.10–3.13; if `pip install` fails on Cloud Shell's Python version, use the project's documented `pipx` method instead. The scan runs several minutes. At the end Prowler prints an overview table and the **paths of its output files** (CSV, JSON in OCSF format, and HTML by default) — copy that path:

```bash
OUT=<paste the output directory Prowler printed>
ls $OUT
```

**What you should see:** a list of compliance frameworks that includes CIS Google Cloud versions; then FAIL results grouped by service. Expect findings you didn't seed (default settings, missing org-level controls) — that's normal for a lab project.

### A3. Triage: find your three in the noise (CLI)

```bash
CSV=$(ls $OUT/*.csv | head -1)
head -1 "$CSV" | tr ';' '\n' | head -40          # learn the column names
grep -i "lab21" "$CSV" | cut -d';' -f1-40 | head
grep -ic "FAIL" "$CSV"
```

⚠️ Prowler's CSV is semicolon-delimited in recent versions and column order varies by version; use the header to find the check ID, severity, resource, and status columns. Then open the **HTML report** for a friendlier view: in Cloud Shell, click **⋮ → Download** and enter the HTML file path.

**What you should see:** FAIL rows naming `lab21-sa` (an SA with an admin/basic role), `lab21-allow-ssh-any` (SSH open to the internet), and your bucket (uniform bucket-level access disabled) ⚠️ (exact check names vary by Prowler version). Note each one's **severity** and any **CIS** control reference.

Now triage like a SOC lead, not like a scanner. For each of your three, answer: *exposed to whom?*, *what's the blast radius?*, *is anything actually using it?* You'll likely conclude: the Editor SA is the highest real risk (anyone who can act as it, or a key leaked later, gets broad project control); the firewall rule is "critical" by severity but currently unreachable (no subnets); the ACL bucket is low (empty, PAP on). Severity isn't priority.

### A4. Write the ticket (your notes)

Use this template for the firewall finding — the one with the scariest severity and the easiest fix:

```
Title:     [HIGH] SSH open to 0.0.0.0/0 — firewall rule lab21-allow-ssh-any (project <ID>)
Source:    Prowler <version>, check <check ID>, scan <timestamp>; maps to CIS GCP <control>
Owner:     <from labels / project owner>          SLA: 7 days (High)  ← your org's policy
Evidence:  rule allows tcp:22 from 0.0.0.0/0 on network lab21-vpc, target tag lab21-nothing
Exposure:  currently none (no subnets or instances) — would expose any VM later tagged lab21-nothing
Threat:    internet SSH brute force / exploitation (ATT&CK T1133, T1110); common initial access
Fix:       restrict source to IAP range 35.235.240.0/20 and use IAP + OS Login, or delete the rule;
           make the change in IaC (module 20); add a guardrail/alert for 0.0.0.0/0 on 22/3389
Verify:    rescan shows PASS for this rule; describe shows new source range
Exception: none requested
```

### A5. Remediate and verify (CLI)

```bash
gcloud compute firewall-rules update lab21-allow-ssh-any --source-ranges=35.235.240.0/20
gcloud compute firewall-rules describe lab21-allow-ssh-any --format="value(sourceRanges)"
gcloud projects remove-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:lab21-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/editor --condition=None
~/venv-prowler/bin/prowler gcp --project-ids $PROJECT_ID --status FAIL
```

**What you should see:** source range `35.235.240.0/20`; in the new output, no FAIL for `lab21-allow-ssh-any`'s internet exposure and none for `lab21-sa`'s Editor role. The ACL bucket still fails — leave it as a documented, accepted lab exception (that's step 5 of the workflow), and delete it in Cleanup.

Check the audit trail of your remediation (module 18): every fix is an Admin Activity event you can attach to the ticket as proof.

```bash
gcloud logging read "logName=\"projects/$PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity\" AND (protoPayload.methodName:\"firewalls.patch\" OR protoPayload.methodName=\"SetIamPolicy\")" \
  --freshness=1h --limit=5 --format="table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

### A6. Security Command Center (Path 1: you have an organization)

Console → **Security → Security Command Center**. If SCC isn't activated, read the activation screen and **stop** — note which tiers are offered and that Premium's project trial auto-converts after 30 days. **Don't start the Premium trial for this lab.**

If Standard is already active for your organization (Google auto-activated it for some orgs in 2026), look at **Findings** and filter to your lab project; then:

```bash
gcloud scc findings list projects/$PROJECT_ID --location=global \
  --filter='state="ACTIVE"' --limit=20 \
  --format="table(finding.category,finding.severity,finding.resourceName.basename())"
```

**What to notice:** scans run on a schedule (Standard roughly every 48 hours; first findings can take up to 72 ⚠️ timing from Google's Security Health Analytics page, not re-checked against the current tier page), so your seeded issues may not appear before you clean them up — a real-world lesson in why posture tools miss short-lived misconfigurations, and why audit-log alerts (module 19) complement them. If you're on Path 2 (no organization), SCC isn't available; Prowler was your CSPM today.

---

## Part B — AWS (optional)

### B1. Prowler on AWS (works on the Free plan)

AWS CloudShell, as `labadmin`. Install into `$HOME` (it persists):

⚠️ Prowler needs Python 3.10–3.13; check `python3 --version` first, and if CloudShell's default is older, use Prowler's documented `pipx` method or a newer `python3.x` if installed. The install is large relative to CloudShell's 1 GB `$HOME` — check `df -h ~` and remove the venv afterward (Cleanup does).

```bash
python3 -m venv ~/venv-prowler && ~/venv-prowler/bin/pip install -q prowler
~/venv-prowler/bin/prowler aws --list-compliance | grep -i cis
~/venv-prowler/bin/prowler aws --region us-east-1 --status FAIL
```

⚠️ A full AWS scan across all Regions can take a long time; limiting to one Region keeps it short (global services like IAM are still checked). **What to notice:** findings for the root account (MFA, access keys), `labadmin` (an IAM user with long-lived credentials — module 00's deliberate trade-off), and missing GuardDuty/Security Hub.

### B2. GuardDuty sample findings (paid-plan accounts only)

> If your AWS account is still on the **Free plan**, skip this — GuardDuty isn't supported there. On the paid plan, enabling GuardDuty starts a **30-day free trial**; you'll delete the detector at the end of this step.

```bash
D=$(aws guardduty create-detector --enable --query DetectorId --output text --region us-east-1)
aws guardduty create-sample-findings --region us-east-1 --detector-id $D \
  --finding-types "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS" "CryptoCurrency:EC2/BitcoinTool.B!DNS"
sleep 20
IDS=$(aws guardduty list-findings --region us-east-1 --detector-id $D --query 'FindingIds' --output text)
aws guardduty get-findings --region us-east-1 --detector-id $D --finding-ids $IDS \
  --query 'Findings[].{type:Type,sev:Severity,title:Title,sample:Service.AdditionalInfo.Value}' --output table
aws guardduty delete-detector --region us-east-1 --detector-id $D
```

**What you should see:** two findings with titles starting **[SAMPLE]**, severities around 8 (High). Read the credential-exfiltration one closely: it's module 05's metadata-theft scenario as GuardDuty reports it. These are **threat** findings, not posture findings — compare them with Prowler's output.

## Part C — Azure (optional): Defender for Cloud's free tier

Portal → **Microsoft Defender for Cloud**:

1. **Environment settings → your subscription → Defender plans.** Confirm **Foundational CSPM** is on (free) and paid plans (Defender CSPM, Servers, Storage…) are **Off**. Don't turn them on for this lab.
2. **Overview → Secure score**, then **Recommendations**. Filter by severity; open one and read its remediation steps and the **MCSB** control it maps to.
3. **Regulatory compliance:** see which standards are assigned (MCSB by default).

In Azure Cloud Shell:

```bash
az security secure-scores list --query "[].{name:displayName, current:score.current, max:score.max, pct:score.percentage}" -o table
```

⚠️ Output field names may differ by CLI version; use `-o json` to inspect. Optional: Prowler also scans Azure (`prowler azure --az-cli-auth`).

---

## Verify it worked

| Check | Expected |
|---|---|
| Seeded issues | Editor SA, SSH-from-anywhere rule (on an empty VPC), ACL bucket (unless UBLA enforced by org policy) |
| First Prowler scan | FAILs for each seeded issue, plus others |
| Ticket | Owner, severity, evidence, exposure, ATT&CK, fix, verification |
| After remediation | Rule source `35.235.240.0/20`; Editor binding gone; rescan clears both |
| Audit log | `firewalls.patch` and `SetIamPolicy` by you |
| (B2) GuardDuty | Two `[SAMPLE]` findings; detector deleted |
| (C) Defender | Foundational CSPM on, paid plans off; secure score visible |

## What to notice (reflection questions)

1. Prowler rated the firewall rule higher than the Editor SA. Which did you fix first and why? What context did the scanner lack?
2. Your rescan proved the fix. What stops the same rule from reappearing next week? (Hint: module 20 — and which Google org policy or hierarchical firewall policy would you use?)
3. SCC Standard scans about every 48 hours. An attacker opens SSH, uses it, and closes it within a day. Which tool catches that, and with what log?
4. GuardDuty and SCC Event Threat Detection are threat detectors; Prowler and Security Hub CSPM are posture tools. Give one example finding from each category.
5. Your scanner's identity can read nearly every configuration in the project. How would you protect and monitor it?

## Cleanup

**Google Cloud**

```bash
gcloud compute firewall-rules delete lab21-allow-ssh-any --quiet
gcloud compute networks delete lab21-vpc --quiet
gcloud projects remove-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:lab21-sa@$PROJECT_ID.iam.gserviceaccount.com --role=roles/editor --condition=None 2>/dev/null || true
gcloud iam service-accounts delete lab21-sa@$PROJECT_ID.iam.gserviceaccount.com --quiet
gcloud storage rm --recursive gs://$B 2>/dev/null || gcloud storage buckets delete gs://$B 2>/dev/null || echo "no lab21 bucket"
gcloud auth application-default revoke --quiet
rm -rf ~/venv-prowler "$OUT"
gcloud compute firewall-rules list --filter="name~lab21" --format="value(name)" || true
gcloud compute networks list --filter="name~lab21" --format="value(name)"
gcloud storage ls | grep lab21 || echo "no lab21 buckets"
```

Revoking Application Default Credentials removes the local credential file Prowler used — don't leave long-lived user credentials lying around in a shell. If you looked at SCC, confirm you did **not** start a Premium trial (Security Command Center → Settings → tier).

**AWS:** `rm -rf ~/venv-prowler ~/output 2>/dev/null`; confirm GuardDuty is off: `aws guardduty list-detectors --region us-east-1` returns an empty list.

**Azure:** nothing created. Confirm Defender paid plans are still **Off** under Environment settings.

**Final check — nothing billable remains:** no `lab21` firewall rule, network, SA, or bucket; no GuardDuty detector; no SCC Premium trial; no Defender paid plan.

## Write-up prompt

> On [date] I ran a CIS-aligned posture assessment of a personal Google Cloud lab project with the open-source tool Prowler after seeding three misconfigurations (an Editor-role service account, an internet-wide SSH firewall rule on an empty network, and a bucket using ACLs). I triaged the results by exposure and blast radius rather than severity alone, wrote one finding up as a remediation ticket with ATT&CK mapping and verification criteria, remediated two findings (restricting SSH to Google's IAP range and removing the Editor grant), confirmed the fixes with a rescan and Cloud Audit Logs, and documented the third as an accepted exception. [Optional: I generated and reviewed GuardDuty sample findings and reviewed Microsoft Defender for Cloud's secure score and recommendations under the free Foundational CSPM tier.] I removed all lab resources and credentials afterward.
