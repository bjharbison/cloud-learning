# 26 Lab — Think like an assessor: write an SSP excerpt for your lab project, with evidence

**Cost:** $0. Google Cloud: read-only `gcloud` queries plus enabling the Cloud Asset API (no charge for these searches); the FedRAMP Marketplace and NIST files are public. AWS (optional): an IAM credential report (free). Azure (optional): an Azure Policy initiative assignment on an empty resource group — Azure Policy evaluation of Azure resources is free ⚠️ (re-check the pricing page) — removed at the end. Nothing billable is created. · **Time:** 2 hours · **Clouds:** GCP (required), AWS and Azure (optional)

## Goal

1. Read a provider's **authorization status** in the FedRAMP Marketplace and its compliance scope page.
2. Pull the **NIST SP 800-53 Moderate baseline** as machine-readable **OSCAL** and inspect it.
3. Write a short **System Security Plan (SSP) excerpt** for your lab project: six controls, who's responsible, and command-line **evidence** for each.
4. Turn gaps into **POA&M** items.
5. (Optional) Generate AWS and Azure evidence for the same controls.

## Prerequisites

- Modules 00–25 done. Your normal lab project (not the deleted module 25 sandbox).
- Cloud Shell.

```bash
PROJECT_ID=$(gcloud config get-value project)
mkdir -p ~/lab26 && cd ~/lab26
```

---

## Part A — Google Cloud

### A1. Check authorization status (browser)

1. Open the **FedRAMP Marketplace** at <https://www.fedramp.gov/marketplace>. Search for **Google** (Google Cloud services), **AWS GovCloud**, and **Azure Government**. For each, record: offering name, status, and level or class shown, and the date you checked.
2. Open Google's **FedRAMP and DoD scope** page: <https://docs.cloud.google.com/docs/security/compliance/fedramp-dod-compliance-scope>. Pick three services you used in earlier labs (for example Cloud Storage, Cloud Run, Secret Manager). For each, note whether it's in scope for FedRAMP High, IL4, and IL5.
3. (Optional) In the console, go to Google's compliance documents download page (see the Audit Manager doc *Download Google Cloud compliance documents*) and find the FedRAMP-related artifacts available to you. Don't redistribute anything that requires an agreement.

Save notes in `status.md`. **What to notice:** the marketplace may show "Class" wording for some offerings and "High/Moderate" for others — the transition in progress.

### A2. Read the control baseline as data (CLI)

NIST publishes 800-53 Rev. 5 as **OSCAL** JSON in its `oscal-content` GitHub repository. Download the Moderate baseline profile and count its controls:

```bash
BASE=https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json
curl -sSfLO $BASE/NIST_SP-800-53_rev5_MODERATE-baseline_profile.json
jq '.profile.imports[0]."include-controls"[0]."with-ids" | length' NIST_SP-800-53_rev5_MODERATE-baseline_profile.json
jq -r '.profile.imports[0]."include-controls"[0]."with-ids"[]' NIST_SP-800-53_rev5_MODERATE-baseline_profile.json \
  | cut -d- -f1 | sort | uniq -c | sort -rn | head -10
jq -r '.profile.imports[0]."include-controls"[0]."with-ids"[]' NIST_SP-800-53_rev5_MODERATE-baseline_profile.json \
  | grep -E '^(ac-2|ac-6|au-2|au-11|cm-8|sc-7|sc-28)$'
```

⚠️ If the download fails, the file has moved — browse <https://github.com/usnistgov/oscal-content> to `nist.gov/SP800-53/rev5/json/` and use the current filename.

**What you should see:** a count of control IDs (base controls and enhancements), the families with the most controls, and confirmation that all seven controls used below are in the Moderate baseline. Compare your count with FedRAMP's ≈ 323 for Moderate (Class C): FedRAMP adds controls on top of NIST's baseline. This JSON is exactly what OSCAL-aware GRC tools ingest — the "machine-readable" direction in M-24-15 and FedRAMP 20x.

### A3. Gather evidence (CLI)

Run each command and save the output as evidence. Each maps to a control you'll describe in A4.

