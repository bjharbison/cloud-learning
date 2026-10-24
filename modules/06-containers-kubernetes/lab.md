# 06 Lab — From Docker to Kubernetes, then lock it down

**Cost:** Part A1 is **$0** — a local Kubernetes cluster (**kind**, "Kubernetes in Docker") running inside Cloud Shell. Part A2 is a **GKE Autopilot** cluster for **about an hour**: the $0.10/hour cluster fee is covered by GKE's **$74.40/month free-tier credit** (one Autopilot or zonal cluster per billing account), and you pay only for the CPU/memory your three small pods request plus the nodes' external IPs — expect well under $1, paid from trial credit. ⚠️ That estimate isn't from a verified price sheet; check Billing → Reports filtered by `lab=06` the next day. **Never leave the GKE cluster running overnight.** AWS and Azure parts are read-only. · **Time:** 2–2.5 hours · **Clouds:** GCP (required), AWS and Azure (read-only)

> **Why two parts?** Managed control planes bill while idle (README). kind gives you a real Kubernetes API for free to learn the objects and security controls. GKE Autopilot then shows what's different when Google runs it — including network policy that's actually enforced.

## Goal

1. Translate a Docker mental model into Kubernetes objects: Deployment, Pod, Service, Namespace.
2. Watch desired state reconcile (delete a pod; it comes back).
3. Block a privileged pod with **Pod Security Admission**.
4. Prove least privilege with **RBAC** (`kubectl auth can-i`).
5. On GKE Autopilot: confirm **Workload Identity** is on, and use a **NetworkPolicy** to cut off traffic — then allow only what's needed.

## Prerequisites

- Modules 00–05 done; budget alerts active.
- Cloud Shell open. It includes Docker (you used it in module 01).
- For Part A2: `gcloud config list` shows your lab project.

Optional alternative for A1: run it on your homelab Docker host instead of Cloud Shell — same commands.

---

## Part A1 — Kubernetes locally with kind ($0)

### A1.1 Install kind and check kubectl (CLI)

