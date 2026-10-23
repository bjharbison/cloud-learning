# Lab Safety

Read before any lab. The goal is zero surprise bills and zero exposed accounts.

## Before the first lab (Module 00 walks through these)

1. **Separate identities.** Use a personal email for these accounts — never a work account.
2. **MFA on the top-level identity** for all three clouds (Google account, AWS root user, Azure/Entra global admin). Prefer a hardware key or authenticator app over SMS.
3. **Don't work as root/owner day to day.** Create a separate admin identity and use that.
4. **Budget alerts on every cloud** at small thresholds (e.g., $1, $5, $10). Alerts notify; they don't stop spending — know how to shut things down.
5. **Know your free-tier terms.** Each provider's free tier and new-account credits have changed in recent years and differ in how they expire. Check the current official free-tier page for each cloud before starting, and note the expiry date in `PROGRESS.md`.

## During every lab

- Prefer the provider's **cloud shell** — nothing to install, no credentials on your laptop.
- **Smallest sizes, one region.** Use the free-tier-eligible machine type and region the lab specifies.
- **Label/tag everything** with `lab=<module-number>` so cleanup is easy to verify.
- **Never expose SSH/RDP to the whole internet** (`0.0.0.0/0`). Use identity-based access (Google IAP, AWS Systems Manager Session Manager, Azure Bastion) or restrict to your own IP.
- **Never commit credentials.** No keys, service-account JSON, `.tfvars` with secrets, or Terraform state in this repo — `.gitignore` blocks the common ones, but check `git status` before every commit.

## After every lab

- Run the lab's **Cleanup** section. Then confirm in the console/billing view that nothing labeled for the lab remains.
- Watch especially for things that bill while idle: static/external IPs, load balancers, NAT gateways, managed Kubernetes control planes, persistent disks/snapshots, and database instances.
- On Google Cloud, deleting a **project** is the cleanest full reset. On AWS and Azure, deleting a **resource group** (Azure) or using tag-based cleanup (AWS) is the closest equivalent.

## Attack-emulation labs (Phase 6)

- Only in your own accounts, against resources you created for the lab.
- Use a **dedicated** project/account/subscription for these labs, then delete it.
- Use recognized open-source tools named in the lab; read what each command does before running it.
