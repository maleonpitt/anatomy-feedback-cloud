# Kubernetes practice manifests (EKS-oriented)

**Code setup only.** Do not `kubectl apply` to a real EKS cluster unless you explicitly authorize AWS usage.

## Layout

| File | Purpose |
|------|---------|
| `namespace.yaml` | `anatomy-feedback` namespace |
| `serviceaccount.yaml` | IRSA-annotated ServiceAccount for API pods |
| `external-secret.yaml` | Secrets Manager → K8s Secret (ESO) |
| `configmap.yaml` | Non-secret env (no `SKIP_AUTH`) |
| `secret.example.yaml` | Manual Secret fallback only — prefer ESO |
| `deployment.yaml` | FastAPI pods, ECR image placeholder, `/health` probes |
| `service.yaml` | ClusterIP → container :5000 |
| `ingress.yaml` | ALB Ingress sketch (AWS LB Controller) |

## Mental model

```text
ECR image
  → Deployment (pods)
  → Service (ClusterIP)
  → Ingress (ALB) :443
  → Internet / api.example.com
```

Frontend stays on **CloudFront → S3** (see `infra/frontend.tf`), not in these manifests.

## Local practice (optional, no AWS)

```bash
# kind or minikube running locally
kubectl apply -f k8s/namespace.yaml
# create a real secret from literals — never commit it
kubectl apply -f k8s/configmap.yaml
# edit deployment image to a locally built tag if testing offline
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Ingress/ALB annotations need a real cluster + AWS LB Controller.

## Related Terraform

See `infra/ecr.tf`, `infra/eks.tf`, `infra/secrets.tf`, `infra/eso_irsa.tf`, and [`docs/SECRETS_PRACTICE.md`](../docs/SECRETS_PRACTICE.md).