From the official kind quick start (check the [releases page](https://kind.sigs.k8s.io/docs/user/quick-start/) for a newer version):

```bash
mkdir -p ~/.local/bin && export PATH="$HOME/.local/bin:$PATH"
[ $(uname -m) = x86_64 ] && curl -Lo ~/.local/bin/kind https://kind.sigs.k8s.io/dl/v0.33.0/kind-linux-amd64
chmod +x ~/.local/bin/kind
kind version

kubectl version --client || {
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x kubectl && mv kubectl ~/.local/bin/
  kubectl version --client
}
```

### A1.2 Create a cluster — and notice it's a container

```bash
kind create cluster --name lab06
kubectl get nodes -o wide
docker ps --format "table {{.Names}}\t{{.Image}}"
```

**What you should see:** one node, `lab06-control-plane`. And `docker ps` shows that node is itself a **container**. kind runs the whole cluster — API server, etcd, scheduler, kubelet — inside one Docker container. In GKE/EKS/AKS those pieces are spread across managed infrastructure and VMs, but the API you're talking to is the same.

```bash
kubectl get pods -n kube-system
```

Find `etcd-…`, `kube-apiserver-…`, `kube-scheduler-…`, and `kube-controller-manager-…` — the control plane from the README diagram. On managed clusters you won't see these; the provider hides them.

### A1.3 A namespace with Pod Security "restricted"

```bash
kubectl create namespace lab06
kubectl label namespace lab06 \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted
kubectl get namespace lab06 --show-labels
```

Now try to run a privileged container — the kind of pod that collapses the container boundary (module 01, ATT&CK T1611):

```bash
kubectl run bad --image=nginx:1.27 -n lab06 --privileged
```

**What you should see:** the API server **refuses** it, listing the violations (`privileged`, `allowPrivilegeEscalation`, `runAsNonRoot`, `seccompProfile`, `capabilities`). Nothing was created. That's admission control.

### A1.4 A compliant Deployment and Service

Write the manifest:

```bash
cat > ~/lab06-app.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello
  namespace: lab06
  labels: {app: hello, lab: "06"}
spec:
  replicas: 2
  selector:
    matchLabels: {app: hello}
  template:
    metadata:
      labels: {app: hello, lab: "06"}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile: {type: RuntimeDefault}
      containers:
      - name: hello
        image: us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0
        ports: [{containerPort: 8080}]
        resources:
          requests: {cpu: 250m, memory: 512Mi}
          limits:   {cpu: 250m, memory: 512Mi}
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities: {drop: ["ALL"]}
---
apiVersion: v1
kind: Service
metadata:
  name: hello
  namespace: lab06
spec:
  selector: {app: hello}
  ports: [{port: 80, targetPort: 8080}]
EOF
kubectl apply -f ~/lab06-app.yaml
kubectl get deploy,rs,pods,svc -n lab06
```

The image is Google's sample `hello-app` from Artifact Registry. Map it to Compose: `image:` is the same; `replicas: 2` replaces `restart: always` plus "run two of them"; the Service is the stable name other containers use.

Test it through a port-forward (nothing is exposed outside Cloud Shell):

```bash
kubectl port-forward -n lab06 svc/hello 8080:80 >/dev/null 2>&1 &
sleep 3; curl -s localhost:8080; kill %1
```

### A1.5 Desired state: delete a pod

```bash
kubectl delete pod -n lab06 $(kubectl get pods -n lab06 -l app=hello -o name | head -1 | cut -d/ -f2)
kubectl get pods -n lab06 -w
```

Press `Ctrl+C` after a replacement appears. Same lesson as the MIG in module 05: you declared two; the controller restores two.

### A1.6 RBAC: a read-only identity

```bash
kubectl create serviceaccount viewer -n lab06
kubectl create role pod-reader -n lab06 --verb=get,list,watch --resource=pods
kubectl create rolebinding viewer-reads-pods -n lab06 --role=pod-reader --serviceaccount=lab06:viewer

for check in "list pods" "delete pods" "get secrets" "create deployments"; do
  echo -n "$check: "
  kubectl auth can-i $check -n lab06 --as=system:serviceaccount:lab06:viewer
done
echo -n "list pods in kube-system: "
kubectl auth can-i list pods -n kube-system --as=system:serviceaccount:lab06:viewer
```

**What you should see:** `yes` only for `list pods` in `lab06`; `no` for everything else. That's need-to-know, namespace-scoped.

### A1.7 Delete the local cluster

```bash
kind delete cluster --name lab06
docker ps    # the lab06-control-plane container is gone
```

---

## Part A2 — GKE Autopilot for one hour

> Start a timer for 60 minutes when you run the create command. Cleanup is at the end of this section **and** in the Cleanup section.

### A2.1 Network and a least-privilege node identity (CLI)

```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud services enable container.googleapis.com

gcloud compute networks create lab06-net --subnet-mode=custom
gcloud compute networks subnets create lab06-subnet \
  --network=lab06-net --region=us-central1 --range=10.60.0.0/20

gcloud iam service-accounts create lab06-nodes --display-name="lab06 GKE nodes"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:lab06-nodes@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.defaultNodeServiceAccount"
```

Why a custom node service account? GKE's docs call `roles/container.defaultNodeServiceAccount` the minimum role for nodes. The alternative, the Compute Engine default service account, may carry Editor (module 05) — or, in organizations created after May 2024, may lack the permissions GKE needs.

Why this network? It has **no firewall rules of its own**, so the only ingress allowed is what GKE creates for the cluster — and Google documents that those rules admit traffic from the control plane, node, and pod ranges, not from the internet. (Production clusters would also use **private nodes**; we skip them here only because private nodes can't pull the public `busybox` image below without Cloud NAT, which costs money.)

### A2.2 Create the Autopilot cluster (console, then CLI)

Console: **Kubernetes Engine → Clusters → Create → Autopilot** → name `lab06-ap`, region `us-central1` → **Networking**: network `lab06-net`, subnet `lab06-subnet` → **Advanced → Security**: service account `lab06-nodes` → **Metadata**: label `lab=06` → Create.

CLI (either, not both):

```bash
gcloud container clusters create-auto lab06-ap \
  --location=us-central1 \
  --network=lab06-net --subnetwork=lab06-subnet \
  --service-account=lab06-nodes@$PROJECT_ID.iam.gserviceaccount.com \
  --labels=lab=06
```

This takes roughly 5–10 minutes. If creation fails with an error about the subnet's secondary ranges or permissions, read the message carefully, fix that one thing, and retry — don't fall back to the `default` network. Then:

```bash
gcloud container clusters get-credentials lab06-ap --location=us-central1
kubectl get nodes
gcloud container clusters describe lab06-ap --location=us-central1 \
  --format="yaml(autopilot,workloadIdentityConfig,networkConfig.datapathProvider)"
```

**What you should see:** `autopilot: enabled: true`; a `workloadPool` of `PROJECT_ID.svc.id.goog` (Workload Identity Federation — always on in Autopilot); and `datapathProvider: ADVANCED_DATAPATH` (that's Dataplane V2, which enforces NetworkPolicy). There may be zero nodes until you deploy something — Autopilot creates nodes for your pods.

> **Public control-plane endpoint:** Google documents that new Autopilot clusters have a publicly accessible IP. Anyone on the internet can reach the API server's address, but every request still needs a valid Google identity plus IAM and RBAC permissions. Production clusters narrow this with authorized networks, a private endpoint, or the DNS-based endpoint — remember the README's misconfiguration #1.

Also notice what you **can't** see:

```bash
kubectl get pods -n kube-system | grep -E "apiserver|etcd" || echo "no control-plane pods visible — Google runs them"
```

### A2.3 Same app, managed cluster

```bash
kubectl create namespace lab06
kubectl label namespace lab06 pod-security.kubernetes.io/enforce=restricted
kubectl apply -f ~/lab06-app.yaml
kubectl get pods -n lab06 -w       # Ctrl+C when both are Running (first time can take a few minutes)
```

If Cloud Shell restarted and `~/lab06-app.yaml` is gone, recreate it from A1.4.

Add a client pod (also restricted-compliant) to test traffic from inside the cluster:

```bash
cat > ~/lab06-client.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: client
  namespace: lab06
  labels: {lab: "06"}
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile: {type: RuntimeDefault}
  containers:
  - name: client
    image: busybox:1.36
    command: ["sleep", "3600"]
    resources:
      requests: {cpu: 250m, memory: 512Mi}
      limits:   {cpu: 250m, memory: 512Mi}
    securityContext:
      allowPrivilegeEscalation: false
      capabilities: {drop: ["ALL"]}
EOF
kubectl apply -f ~/lab06-client.yaml
kubectl wait -n lab06 --for=condition=Ready pod/client --timeout=300s
kubectl exec -n lab06 client -- wget -qO- -T 5 http://hello
```

**What you should see:** the hello-app response. By default, any pod can reach any pod.

### A2.4 Network policy: deny, then allow only what's needed

Default-deny all ingress in the namespace:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny-ingress, namespace: lab06}
spec:
  podSelector: {}
  policyTypes: [Ingress]
EOF
sleep 10
kubectl exec -n lab06 client -- wget -qO- -T 5 http://hello || echo "BLOCKED (expected)"
```

Now allow only pods labeled `role=frontend` to reach `app=hello` on 8080:

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: allow-frontend-to-hello, namespace: lab06}
spec:
  podSelector: {matchLabels: {app: hello}}
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector: {matchLabels: {role: frontend}}
    ports: [{port: 8080, protocol: TCP}]
EOF
kubectl exec -n lab06 client -- wget -qO- -T 5 http://hello || echo "still blocked — client isn't a frontend yet"
kubectl label pod client -n lab06 role=frontend
sleep 10
kubectl exec -n lab06 client -- wget -qO- -T 5 http://hello
```

**What you should see:** blocked → still blocked → allowed once the client carries the right label. Segmentation by **identity labels**, not IP addresses — like OPNsense rules written against aliases that follow the device.

> **Why A1 didn't do this:** a NetworkPolicy only works if the cluster's network plugin enforces it. GKE Dataplane V2 does, always. Whether kind's default plugin does depends on its version — ⚠️ not verified for kind v0.33.0 this run. If you're curious, repeat A2.4 on kind: if traffic isn't blocked, you've just seen the README's "silent no-op" trap first-hand.

### A2.5 Delete the cluster now

```bash
gcloud container clusters delete lab06-ap --location=us-central1 --quiet
```

Deletion takes several minutes. Continue with Parts B and C while it runs, then do the **Cleanup** checks.

---

## Part B — AWS (read-only, $0)

EKS has no free control plane ($0.10/hour per cluster), so look, don't build. In CloudShell:

```bash
aws eks list-clusters                          # expect an empty list
aws eks describe-addon-versions --addon-name vpc-cni \
  --query "addons[0].addonVersions[0].addonVersion" --output text
aws eks describe-addon-versions --addon-name eks-pod-identity-agent \
  --query "addons[0].addonVersions[0].addonVersion" --output text
```

**Notice:** network policy (VPC CNI) and Pod Identity are **add-ons** you choose to install and configure. On GKE Autopilot both equivalents were on before you asked.

## Part C — Azure (read-only, $0)

In Azure Cloud Shell:

```bash
az aks get-versions --location eastus --output table
az aks list -o table                            # expect empty
```

Then read the `az aks create` flags for the security features from the README:

```bash
az aks create --help | grep -E -- "--tier|--network-policy|--enable-oidc-issuer|--enable-workload-identity"
```

**Notice:** `--tier free` (no management fee), `--network-policy` (off unless you pick an engine), and `--enable-oidc-issuer --enable-workload-identity` (Workload ID is opt-in on Standard AKS).

---

## Verify it worked

| Check | Expected |
|---|---|
| Privileged pod in restricted namespace (A1.3) | Rejected by the API server |
| Deleted pod (A1.5) | Replaced automatically |
| `kubectl auth can-i` (A1.6) | `yes` only for `list pods` in `lab06` |
| Autopilot describe (A2.2) | Autopilot on; `workloadPool` set; Dataplane V2 |
| NetworkPolicy (A2.4) | Blocked by default-deny; allowed only with `role=frontend` |

## What to notice (reflection questions)

1. List each Kubernetes object you created and its Docker/Compose equivalent. Which one has no Docker equivalent at all? (NetworkPolicy, RBAC.)
2. On kind you could see `etcd` and `kube-apiserver` pods; on GKE you couldn't. What does that tell you about the shared-responsibility line?
3. Your app pods had no cloud permissions. If they needed to read one Cloud Storage bucket, what would you bind, and to what? (A Kubernetes ServiceAccount → an IAM role on that bucket via Workload Identity Federation.)
4. Why is `kubectl auth can-i --as=...` a useful habit for a security reviewer?
5. You deleted the cluster. Which items in this lab would still have billed if you hadn't?

## Cleanup

**kind** (if not already done):

```bash
kind delete cluster --name lab06 2>/dev/null; kind get clusters     # expect "No kind clusters found."
rm -f ~/lab06-app.yaml ~/lab06-client.yaml
```

**Google Cloud** — make sure the cluster is fully gone before deleting the network:

```bash
gcloud container clusters list                                   # expect no lab06-ap
gcloud container clusters delete lab06-ap --location=us-central1 --quiet 2>/dev/null || true

gcloud compute firewall-rules list --filter="network:lab06-net" --format="value(name)"
# If any gke-lab06-ap-* rules remain after the cluster is gone, delete them:
# gcloud compute firewall-rules delete RULE_NAME --quiet

gcloud compute networks subnets delete lab06-subnet --region=us-central1 --quiet
gcloud compute networks delete lab06-net --quiet

gcloud projects remove-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:lab06-nodes@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.defaultNodeServiceAccount"
gcloud iam service-accounts delete lab06-nodes@$PROJECT_ID.iam.gserviceaccount.com --quiet
```

Confirm nothing billable remains:

```bash
gcloud container clusters list                      # Listed 0 items
gcloud compute instances list                       # no gke-lab06-* nodes
gcloud compute disks list                           # no gke-lab06-* disks
gcloud compute forwarding-rules list                # nothing (you never created a LoadBalancer Service)
gcloud compute addresses list                       # nothing from this lab
gcloud compute networks list                        # no lab06-net
```

Remove the stale **kubeconfig** entry (the local file where kubectl stores cluster addresses and credentials; optional): `kubectl config delete-context gke_${PROJECT_ID}_us-central1_lab06-ap`.

**AWS / Azure:** nothing was created.

**Final check:** tomorrow, **Billing → Reports**, filter **Service = Kubernetes Engine** and label `lab=06`. The cluster fee should show as offset by the free-tier credit; pod charges should be cents.

## Write-up prompt

> On [date] I ran Kubernetes locally with kind and on Google Kubernetes Engine Autopilot. I deployed a non-root, read-only-filesystem application as a Deployment and Service, enforced the Pod Security "restricted" standard on its namespace (and confirmed a privileged pod was rejected), and verified namespace-scoped RBAC with `kubectl auth can-i`. On GKE Autopilot I used a least-privilege node service account, confirmed Workload Identity Federation and Dataplane V2 were enabled, and applied a default-deny NetworkPolicy plus a label-based allow rule, verifying traffic was blocked and then permitted. I deleted the cluster and all supporting resources within the hour.
