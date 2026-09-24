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

## Cloud / CI (later)

| Secret location | Use |
|-----------------|-----|
| GitHub Actions **encrypted secrets** | CI deploy credentials (OIDC preferred over long-lived keys) |
| AWS Secrets Manager / SSM Parameter Store | Runtime app secrets for ECS tasks |
| IAM task roles | S3/ECR access — prefer roles over embedding keys in images |

## Hard rules for this practice project

1. No `terraform apply` / live deploy without explicit authorization.  
2. Prefer **OIDC** from GitHub → AWS over storing `AWS_ACCESS_KEY_ID` in GitHub when possible.  
3. Images in **ECR** should not bake in secrets; inject at runtime.  
4. `SKIP_AUTH` / `/dev-login` is **local-only** (`FLASK_ENV=local`). Never enable in ECS/prod task env.  
5. If a secret is ever pushed accidentally: **rotate it** and scrub history (or treat the key as burned).

## Reporting

If you find a committed secret in this repo, rotate the credential and open an issue (without pasting the secret).
