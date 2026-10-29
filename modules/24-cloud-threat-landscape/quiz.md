# 24 Quiz — Cloud threat landscape for CTI

1. In the Storm-0558 intrusion, what did the actor use to get into enterprise mailboxes, and on whose side of shared responsibility did the root failure sit?
<details><summary>Answer</summary>

A stolen Microsoft consumer (MSA) **signing key**, used to forge tokens that Exchange Online accepted for enterprise accounts because of a validation flaw. Key custody and token validation are the **provider's** responsibility — customers could only control visibility (logging).
</details>

2. How was Storm-0558 first detected, and what does that teach about logging?
<details><summary>Answer</summary>

A U.S. federal civilian agency noticed **MailItemsAccessed** events from an unexpected application ID in its Microsoft 365 audit logs (then a premium-tier log). Lesson: the logging tier and a baseline of normal app behavior decide whether you see token abuse at all.
</details>

3. Microsoft's September 2023 explanation of how the key was stolen was later qualified. How?
<details><summary>Answer</summary>

In March 2024 Microsoft added a note saying it had **not found** a crash dump containing the key material. The 2021 crash-dump path remains a hypothesis; how the key was taken isn't publicly established. Good CTI separates observed facts from hypotheses.
</details>

4. Name the two weaknesses Midnight Blizzard chained to get from a password spray to reading Microsoft executives' email.
<details><summary>Answer</summary>

A **legacy non-production test tenant account without MFA** (password spray, T1110.003), and a **legacy test OAuth application** with elevated access to the corporate tenant — used to create apps and grant the Exchange **full_access_as_app** role.
</details>

5. Why didn't blocking source IPs help against Midnight Blizzard's spraying?
<details><summary>Answer</summary>

Microsoft reported the actor used **residential proxies** — many ordinary consumer IPs with low reputation signal — so IP-based indicators were impractical. Detection has to be behavioral (spray patterns, new OAuth grants, app-only mail access).
</details>

6. Spot the misattribution: "Volt Typhoon broke into Azure tenants with stolen NTDS credentials, according to CISA."
<details><summary>Answer</summary>

Overstated. AA24-038A describes anomalous sign-ins to **one** victim's Azure tenant, possibly with AD-derived credentials, and says attribution of that activity was **inconclusive**. Accurate wording: "CISA and partners reported possible use of AD-derived credentials against a victim's Azure tenant but could not conclusively attribute it."
</details>

7. Scattered Spider: list three identity-plane persistence actions you would alert on, with where the log lives.
<details><summary>Answer</summary>

Any three: new MFA device/method registered (Entra audit "User registered security info"; AWS `EnableMFADevice`); **new federated IdP / domain federation** (Entra audit "Set domain authentication"; AWS `CreateSAMLProvider`); new cloud VM created by an unusual principal (Admin Activity `instances.insert`, `RunInstances`, Azure Activity Log); new access key / SA key (`CreateAccessKey`, `CreateServiceAccountKey`).
</details>

8. The 2024 Snowflake campaign involved no vulnerability in Snowflake. Why is it still a cloud-security case study?
<details><summary>Answer</summary>

It's shared responsibility in SaaS: Mandiant found customer accounts with **no MFA, unrotated passwords, and no network allowlists**, accessed with infostealer-stolen credentials. Identity settings are the customer's job; credential-exposure monitoring is a CTI deliverable.
</details>

9. What ATT&CK ID would you use today for "attacker disabled CloudTrail," and why might a 2024 report give a different one?
<details><summary>Answer</summary>

**T1685.002 Disable or Modify Cloud Log.** ATT&CK v19 (April 2026) revoked T1562 Impair Defenses and split Defense Evasion into Stealth and Defense Impairment; older reports use **T1562.008**.
</details>

10. Match the provider to its threat-intel offering: Google Threat Intelligence; GuardDuty Extended Threat Detection; Defender XDR / Sentinel threat intelligence.
<details><summary>Answer</summary>

Google Threat Intelligence → **Google** (Mandiant + VirusTotal + Google telemetry). GuardDuty Extended Threat Detection → **AWS** (multi-stage attack-sequence findings; AWS mostly embeds its intel in services). Defender XDR / Sentinel TI → **Microsoft** (standalone Defender Threat Intelligence capabilities were folded into these).
</details>

11. Scenario: an agency SOC wants to load your team's indicators into Microsoft Sentinel automatically. What formats and mechanisms do you propose, and what caveat do you add?
<details><summary>Answer</summary>

Publish **STIX 2.1** objects from a **TAXII 2.x** server for Sentinel's TAXII connector, or push via Sentinel's **threat intelligence upload API**; indicators land in the ThreatIntelIndicators/ThreatIntelObjects tables. Caveat: atomic IOCs decay fast (residential proxies, rotating infrastructure) — pair them with expiry dates and behavioral detections.
</details>

12. Why does the CTI writer say "Microsoft assesses with moderate confidence that Storm-0558 is China-based" instead of "China attacked Microsoft"?
<details><summary>Answer</summary>

Attribution discipline: name whose assessment it is and its confidence, separate fact from judgment, and avoid overstating. Decision-makers weigh a vendor's moderate-confidence assessment differently from a government's formal attribution.
</details>
