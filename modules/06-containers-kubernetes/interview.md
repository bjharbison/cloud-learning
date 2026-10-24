# 06 Interview Prep — Containers and Kubernetes

## Likely questions

### Q1. "Explain Kubernetes to me like I've only used Docker."

**Answer outline:**
- Docker runs containers on one host when you tell it to. Kubernetes runs them across many hosts and keeps them matching a declared desired state.
- Pod ≈ container; Deployment ≈ "keep N copies running and roll updates"; Service ≈ stable name in front of changing pods; Namespace ≈ a project boundary for names, permissions, and policy.
- Control plane: API server + etcd + scheduler + controllers. Nodes: kubelet + runtime.
- Managed services run the control plane for you.

**Strong signal:** "you declare, controllers reconcile" — and connecting it to MIGs/autohealing.

### Q2. "GKE Autopilot or Standard? And how does that compare to EKS and AKS?"

**Answer outline:**
- Autopilot: Google manages nodes, hardened defaults (no privileged pods, Workload Identity always on, Dataplane V2), billed by pod requests. Google recommends it for most workloads.
- Standard: when you need node-level control or privileged workloads.
- EKS: control plane managed; nodes via managed node groups, Fargate, or Auto Mode; network policy and Pod Identity are add-ons you enable.
- AKS: Free/Standard/Premium tiers; AKS Automatic; network policy engine must be chosen.

**Strong signal:** knowing which security features are on by default vs opt-in on each.
**Avoid:** "they're all the same Kubernetes" (true for the API, false for defaults and ops).

### Q3. "How do you secure a Kubernetes cluster?"

**Answer outline (the five controls):**
1. API access: cloud IAM + RBAC; no daily cluster-admin; groups not individuals; audit logs on.
2. Workload identity: no keys in Secrets; pods don't use the node identity.
3. Network policy: default-deny + explicit allows; confirm the CNI enforces it.
4. Admission control: Pod Security `restricted`; policy engine; signed images.
5. Supply chain: trusted registry, scanning, pin by digest.
- Plus: private nodes/control plane where feasible; keep versions current.

**Strong signal:** naming the trap that NetworkPolicy objects are ignored without an enforcing CNI.

### Q4. "What does the threat look like?"

**Answer outline:**
- Exposed kubelets and Docker APIs → deploy miners (Hildegard, Kinsing; T1610, T1496.001).
- Stolen kubeconfig (kubectl's credentials file) or cloud credentials → `kubectl exec`, read Secrets (T1609, T1552.007).
- Privileged pods → escape to node → node identity → cloud (T1611, then T1552.005).
- Detection: Kubernetes audit logs for `create pod`, `exec`, `get secrets`, new ClusterRoleBindings.

### Q5. "When would you *not* use Kubernetes?"

**Answer outline:**
- Small, stateless, request-driven services with no platform team: Cloud Run / serverless (module 07).
- Lift-and-shift apps that need a full OS: VMs (module 05).
- Kubernetes pays off with many services, portability needs, or an existing platform team — and it has a real operational cost.

## 60-second executive explanation

"Containers package an application with everything it needs so it runs the same everywhere. Kubernetes is the system that runs thousands of those containers across many servers and automatically restarts or moves them when something fails. Google invented the technology behind it and offers it as a managed service, so Google runs the brain of the system and we focus on the applications. The security work is ours: deciding who can change the system, which applications can talk to each other, and which software is allowed to run at all. Done well, it gives a mission team the ability to ship updates quickly without opening new risk each time."

## Whiteboard prompt

Draw a GKE Autopilot cluster: control plane (Google-managed) and nodes. Inside, one namespace with a Deployment, Service, and NetworkPolicies (default-deny + allow from frontend). Show the KSA → Workload Identity → IAM role on one bucket. Show the admission path: Pod Security restricted + Binary Authorization. Then draw the attacker's path from an exposed kubelet to a miner, and mark which control breaks each step.

## What you can honestly claim

- **After reading + quiz:** "I've studied Kubernetes architecture and security — RBAC, workload identity, network policy, and admission control — and how GKE, EKS, and AKS differ in defaults and pricing."
- **After completing the lab:** "In a personal lab I deployed workloads to a local Kubernetes cluster and to GKE Autopilot, enforced Pod Security standards and namespace-scoped RBAC, and used NetworkPolicies to implement default-deny segmentation." That's accurate for a one-hour lab cluster — say "lab," not "environment I managed."
- **Still requires (cert / production experience / clearance):** operating production clusters, upgrades and incident response at scale, building a software factory, or working with Iron Bank/Platform One in a DoD program. Don't claim "Kubernetes administrator." The CNCF's CKA/CKAD/CKS exams and Google's Associate Cloud Engineer are claimable milestones (⚠️ CNCF exam details not verified this run).