```bash
# AU-11 Audit record retention: what does each log bucket keep?
gcloud logging buckets list --location=global --project=$PROJECT_ID \
  --format="table(name.basename(),retentionDays,locked)" | tee ev-au11.txt

# AU-2 / AU-12 Event logging: which Data Access logs are on?
gcloud projects get-iam-policy $PROJECT_ID --format="yaml(auditConfigs)" | tee ev-au2.txt

# AC-2 / AC-6 Account management and least privilege: who has which role? Flag basic roles.
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
  --format="table(bindings.role,bindings.members)" | tee ev-ac2.txt
grep -E "roles/(owner|editor)" ev-ac2.txt || echo "no basic roles"

# SC-7 Boundary protection: any firewall rule open to the internet on SSH/RDP?
gcloud compute firewall-rules list --project=$PROJECT_ID \
  --format="table(name,network.basename(),direction,sourceRanges.list(),allowed[].map().firewall_rule().list())" | tee ev-sc7.txt

# CM-8 System component inventory: what exists in the project?
gcloud services enable cloudasset.googleapis.com --project=$PROJECT_ID
gcloud asset search-all-resources --scope=projects/$PROJECT_ID \
  --format="table(assetType,displayName,location)" | tee ev-cm8.txt
```

**What you should see:** `_Required` with 400 days and `_Default` with 30 (unless you changed it in module 18); probably no `auditConfigs` (Data Access off); your account with `roles/owner`; the default network's firewall rules if it still exists (check whether any allow `0.0.0.0/0` on 22 or 3389 — module 11 covered why that's bad and the IAP alternative); and a short inventory of leftover resources. If the inventory shows anything from an old lab, that's a cleanup finding too.

Hash the evidence, as you did in module 23:

```bash
sha256sum ev-*.txt | tee evidence-hashes.txt
```

### A4. Write the SSP excerpt (your notes)

