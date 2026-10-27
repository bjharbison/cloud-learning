# 16 Quiz — Encryption and key management

1. An agency official says, "Our data is encrypted at rest, so a stolen service-account key can't expose it." What's wrong with that?
<details><summary>Answer</summary>

Default encryption at rest protects against physical media theft. A principal with valid IAM access gets data decrypted for it automatically by the platform. Access control is IAM; encryption at rest isn't a substitute.
</details>

2. In plain language, what are a DEK and a KEK, and why does envelope encryption use both?
<details><summary>Answer</summary>

The DEK (data encryption key) encrypts the data locally; the KEK (key encryption key), held in KMS, encrypts the DEK. Only the small wrapped DEK goes to KMS, so large data never leaves its location, and controlling the KEK controls every DEK under it.
</details>

3. Put these in order from least to most customer control, and give one downside of the top rung: CMEK, provider-managed, external key manager, customer-supplied.
<details><summary>Answer</summary>

Provider-managed → CMEK → customer-supplied → external (customer-supplied and external both keep raw key material away from the provider at rest; external keeps it outside the cloud entirely). Downside of external keys: your key manager's availability and latency become part of the cloud service's availability, with no provider SLA for that piece.
</details>

4. True or false: rotating a Cloud KMS key re-encrypts existing data with the new version.
<details><summary>Answer</summary>

False. Rotation creates a new primary version for new encryption. Existing data stays under the version that encrypted it, which must stay enabled to read it.
</details>

5. Spot the misconfiguration: one Google group holds both `roles/cloudkms.admin` and `roles/cloudkms.cryptoKeyEncrypterDecrypter` on production keys.
<details><summary>Answer</summary>

No separation of duties: the same people can change key policy and use the key to decrypt. Split key administration from key use, ideally in a dedicated key project.
</details>

6. You disable the key version protecting a CMEK bucket. Which operations still work, and which fail?
<details><summary>Answer</summary>

Reading object data (download, copy, rewrite) fails. Listing and deleting objects still work because metadata uses Google's keys. If the disabled version is primary, new writes fail too. Re-enabling restores access; destroying makes the data unrecoverable.
</details>

7. Compare deletion safety nets: Google Cloud KMS key versions, AWS KMS keys, Azure Key Vault.
<details><summary>Answer</summary>

Google: destroy is scheduled (default 30 days, 24 hours–120 days) and billed until destroyed; then versions, keys, and key rings can be deleted. AWS: schedule deletion with a 7–30 day window (default 30), not billed while pending, cancellable. Azure: soft delete is mandatory (7–90 days, default 90); purge protection, if enabled, is irreversible and blocks purging until retention ends.
</details>

8. What does Key Access Justifications do, and what does it require?
<details><summary>Answer</summary>

It attaches a reason code to each request to use a key and lets the customer's policy (in Cloud KMS or at an external key manager) approve or deny based on that reason. It's available only with Assured Workloads control packages.
</details>

9. Which cloud's secrets manager rotates secrets natively, and what do the other two do?
<details><summary>Answer</summary>

AWS Secrets Manager rotates via Lambda (managed rotation for some services). Google Secret Manager sends Pub/Sub rotation notifications on a schedule and your code rotates. Azure Key Vault has key rotation policies; secret rotation is event-driven with your own code.
</details>

10. Scenario: describe the January 2025 S3 ransomware technique AWS reported, its ATT&CK mapping, and two preventive controls.
<details><summary>Answer</summary>

Attackers with stolen credentials re-encrypted S3 objects using SSE-C (customer-provided keys) via `CopyObject`, so only they held the key — T1486 Data Encrypted for Impact. Controls: block SSE-C by bucket policy or RCP (now default on new buckets since April 2026), short-term credentials instead of long-lived keys, versioning and backups, and alerting on SSE-C requests in CloudTrail.
</details>

11. Where are Encrypt/Decrypt calls logged by default on Google Cloud vs AWS?
<details><summary>Answer</summary>

Google: Data Access audit logs, which are off by default — enable them for Cloud KMS. AWS: KMS cryptographic operations are logged to CloudTrail by default (as management events; a trail can exclude all KMS events, which is itself logged).
</details>

12. An agency requires FIPS-validated modules. What's the nuance you raise in September 2026 and later?
<details><summary>Answer</summary>

FIPS 140-2 certificates moved to NIST's Historical List in September 2026. Existing systems may keep using them, but new procurements increasingly want FIPS 140-3. Check which certificate each service relies on (e.g., Google Cloud HSM states 140-2 Level 3; AWS KMS states 140-3 Level 3).
</details>
