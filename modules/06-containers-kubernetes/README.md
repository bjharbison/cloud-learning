# 06 — Containers and Kubernetes: GKE, EKS, AKS

> **In one sentence:** you'll be able to explain Kubernetes to someone who knows Docker, compare GKE, EKS, and AKS honestly, and name the five controls that keep a cluster from becoming a cryptominer.

**Prereqs:** modules 00–05 (module 01 for containers vs VMs; module 05 for desired state and VM identity) · **Time:** ~4 hours incl. lab · **Phase:** 2

## Learning objectives

- Map your Docker and Compose experience onto Kubernetes objects.
- Draw the Kubernetes control plane and nodes in plain language, and say which parts a managed service runs for you.
- Compare GKE Autopilot vs Standard, EKS, and AKS — including what each **bills while idle**.
- Apply the security basics: **RBAC**, **workload identity**, **network policy**, **admission control**, and image supply chain.
- Recognize the main container and Kubernetes ATT&CK techniques.

## Why this matters for the target roles

- **Customer engineer / architect:** "Should we run this on GKE, Cloud Run, or VMs?" is a weekly question. Kubernetes started at Google, and GKE is a flagship Google Cloud product.
- **Cloud security:** Kubernetes has its own identity system, network model, and API — a second control plane inside the cloud's control plane. Most cluster compromises are misconfigurations.
- **CTI:** exposed kubelets and container APIs are a well-documented cryptojacking target (TeamTNT's Hildegard; Kinsing). You'll read these reports with real understanding.

---

## Concepts

### From Docker to Kubernetes: what you already know

You've run MQTT, InfluxDB, and Grafana with Docker. Here's the mapping:

| You know (Docker / Compose) | Kubernetes term | What changes |
|---|---|---|
| Image (`grafana/grafana:11`) | **Image** — same thing | Pulled from a **registry**: Artifact Registry (Google), ECR (AWS), ACR (Azure) |
| `docker run` one container | **Pod** — one or more containers sharing a network namespace and volumes | The smallest thing Kubernetes schedules |
| `restart: always` | **Deployment** (via a ReplicaSet) keeps N pods running | Self-healing, rolling updates — like the MIG in module 05 |
| Compose service name / port | **Service** — a stable virtual IP and DNS name in front of a set of pods | Pods come and go; the Service stays |
| Compose project | **Namespace** — a scope for names, policies, and permissions | Also the unit for RBAC and Pod Security labels |
| `.env` file, bind-mounted config | **ConfigMap** / **Secret** | Secrets are only base64-encoded by default — encrypt them (module 16) |
| One Docker host | A **cluster** of **nodes** (VMs) | The scheduler decides which node runs each pod |
| You, typing commands | **Controllers** reconciling **desired state** | You declare; the system converges |

**The key mental shift:** with Docker you *issue commands*. With Kubernetes you *write down what you want* (YAML), hand it to the API, and controllers keep reality matching it. You saw this in module 05 when the MIG replaced a deleted VM. Kubernetes does it for everything.

### Kubernetes architecture in plain language

```
              CONTROL PLANE  (managed for you on GKE/EKS/AKS)
   ┌──────────────────────────────────────────────────────────────┐
   │  kube-apiserver  ◄── every request goes here (kubectl, nodes) │
   │  etcd            ◄── the cluster's database of desired state  │
   │  scheduler       ◄── picks a node for each new pod            │
   │  controller-manager ◄── loops that fix drift (replicas, etc.) │
   │  cloud-controller-manager ◄── talks to the cloud (LBs, disks) │
   └───────────────────────────────▲──────────────────────────────┘
                                   │ HTTPS
   NODES (VMs in YOUR project/account/subscription; on Autopilot, Google manages them)
   ┌──────────────────────┐  ┌──────────────────────┐
   │ kubelet (node agent) │  │ kubelet              │
   │ container runtime    │  │ container runtime    │
   │ [pod][pod][pod]      │  │ [pod][pod]           │
   └──────────────────────┘  └──────────────────────┘
```

- **kube-apiserver** — the front door. Every action is an authenticated, authorized API call. It's the Kubernetes equivalent of the cloud's control-plane API.
- **etcd** — key-value store holding all cluster state, including Secrets. Whoever reads etcd reads everything.
- **scheduler** — places pods on nodes based on requested CPU/memory and constraints.
- **controller-manager** — runs reconciliation loops (keep 3 replicas, replace failed pods).
- **kubelet** — the agent on each node that starts containers and reports status. Its API is a classic attack target when exposed.

**Bridge to your OT background:** the API server plus etcd is the historian and the engineering workstation in one; controllers are the PLC logic scanning setpoint vs process value; kubelets are the field I/O. Compromise the engineering workstation and you own the plant.

### Managed Kubernetes: what the provider runs

All three run the control plane for you. The differences are in the nodes, the defaults, and the bill.

**GKE has two modes:**

- **Autopilot** — Google manages the nodes, scaling, and hardened defaults; you pay for the CPU, memory, and storage your pods **request** (pod-based billing for general-purpose workloads). Google recommends Autopilot for most workloads. New Autopilot clusters are **regional**. Autopilot blocks things like privileged pods by default, and Workload Identity Federation for GKE is **always on**.
- **Standard** — you manage node pools (machine types, scaling, upgrades windows). More control; more responsibility. Can run privileged workloads if you allow them.

**EKS:** AWS runs the control plane; you choose managed node groups, self-managed nodes, Fargate (serverless pods), or **EKS Auto Mode** (AWS manages nodes, with a per-instance management fee on top of EC2).

**AKS:** Azure runs the control plane; you manage node pools, or use **AKS Automatic**. AKS has **Free**, **Standard**, and **Premium** cluster management tiers.

### What it costs while doing nothing

Managed control planes are the classic "bills while idle" item from [`lab-safety.md`](../../reference/lab-safety.md).

| | Cluster/control-plane fee | Free allowance | Notes |
|---|---|---|---|
| **GKE** | **$0.10 per cluster per hour** (any mode); $0.60/hour on the Extended release channel during extended support | **$74.40/month credit per billing account** — covers one Autopilot or zonal Standard cluster's fee; doesn't cover compute or regional Standard clusters; doesn't roll over | Autopilot: you pay for pod requests. Standard: you pay for node VMs |
| **EKS** | **$0.10 per cluster per hour** on standard support; **$0.60** on extended support | No EKS-specific free allowance listed | Plus EC2 nodes (or Fargate); Auto Mode adds a per-instance fee |
| **AKS** | **Free tier: no cluster management fee** (no financially backed SLA; recommended under 10 nodes); Standard and Premium are paid ⚠️ hourly rates not verified this run | Free tier itself | You still pay for node VMs, disks, load balancers, public IPs |

**The extended-support trap:** both GKE and EKS charge 6× more per hour for clusters left on old Kubernetes versions past standard support. Upgrades are a cost control, not just a security one.

### Shared responsibility in managed Kubernetes

| Layer | Provider | Customer |
|---|---|---|
| Control plane availability, etcd, API server patching | ✅ | |
| Node OS patching | ✅ on Autopilot / Auto Mode / AKS Automatic; shared on Standard node pools (you schedule upgrades) | ✅ on Standard |
| **Who can call the API (cloud IAM + Kubernetes RBAC)** | | ✅ always |
| **Network policy, Services, load balancer exposure** | | ✅ always |
| Images, their vulnerabilities, their provenance | | ✅ always |
| Pod security settings, Secrets handling | | ✅ always |

> **Identity, access control, and network exposure stay the customer's job** — just as with VMs. Managed Kubernetes removes the control-plane chores, not the access decisions.

---

## Kubernetes security basics (the five controls)

### 1. Access to the API: cloud IAM + Kubernetes RBAC

Two layers decide who can do what:

- **Cloud IAM** gets you to the cluster. Google IAM roles on the project; EKS **access entries** map IAM principals to Kubernetes permissions (AWS calls them the best way to grant API access, replacing the legacy `aws-auth` ConfigMap); AKS integrates **Microsoft Entra ID** with Kubernetes RBAC or Azure RBAC.
- **Kubernetes RBAC** decides what you can do inside: **Roles** (namespace-scoped) and **ClusterRoles** (cluster-wide) list verbs on resources; **RoleBindings** / **ClusterRoleBindings** grant them to users, groups, or **ServiceAccounts**.

Rules of thumb: no human gets `cluster-admin` day to day; bind roles to groups; namespace-scope everything you can; audit who can read Secrets or `exec` into pods.

**Bridge:** RBAC is need-to-know inside the compartment. Cloud IAM gets you into the SCIF; RBAC decides which safes you can open.

### 2. Workload identity: pods without keys

Pods often need to call cloud APIs (read a bucket, write a queue). The bad old way: put a service-account key in a Secret. The good way: let the pod's Kubernetes **ServiceAccount** be exchanged for a short-lived cloud identity.

| | Google Cloud | AWS | Azure |
|---|---|---|---|
| Feature | **Workload Identity Federation for GKE** | **EKS Pod Identity** (or the older **IRSA**) | **Microsoft Entra Workload ID** |
| How | KSA becomes an IAM principal in pool `PROJECT_ID.svc.id.goog`; GKE metadata server intercepts metadata requests | Associate an IAM role with a KSA; an agent DaemonSet hands out credentials per node | Cluster acts as an OIDC issuer; a federated identity credential on a managed identity trusts the KSA |
| Default | **Always on** in Autopilot; opt-in on Standard | Opt-in (agent add-on; built into Auto Mode) | Preconfigured in AKS Automatic; opt-in on Standard |
| What it prevents | Pods using the **node's** service account | Pods using the node's instance profile | Stored client secrets |

Why it matters: without it, every pod on a node can use the node's identity — module 05's metadata-server problem, multiplied by every pod. AWS adds a useful reminder in its own docs: containers are not a security boundary, and Pod Identity doesn't change that.

### 3. Network policy: default allow → default deny

**By default, every pod can talk to every other pod in the cluster.** A Kubernetes **NetworkPolicy** restricts that, but only if the cluster's network plugin (**CNI**) enforces it.

- **GKE:** **Dataplane V2** (eBPF/Cilium-based) enforces NetworkPolicy "always on" and is enabled by default on new Autopilot clusters, with built-in network policy logging.
- **EKS:** the Amazon VPC CNI supports network policy, but you must **enable** it (`enableNetworkPolicy`). A "strict" mode starts new pods default-deny.
- **AKS:** off unless you choose an engine: **Azure CNI Powered by Cilium** (recommended), Azure Network Policy Manager (being retired on Linux by September 30, 2028), or Calico.

**The trap:** a NetworkPolicy object on a cluster that doesn't enforce it does nothing — silently.

**Bridge:** this is your VLAN segmentation on OPNsense, but at pod granularity and defined by labels instead of IP ranges.

### 4. Admission control: stop bad pods at the door

**Admission controllers** inspect every create/update request after authentication and before it's stored.

- **Pod Security Admission** (built into Kubernetes; stable since v1.25, replacing PodSecurityPolicy): label a namespace with a level — `privileged`, `baseline`, or `restricted` — in a mode — `enforce`, `audit`, or `warn`. `restricted` blocks root, privilege escalation, host namespaces, and more.
- **Policy engines** for custom rules: open-source OPA Gatekeeper and Kyverno; GKE Policy Controller and **Binary Authorization** (only deploy images that are signed/attested); Azure Policy for AKS (⚠️ AWS-native equivalent not verified this run; EKS users commonly run Gatekeeper or Kyverno).

### 5. Image supply chain

- Pull only from registries you control; scan images; pin by digest, not `latest`.
- Sign images and enforce signatures at admission (Binary Authorization and similar).
- Keep images small and non-root.

---

## Text diagram — a hardened cluster on Google Cloud

```
 Developer ──(Google identity + MFA)──► GKE API server (IAM + RBAC check, audit-logged)
                                            │ admission: Pod Security "restricted", Binary Authorization
                                            ▼
  namespace: mission-app  (PSA label: enforce=restricted)
  ┌────────────────────────────────────────────────────────────────┐
  │ Deployment "api" (3 replicas, non-root, read-only FS)            │
  │   KSA "api-sa" ──Workload Identity──► IAM: roles/storage.objectViewer on ONE bucket
  │ NetworkPolicy: default-deny ingress; allow from app=frontend :8080│
  └────────────────────────────────────────────────────────────────┘
  Images: Artifact Registry (scanned, signed) — no Docker Hub in prod
  Nodes: Autopilot-managed, private (no external IPs)
```

## Google Cloud vs AWS vs Azure

| Capability | Google Cloud (GKE) | AWS (EKS) | Azure (AKS) | Notable difference |
|---|---|---|---|---|
| Fully managed nodes | **Autopilot** (pod-based billing) | **EKS Auto Mode** (EC2 + per-instance fee); Fargate | **AKS Automatic** | Autopilot bills by pod request, not node |
| Self-managed node pools | Standard mode | Managed node groups / self-managed | Node pools | |
| Control-plane fee | $0.10/hr; $74.40/month free credit for one Autopilot or zonal cluster | $0.10/hr standard; $0.60/hr extended | Free tier: none; Standard/Premium paid | AKS Free tier has no SLA |
| Extended/LTS support | Extended channel (+$0.50/hr) | Extended support (+$0.50/hr) | Premium tier with LTS (24 months) | |
| API access identity | Google IAM + RBAC | IAM via **access entries** + RBAC | Entra ID + Kubernetes RBAC or Azure RBAC | |
| Workload identity | Workload Identity Federation for GKE (always on in Autopilot) | EKS Pod Identity / IRSA | Entra Workload ID | |
| Network policy | Dataplane V2, always on (default for new Autopilot) | VPC CNI, **must enable** | Cilium / NPM / Calico, **must choose** | Only GKE enforces out of the box |
| Control-plane logs | Cloud Audit Logs (⚠️ default log scope not re-verified this run) | **Off by default**; enable each type (api, audit, authenticator, controllerManager, scheduler) to CloudWatch | Diagnostic settings (⚠️ not verified this run) | EKS audit logs cost CloudWatch ingestion |
| Registry | Artifact Registry | ECR | ACR | |

## Administer and monitor it

- **`kubectl`** is the universal tool: `get`, `describe`, `logs`, `apply`, `auth can-i`.
- **Upgrades** are routine work: release channels (GKE), version support windows (EKS, AKS). Falling behind costs money (extended support) and leaves CVEs open.
- **Audit logs:** Kubernetes API audit events go to Cloud Logging on GKE, CloudWatch (if enabled) on EKS, and Azure Monitor on AKS. These are the logs a detection engineer needs (module 22).
- **Cost:** Autopilot shows pod-level cost; on node-based clusters, idle node capacity is waste.

## Security angle

Top misconfigurations:

1. **Exposed API server or kubelet** with anonymous access → instant compromise (Hildegard's entry point).
2. **`cluster-admin` everywhere** and broad `ClusterRoleBindings` to service accounts.
3. **No workload identity** — pods using node credentials or long-lived keys in Secrets.
4. **No network policy enforcement** — flat pod network; one compromised pod reaches everything.
5. **Privileged pods / host mounts** — collapse the container boundary (module 01's warning about the Docker socket).
6. **Unscanned images from public registries**, tagged `latest`.
7. **Services of type LoadBalancer** created casually — a public endpoint (and a bill) per Service.

**Shared responsibility:** the provider runs and patches the control plane. **RBAC, workload identity, network policy, admission rules, image choice, and Service exposure are always the customer's.**

## Threat intel angle

- **T1610 Deploy Container** — attackers with API access launch their own containers (usually miners).
- **T1609 Container Administration Command** — `kubectl exec` or kubelet API calls to run commands in existing containers.
- **T1611 Escape to Host** — from a privileged pod or host mount to the node (module 01).
- **T1613 Container and Resource Discovery** — enumerate pods, Secrets, service accounts after access.
- **T1552.007 Unsecured Credentials: Container API** — harvesting credentials through the Kubernetes or Docker API.
- **T1496.001 Compute Hijacking** — the usual end state.

**Public reporting worth reading:** MITRE's entries for **Hildegard** (S0601; targets misconfigured kubelets allowing anonymous access; attributed to TeamTNT; first seen January 2021) and **Kinsing** (S0599; reached victims through an exposed Docker daemon API; cryptomining and SSH-based spread).

**Bridge to your CTI work:** the API server is the adversary's objective, not the containers. Collection priority: Kubernetes audit logs (who called `create pod`, `exec`, `get secrets`), then cloud audit logs for identity abuse.

## Public sector notes

- **DoD Enterprise DevSecOps reference designs** include a CNCF Kubernetes reference design (DoD CIO, 2021) — Kubernetes is the expected platform for many defense software factories.
- **Iron Bank** is Platform One's repository of 1,000+ hardened container images for DoD, with vulnerability and compliance assessments to support ATOs. It's free but requires an account; anonymous pulls aren't allowed.
- In disconnected environments (module 28), clusters can't pull from public registries at all — image mirroring and signing become mandatory, not optional.
- Managed Kubernetes availability and authorization levels differ by government environment; check before designing (modules 26–27).

## Key takeaways

- Kubernetes = an API server + database of desired state + controllers that reconcile. You declare; it converges.
- Docker concepts map cleanly: container → pod, `restart: always` → Deployment, service name → Service, project → namespace.
- GKE Autopilot manages nodes and bills by pod request; Standard gives control. EKS and AKS have their own managed-node modes.
- **Control planes bill while idle:** GKE and EKS $0.10/hr (6× on extended support); AKS Free tier has no fee. GKE's $74.40/month credit covers one Autopilot or zonal cluster's fee.
- Five controls: RBAC, workload identity, network policy (enforced!), admission control, image supply chain.
- Only GKE enforces NetworkPolicy out of the box; EKS and AKS need it enabled.
- The API server is the crown jewel. RBAC, network policy, and exposure are **always the customer's**.

## Sources

- [Kubernetes — Components](https://kubernetes.io/docs/concepts/overview/components/) and [Cluster architecture](https://kubernetes.io/docs/concepts/architecture/)
- [Kubernetes — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/) and [v1.25: Pod Security Admission stable](https://kubernetes.io/blog/2022/08/25/pod-security-admission-stable/)
- [Google Cloud — GKE pricing](https://cloud.google.com/kubernetes-engine/pricing)
- [Google Cloud — About GKE modes of operation](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode)
- [Google Cloud — GKE Autopilot overview](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Google Cloud — Workload Identity Federation for GKE](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Google Cloud — GKE Dataplane V2](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/dataplane-v2)
- [Google Cloud — Configure GKE node service accounts](https://docs.cloud.google.com/kubernetes-engine/security/configure-node-service-accounts)
- [Google Cloud — Automatically created firewall rules](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/firewall-rules)
- [AWS — Amazon EKS pricing](https://aws.amazon.com/eks/pricing/)
- [AWS — EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [AWS — EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)
- [AWS — Restrict pod traffic with network policies (VPC CNI)](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [AWS — Send EKS control plane logs to CloudWatch](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
- [Microsoft — AKS Free, Standard, and Premium tiers](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers)
- [Microsoft — Entra Workload ID on AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [Microsoft — Network policies in AKS](https://learn.microsoft.com/en-us/azure/aks/use-network-policies)
- [Iron Bank FAQ (Platform One)](https://docs-ironbank.dso.mil/faq/)
- [DoD CIO — DevSecOps Reference Design: CNCF Kubernetes (PDF, 2021)](https://dodcio.defense.gov/Portals/0/Documents/Library/DoD%20Enterprise%20DevSecOps%20Reference%20Design%20-%20CNCF%20Kubernetes%20w-DD1910_cleared_20211022.pdf)
- [MITRE ATT&CK — T1610](https://attack.mitre.org/techniques/T1610/), [T1609](https://attack.mitre.org/techniques/T1609/), [T1613](https://attack.mitre.org/techniques/T1613/), [T1611](https://attack.mitre.org/techniques/T1611/), [T1552.007](https://attack.mitre.org/techniques/T1552/007/), [Hildegard S0601](https://attack.mitre.org/software/S0601/), [Kinsing S0599](https://attack.mitre.org/software/S0599/)

Verified: 2026-10-24
