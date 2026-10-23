# Glossary

Plain-language definition first, then how practitioners use the term. Alphabetical. Modules append as they're built.

**Break-glass account** — An emergency admin identity kept locked away, used only when normal admin access fails, and alerted on whenever it signs in. (Module 00)

**Budget (cloud billing)** — A spending threshold that sends alerts as actual or forecasted cost crosses percentages you set. On all three clouds, budgets notify; they don't stop resources. (Module 00)

**Cloud shell** — A free, temporary Linux environment in the browser, pre-authenticated and preloaded with the provider's CLI: Google Cloud Shell, AWS CloudShell, Azure Cloud Shell. Keeps credentials off your laptop. (Module 00)

**Container** — A packaged app plus its libraries that runs as an isolated process on a shared host kernel, separated by Linux namespaces (what it can see) and cgroups (what it can use). Faster and denser than a VM; a weaker isolation boundary. Homelab equivalent: Docker or Proxmox LXC. (Module 01)

**Control plane / data plane** — The control plane is where you *manage* resources (create a VM, change a policy) — almost always API calls. The data plane is where the resource *does its work* (traffic through a VM, reads from a bucket). Logging and permissions often differ between the two.

**Free trial vs free tier** — A free trial is time-limited credit you can spend broadly (Google $300/90 days; AWS up to $200 on a 6-month free plan; Azure $200/30 days, as of 2026). A free tier is specific services with monthly limits that stay free. (Module 00)

**Hardware root of trust** — A chip that verifies a server's firmware before the main CPU runs anything, so tampered hardware won't boot. Google: Titan (and Caliptra); AWS: Nitro Controller + Nitro Security Chip; Azure: Cerberus. (Module 01)

**Hypervisor** — Software that runs multiple isolated virtual machines on one physical server. Type 1 runs on bare metal (KVM, Hyper-V, Nitro Hypervisor); Type 2 runs as an app on a normal OS. (Module 01)

**IaaS / PaaS / SaaS** — How much of the stack the provider runs for you. IaaS: they run hardware and virtualization; you run the OS up. PaaS: they also run the OS and runtime; you bring code and data. SaaS: they run the whole application; you manage users and data. (Module 01)

**IAM Identity Center (AWS)** — AWS's service for human sign-in to AWS accounts and apps, using permission sets instead of long-lived IAM users. Its organization instance runs in an AWS Organizations management account. (Module 00)

**Least privilege** — Give each identity only the permissions it needs, for only as long as it needs them. The cloud version of need-to-know.

**Multi-tenancy** — Many customers' workloads sharing the same physical infrastructure, kept apart by the hypervisor and hardware. NIST calls it resource pooling. (Module 01)

**NIST SP 800-145** — The U.S. government's definition of cloud computing: five essential characteristics (on-demand self-service, broad network access, resource pooling, rapid elasticity, measured service), three service models, four deployment models. Citing it signals fluency with government customers. (Module 01)

**Nitro System (AWS)** — AWS's virtualization platform: Nitro Cards (networking, storage, management offload), the Nitro Security Chip, and the minimal Nitro Hypervisor. (Module 01)

**Offload card / processor** — Dedicated hardware that handles networking, storage, encryption, and management off the host CPU, keeping provider control software out of tenant reach. Google Titanium Offload Processors, AWS Nitro Cards, Azure Boost. (Module 01)

**Permission set (AWS)** — A reusable bundle of permissions in IAM Identity Center that you assign to a user or group for a specific AWS account. (Module 00)

**Phishing-resistant MFA** — A second factor cryptographically bound to the real website (passkeys, FIDO2 security keys), so a fake login page can't capture and replay it. SMS codes and push approvals are not phishing-resistant. (Module 00)

**Region / zone** — A region is a geographic area containing several isolated data-center groups called zones (AWS: Availability Zones). Spreading across zones protects against a single facility failing; spreading across regions protects against a regional outage. (Module 02)

**Root user (AWS)** — The identity created with an AWS account, with unrestricted access including billing and account closure. AWS requires MFA on it; best practice is no access keys and rare use. Google Cloud has no direct equivalent. (Module 00)

**Shared fate** — Google Cloud's framing that the provider should actively help customers secure their workloads (secure defaults, blueprints, guidance), on top of the shared responsibility split. Doesn't move the line: customers still configure identity and access. (Module 01)

**Shared responsibility model** — The provider secures the cloud itself (facilities, hardware, hypervisor); the customer secures what they put in it. Identity, access control, firewall rules, network configuration, and data are always the customer's job. (Module 01)

**Titanium (Google Cloud)** — Google's hardware security architecture: Titan root-of-trust chips, Caliptra, Titanium Offload Processors, and related components that verify boot integrity and offload I/O and encryption. (Module 01)

**VM escape** — Code inside a virtual machine breaking out to the hypervisor or host. Rare in public reporting and the provider's responsibility to prevent; container escape (ATT&CK T1611) is the customer-side analog. (Module 01)

**VPC (Virtual Private Cloud)** — A private, software-defined network inside a cloud provider, where you define IP ranges, subnets, routes, and firewall rules. Closest homelab analogy: your OPNsense-managed VLANs — but defined entirely by API. (Module 10)
