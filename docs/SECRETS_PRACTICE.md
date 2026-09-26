# Secrets practice — AWS Secrets Manager + External Secrets

**Code-only.** Do not create live secrets or `terraform apply` unless you authorize it.

## Target flow

```text
AWS Secrets Manager  (infra/secrets.tf)
        │
        │  External Secrets Operator + IRSA (infra/eso_irsa.tf)
        ▼
K8s Secret: anatomy-feedback-api-secrets
        │
        │  Deployment envFrom.secretRef
        ▼
FastAPI os.getenv(...)   (no app code change)
```

Local still uses `backend/.env`. Cloud does **not** bake secrets into the Docker image.

## What’s in which secret

| Key | Purpose |
|-----|---------|
| `SESSION_SECRET_KEY` | Sign session cookie |
| `MICROSOFT_CLIENT_*` | Azure OAuth |
| `MICROSOFT_REDIRECT_URI` | OAuth callback on API host |
| `OPENAI_API_KEY` | Feedback narrative |
| `CATEGORY_BUCKET_NAME` | Category CSV bucket name |

AWS access for S3 is **IRSA** (`infra/irsa_api.tf`), not access keys in Secrets Manager.

## Files

| File | Role |
|------|------|
| `infra/secrets.tf` | Secrets Manager secret (+ placeholder version, then ignore) |
| `infra/eso_irsa.tf` | IAM role for ESO to `GetSecretValue` |
| `k8s/external-secret.yaml` | SecretStore + ExternalSecret sync |
| `k8s/secret.example.yaml` | Manual/local fallback only |

## After authorized apply

1. Put real values (do not commit the file):

```bash
aws secretsmanager put-secret-value \
  --secret-id anatomy-feedback/api \
  --secret-string file://api-secrets.json
```

2. Install [External Secrets Operator](https://external-secrets.io/) on EKS.  
3. Set `eso_irsa_role_arn` on the `external-secrets` ServiceAccount.  
4. `kubectl apply -f k8s/external-secret.yaml`  
5. Confirm Secret exists; pods already reference `anatomy-feedback-api-secrets`.

## What we intentionally do not do

- Store secrets in git or the container image  
- Put `AWS_ACCESS_KEY_ID` in Secrets Manager for the API (use IRSA)  
- Have FastAPI call Secrets Manager directly (ESO keeps `getenv` simple)
