# 05 Quiz — Compute

1. Name the five things you choose when you create a cloud VM, plus the one people forget.
<details><summary>Answer</summary>

Machine type, image, boot disk, network interface, and metadata/startup settings — plus the VM's **identity** (Google service account, AWS instance profile, Azure managed identity), which decides what the VM itself can do in the cloud.
</details>

2. Match the blueprint and the managed fleet on each cloud.
<details><summary>Answer</summary>

Google: instance template → managed instance group (MIG). AWS: launch template → Auto Scaling group. Azure: scale set model → Virtual Machine Scale Set.
</details>

3. You delete a VM that belongs to a MIG with target size 2. What happens, and what's the general principle?
<details><summary>Answer</summary>

The MIG creates a replacement to restore the target size. Principle: desired-state management — you declare how many, the platform reconciles reality to match. Kubernetes works the same way (module 06).
</details>

4. Why should autoscaling always have a maximum? Give a security reason and a public-sector reason.
<details><summary>Answer</summary>

Security: a bug, attack, or traffic flood can't scale you into a huge bill or give an attacker unlimited compute. Public sector: the max is a ceiling that keeps spend inside a fixed appropriation (Antideficiency Act, module 04).
</details>

5. Compare IAP TCP forwarding, Session Manager, and Azure Bastion. Which needs no inbound rule at all?
<details><summary>Answer</summary>

All three broker admin access after checking cloud identity, so VMs need no public IP. IAP needs a firewall rule allowing port 22 from IAP's range (35.235.240.0/20). Bastion connects to the VM's private IP from inside the VNet. **Session Manager** needs no inbound rule — the SSM Agent connects outbound to Systems Manager.
</details>

6. What problem does OS Login solve compared with SSH keys in project metadata?
<details><summary>Answer</summary>

Metadata keys are static and outlive the people who added them; anyone who can edit project metadata can add a key to every VM. OS Login ties Linux accounts to Google identities and IAM roles (`roles/compute.osLogin` / `roles/compute.osAdminLogin`), so removing a role revokes access everywhere and access is checked continuously.
</details>

7. An attacker finds an SSRF bug in a web app on an EC2 instance. What are they after, and what two controls blunt it?
<details><summary>Answer</summary>

The instance metadata service at 169.254.169.254, to steal the instance role's temporary credentials (ATT&CK T1552.005). Controls: require IMDSv2 (session tokens defeat simple SSRF), and give the instance profile least privilege so stolen credentials are worth little.
</details>

8. Spot the misconfiguration: "Our Google VMs use the default compute service account, and the project was created in 2022 under an org that never changed defaults."
<details><summary>Answer</summary>

The default service account may hold the broad Editor role (automatic grant), so any shell or SSRF on any VM can act as an editor of the whole project. Use a dedicated, least-privilege service account (or none), and enforce the org policy that disables automatic grants.
</details>

9. True or false: a Spot e2-micro in us-central1 is covered by Google's always-free tier.
<details><summary>Answer</summary>

False. The free tier covers one **non-preemptible** e2-micro's worth of hours per month in us-west1, us-central1, or us-east1.
</details>

10. What do Shielded VM / Trusted Launch protect, and what do Confidential VMs add?
<details><summary>Answer</summary>

Shielded/Trusted Launch protect the boot chain: Secure Boot, a vTPM, and integrity monitoring against rootkits and bootkits. Confidential VMs add hardware memory encryption (AMD SEV/SEV-SNP, Intel TDX) with keys the hypervisor can't read, plus hardware attestation — protecting data **in use**.
</details>

11. Scenario: an agency wants to lift-and-shift a web tier that must survive a zone outage, with admins who can't have open SSH. Sketch it on Google Cloud.
<details><summary>Answer</summary>

Instance template (hardened golden image, Shielded VM, no external IP, least-privilege service account) → regional MIG across 2–3 zones with autohealing health checks and autoscaling with min/max → load balancer in front (module 12). Admin access via OS Login + IAP only; firewall allows 22 from 35.235.240.0/20 only; IAP and OS Login roles granted to an admin group.
</details>

12. Which ATT&CK technique describes backdooring a golden image, and why is it so effective?
<details><summary>Answer</summary>

T1525 Implant Internal Image. Every VM built from the image inherits the backdoor, including replacements created by autohealing and autoscaling — so the defender's own automation spreads the compromise.
</details>