Create `ssp-excerpt.md` with one row per control. Responsibility is **Customer**, **Shared**, or **Inherited** (from Google's authorization).

```bash
cat > ssp-excerpt.md <<'EOF'
# SSP excerpt — <PROJECT_ID> (personal lab, not a real system)

Authorization boundary: one Google Cloud project; identities: one Google Account admin + lab service accounts.

| Control | Implementation statement (what we do) | Responsibility | Evidence | Status |
|---|---|---|---|---|
| AC-2 Account management | | Customer | ev-ac2.txt | |
| AC-6 Least privilege | | Customer | ev-ac2.txt | |
| AU-2 Event logging | | Shared (Google generates; we choose Data Access) | ev-au2.txt | |
| AU-11 Audit record retention | | Shared | ev-au11.txt | |
| CM-8 System component inventory | | Customer | ev-cm8.txt | |
| SC-7 Boundary protection | | Customer | ev-sc7.txt | |
| SC-28 Protection of information at rest | Google encrypts at rest by default; CMEK not used | Shared / largely inherited | Google docs (module 16) | |
| PE-3 Physical access control | Not applicable to us — data-center physical security | Inherited | Google FedRAMP package | Inherited |
EOF
```

Fill in the blanks in two sentences per row. Be specific ("one human principal holds roles/owner; no service account holds a basic role"). Mark **Status** as Implemented, Partially implemented, or Planned.

**Assessor's check:** read AU-11 against OMB M-21-31's expectation of 12 months active storage for key logs (module 18). Does a 30-day `_Default` bucket meet it for the logs that live there?

### A5. Turn gaps into a POA&M (your notes)

For every row that isn't fully implemented, add an item:

```bash
cat > poam.md <<'EOF'
| ID | Control | Weakness | Planned fix | Milestone date | Status |
|---|---|---|---|---|---|
| P-01 | AU-11 | _Default bucket retains 30 days | Route key logs to a bucket with ≥ 365-day retention (module 18) | | Open |
EOF
```

Add at least two more from your evidence (common ones: owner role on a personal account with no break-glass alternative; no Data Access logging on sensitive services).

---

## Part B — AWS (optional): account-management evidence

AWS CloudShell, as `labadmin`.

```bash
aws iam generate-credential-report
sleep 10
aws iam get-credential-report --query Content --output text | base64 -d | cut -d, -f1,4,8,9,11 | column -t -s,
```

**What you should see:** each IAM user, whether a password is enabled, MFA status, and access-key status. That's **AC-2** and **IA-2** evidence in one file. Add an AWS row to your SSP excerpt.

Then, in the console, open **AWS Artifact → Reports** and search **FedRAMP**. Read what's offered and any agreement terms before downloading. Don't redistribute.

## Part C — Azure (optional): a regulatory compliance initiative

Azure Cloud Shell (Bash), as `labadmin`. Assign NIST's 800-53 initiative to an **empty** resource group and see what Azure Policy reports.

```bash
az group create -n lab26-rg -l eastus --tags lab=26
az policy set-definition list \
  --query "[?policyType=='BuiltIn' && contains(displayName,'NIST SP 800-53 Rev. 5')].{name:name, displayName:displayName}" -o table
```

Copy the `name` (a GUID) of the commercial-cloud initiative, then:

```bash
INIT=<paste-name>
RG_ID=$(az group show -n lab26-rg --query id -o tsv)
az policy assignment create --name lab26-nist --display-name "lab26 NIST 800-53 Rev5 (audit view)" \
  --policy-set-definition $INIT --scope $RG_ID --mi-system-assigned --location eastus
```

Some policies in the initiative can deploy or modify resources, so Azure requires a managed identity on the assignment. It does nothing unless you start a remediation task — don't. Evaluation takes up to about 30 minutes; then:

```bash
az policy state summarize --resource-group lab26-rg --query "results" -o json | head -30
```

Or Portal → **Policy → Compliance → lab26-nist** → browse by **control**. **What to notice:** the dashboard groups findings by 800-53 control ID — the same IDs as your SSP excerpt. An empty resource group will show few resources; the point is the mapping.

---

## Verify it worked

| Check | Expected |
|---|---|
| Status notes | Marketplace and scope-page findings for three providers, with dates |
| OSCAL | Control count and family breakdown from the Moderate baseline |
| Evidence | Five `ev-*.txt` files and their SHA-256 hashes |
| SSP excerpt | Eight controls with implementation, responsibility, evidence, status |
| POA&M | At least three items with planned fixes |
| (B/C) | AWS credential report row; Azure initiative compliance view |

## What to notice (reflection questions)

1. Which of your eight controls were fully **inherited**? Which were entirely **yours**? What does that say about "we're on a FedRAMP High cloud, so we're compliant"?
2. Which evidence would an assessor trust more — a screenshot or a command output with a hash and timestamp? How would FedRAMP 20x's KSIs change how you collect it?
3. Your inventory (CM-8) showed leftovers from earlier labs, or didn't. How would an agency keep a monthly inventory accurate for ConMon?
4. If this project held CUI for a defense contractor, which provider environment and which authorization level would DFARS 252.204-7012 require?
5. If an agency AO asked you, as a CE, "Will this be ATO'd?", what's the honest answer?

## Cleanup

**Google Cloud**

```bash
gcloud services disable cloudasset.googleapis.com --project=$PROJECT_ID --quiet || true
```

Download `status.md`, `ssp-excerpt.md`, `poam.md`, the `ev-*.txt` files, and `evidence-hashes.txt` (Cloud Shell **⋮ → Download**) — they're your evidence. They contain your project ID and email but no secrets; keep them out of public repos. Then `rm -rf ~/lab26`.

**AWS:** nothing created (the credential report is regenerated on demand and can't be deleted; it's harmless).

**Azure**

```bash
az policy assignment delete --name lab26-nist --scope $(az group show -n lab26-rg --query id -o tsv)
az group delete -n lab26-rg --yes --no-wait
```

**Final check — nothing billable remains:** no new Google Cloud resources (only an API toggled); no `lab26-nist` assignment (`az policy assignment list --query "[?name=='lab26-nist']"` returns `[]`) and no `lab26-rg`.

## Write-up prompt

> On [date] I practiced federal compliance documentation in a personal lab. I checked current FedRAMP Marketplace and provider scope listings for Google Cloud, AWS GovCloud, and Azure Government; parsed the NIST SP 800-53 Rev. 5 Moderate baseline in OSCAL JSON; and wrote a System Security Plan excerpt for my Google Cloud lab project covering eight controls (AC-2, AC-6, AU-2, AU-11, CM-8, SC-7, SC-28, PE-3) with customer/shared/inherited responsibility and hashed command-line evidence. I turned gaps into a POA&M. [Optional: I generated an AWS IAM credential report as account-management evidence and viewed an Azure Policy NIST SP 800-53 Rev. 5 initiative by control.]
