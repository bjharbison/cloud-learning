# Glossary

Plain-language definition first, then how practitioners use the term. Alphabetical. Modules append as they're built.

**Control plane / data plane** — The control plane is where you *manage* resources (create a VM, change a policy) — almost always API calls. The data plane is where the resource *does its work* (traffic through a VM, reads from a bucket). Logging and permissions often differ between the two.

**IaaS / PaaS / SaaS** — How much of the stack the provider runs for you. IaaS: they run hardware and virtualization; you run the OS up. PaaS: they also run the OS and runtime; you bring code and data. SaaS: they run the whole application; you manage users and data. (Module 01)

**Least privilege** — Give each identity only the permissions it needs, for only as long as it needs them. The cloud version of need-to-know.

**NIST SP 800-145** — The U.S. government's definition of cloud computing: five essential characteristics (on-demand self-service, broad network access, resource pooling, rapid elasticity, measured service), three service models, four deployment models. Citing it signals fluency with government customers. (Module 01)

**Region / zone** — A region is a geographic area containing several isolated data-center groups called zones (AWS: Availability Zones). Spreading across zones protects against a single facility failing; spreading across regions protects against a regional outage. (Module 02)

**Shared responsibility model** — The provider secures the cloud itself (facilities, hardware, hypervisor); the customer secures what they put in it. Identity, access control, firewall rules, network configuration, and data are always the customer's job. (Module 01)

**VPC (Virtual Private Cloud)** — A private, software-defined network inside a cloud provider, where you define IP ranges, subnets, routes, and firewall rules. Closest homelab analogy: your OPNsense-managed VLANs — but defined entirely by API. (Module 10)
