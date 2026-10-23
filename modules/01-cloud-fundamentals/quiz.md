# 01 Quiz — Cloud fundamentals

1. Name NIST SP 800-145's five essential characteristics.
<details><summary>Answer</summary>

On-demand self-service, broad network access, resource pooling, rapid elasticity, measured service.
</details>

2. An agency says it already has a "private cloud": a VMware cluster where teams file a ticket and wait three days for a VM. Using NIST, what's missing?
<details><summary>Answer</summary>

On-demand self-service (and likely rapid elasticity and measured service). It's virtualization, not cloud, by NIST's definition.
</details>

3. You run `uname -r` on a Docker host and inside one of its containers. Same or different? Then on a KVM host and inside one of its VMs?
<details><summary>Answer</summary>

Container: same — containers share the host kernel. VM: different — each VM boots its own kernel above the hypervisor.
</details>

4. Match the custom hardware to the cloud: Nitro, Titanium, Azure Boost, Titan, Cerberus.
<details><summary>Answer</summary>

AWS: Nitro. Google Cloud: Titanium (offload/security architecture) and Titan (root-of-trust chip). Azure: Azure Boost (offload) and Cerberus (root of trust).
</details>

5. What two jobs do these custom chips and cards do, in plain words?
<details><summary>Answer</summary>

(1) Verify firmware before the server boots (root of trust). (2) Take networking, storage, encryption, and management work off the main CPU, so provider control software sits outside tenants' reach.
</details>

6. True or false: in PaaS, the provider is responsible for firewall rules because it manages the platform.
<details><summary>Answer</summary>

False. The provider builds the firewall capability; the customer configures who and what can reach the service. Firewall rules, identity, VPN config, and SSH/RDP access are always the customer's.
</details>

7. Spot the misconfiguration: a VM on a network with a firewall rule `allow tcp:22 from 0.0.0.0/0` and an external IP. What's wrong, and what's the safer pattern on each cloud?
<details><summary>Answer</summary>

SSH is exposed to the whole internet; scanners will find it in minutes. Safer: no external IP and identity-based access — Google IAP TCP forwarding (firewall allows only 35.235.240.0/20), AWS Systems Manager Session Manager, Azure Bastion. Or at minimum restrict the source to your own IP.
</details>

8. What does AWS mean by "security of the cloud" vs "security in the cloud"? Give one example of each.
<details><summary>Answer</summary>

Of: AWS protects the hardware, software, networking, and facilities (e.g., physical data-center security, the hypervisor). In: the customer secures what they put there (e.g., security group configuration, IAM permissions, guest OS patching, data).
</details>

9. What is Google's "shared fate," and does it change who configures IAM?
<details><summary>Answer</summary>

Google's framing that the provider should actively help customers be secure (secure defaults, blueprints, guidance). It doesn't change the line: IAM configuration remains the customer's.
</details>

10. Scenario: a customer asks, "How do I know another tenant can't read my VM's memory?" Outline a credible answer.
<details><summary>Answer</summary>

Tenant isolation rests on the hypervisor and hardware: a minimal hypervisor, hardware-assisted virtualization, silicon roots of trust, and offload cards keeping provider control outside tenant reach (cite Nitro / Titanium / Azure Boost by name). Point to the provider's published architecture docs and third-party audits/authorizations. For more, offer confidential computing (encrypted memory) — module 16. Don't claim "impossible."
</details>

11. Which ATT&CK technique covers breaking out of a container, and why is it more relevant to customers than VM escape?
<details><summary>Answer</summary>

T1611 Escape to Host. Container hosts (e.g., Kubernetes nodes) are customer-managed and often misconfigured (privileged containers, host mounts), while provider hypervisor escapes are rare and handled by the provider.
</details>

12. Why is cloud's OpEx model in tension with government appropriations?
<details><summary>Answer</summary>

Appropriations are fixed amounts for fixed periods; elastic, usage-based bills vary month to month and can exceed what was obligated. Agencies need cost controls and contract structures to fit metered spend into fixed funding (module 04).
</details>
