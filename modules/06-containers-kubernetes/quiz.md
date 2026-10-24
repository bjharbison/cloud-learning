# 06 Quiz — Containers and Kubernetes

1. Map these Docker/Compose ideas to Kubernetes: a running container, `restart: always` with 3 copies, a Compose service name, a Compose project.
<details><summary>Answer</summary>

Pod (one or more containers); Deployment with `replicas: 3`; Service (stable virtual IP + DNS name); Namespace.
</details>

2. Name the control-plane components and what each does, in one line each.
<details><summary>Answer</summary>

kube-apiserver: the front door; every request is an authenticated API call. etcd: stores all cluster state (including Secrets). Scheduler: picks a node for each pod. Controller-manager: reconciliation loops that fix drift. (Cloud-controller-manager: talks to the cloud for load balancers, disks.) On nodes, the kubelet runs pods.
</details>

3. GKE Autopilot vs Standard: who manages nodes, and how are you billed?
<details><summary>Answer</summary>

Autopilot: Google manages nodes; general-purpose pods are billed for the CPU, memory, and ephemeral storage they **request**. Standard: you manage node pools and pay for the node VMs. Both pay the $0.10/hour cluster fee (offset by the $74.40/month free-tier credit for one Autopilot or zonal cluster).
</details>

4. Which managed Kubernetes service has no control-plane fee in its lowest tier, and what do you give up?
<details><summary>Answer</summary>

AKS Free tier: no cluster management fee, but no financially backed SLA (Microsoft recommends it for dev/test and clusters under 10 nodes). You still pay for nodes, disks, and networking.
</details>

5. Why do GKE and EKS charge $0.60/hour for some clusters?
<details><summary>Answer</summary>

Extended support: clusters on Kubernetes versions past standard support pay an extra $0.50/hour. Keeping clusters upgraded is a cost control as well as a security one.
</details>

6. Spot the problem: "We wrote NetworkPolicies for every namespace on our new EKS cluster, so pods are segmented."
<details><summary>Answer</summary>

NetworkPolicy is only enforced if the CNI enforces it. On EKS the VPC CNI's network policy support must be explicitly enabled (`enableNetworkPolicy`). Without it the policies are silently ignored. (AKS similarly needs an engine chosen; GKE Dataplane V2 enforces by default.)
</details>

7. What problem does workload identity solve? Name it on each cloud.
<details><summary>Answer</summary>

It gives pods short-lived cloud credentials tied to their Kubernetes ServiceAccount, so you don't store keys in Secrets and pods don't borrow the node's identity. Google: Workload Identity Federation for GKE (always on in Autopilot). AWS: EKS Pod Identity (or IRSA). Azure: Microsoft Entra Workload ID.
</details>

8. A namespace is labeled `pod-security.kubernetes.io/enforce=restricted`. Someone submits a pod with `privileged: true`. What happens, and which component does it?
<details><summary>Answer</summary>

The API server's Pod Security Admission controller rejects the request before it's stored, listing the violations. Nothing is created. (`audit` or `warn` modes would allow it but record or warn.)
</details>

9. You run `kubectl auth can-i get secrets -n prod --as=system:serviceaccount:prod:ci-bot` and get `yes`. Why should a security reviewer care?
<details><summary>Answer</summary>

The CI bot's identity can read every Secret in `prod` — credentials, API keys, tokens. If the CI system is compromised, so are all of them. Scope its Role to only what it deploys, and never grant Secret reads it doesn't need.
</details>

10. In EKS, what replaced the legacy `aws-auth` ConfigMap for granting IAM principals access to the Kubernetes API?
<details><summary>Answer</summary>

EKS access entries, which associate an IAM principal with Kubernetes permissions (via AWS-managed access policies or Kubernetes groups) through the EKS API.
</details>

11. Scenario: an agency wants to run a containerized analytics app on Google Cloud with minimal ops staff and strict segmentation. Recommend a setup.
<details><summary>Answer</summary>

GKE Autopilot (Google manages nodes; hardened defaults; Workload Identity always on; Dataplane V2 enforcing NetworkPolicy). Least-privilege node service account; private nodes; images from Artifact Registry, scanned and signed with Binary Authorization; namespaces with Pod Security `restricted`; default-deny NetworkPolicies plus explicit allows; RBAC bound to groups; audit logs to the SIEM. If the app is stateless and request-driven, also consider Cloud Run (module 07).
</details>

12. Which public malware families targeted exposed kubelets and Docker APIs, and which ATT&CK techniques describe what they did?
<details><summary>Answer</summary>

Hildegard (S0601, TeamTNT; misconfigured kubelets with anonymous access) and Kinsing (S0599; exposed Docker daemon API). Techniques: T1610 Deploy Container, T1609 Container Administration Command, T1611 Escape to Host, and T1496.001 Compute Hijacking for the cryptomining.
</details>
