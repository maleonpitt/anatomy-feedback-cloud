# Security

This repository is **public**. Treat everything committed as visible forever.

## Never commit

- `.env`, `.env.production`, or any file with real secrets  
- AWS access keys, session tokens  
- Microsoft client secrets, OpenAI API keys, session signing keys  
- SSH/PEM private keys  
- Production host credentials or personal tokens  

Only commit **`.env.example`** with obvious placeholders (`your-…`, `replace-me`).

## Local secrets

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# edit .env files locally — they are gitignored
```

## Cloud / CI

| Secret / config | Use |
|-----------------|-----|
| GitHub secret **`AWS_ROLE_ARN`** | OIDC deploy role — live CD only |
| GitHub variables (`ECR_REPOSITORY`, …) | CD targets — [`docs/CD_PRACTICE.md`](docs/CD_PRACTICE.md) |
| **AWS Secrets Manager** (`infra/secrets.tf`) | Microsoft / OpenAI / session secrets |
| External Secrets Operator | Syncs SM → K8s Secret — [`docs/SECRETS_PRACTICE.md`](docs/SECRETS_PRACTICE.md) |
| API IRSA | Category S3 (no static AWS keys) |

## Hard rules for this practice project

1. No `terraform apply` / live deploy without explicit authorization.  
2. Prefer **OIDC** from GitHub → AWS (`infra/github_oidc.tf`) over storing `AWS_ACCESS_KEY_ID` in GitHub.  
3. Images in **ECR** should not bake in secrets; inject at runtime via Secrets Manager → ESO → env.  
4. `SKIP_AUTH` / `/dev-login` is **local-only** (`FLASK_ENV=local`). Never enable in cloud/prod env.  
5. CD defaults to **dry_run=true**; set `dry_run=false` only after authorize + `AWS_ROLE_ARN`.  
6. If a secret is ever pushed accidentally: **rotate it** and scrub history (or treat the key as burned).

## Reporting

If you find a committed secret in this repo, rotate the credential and open an issue (without pasting the secret).
