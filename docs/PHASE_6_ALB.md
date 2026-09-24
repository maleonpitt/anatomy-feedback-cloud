# Phase 6 — Application Load Balancer architecture (local design)

This document describes the **hypothetical** API path for the anatomy-feedback backend modernization exercise. Nothing here is deployed to AWS or the live site.

## End-to-end request path

```text
Browser
   ↓
HTTPS (api.example.com)
   ↓
Internet Gateway
   ↓
ALB listener :443
   ↓
TLS termination (ACM certificate — placeholder in Terraform)
   ↓
Target Group (HTTP to backend :5000)
   ↓
Health check: GET /health → {"status":"healthy"} (HTTP 200)
   ↓
Healthy EC2 target (private subnet)
   ↓
Backend security group (app port from ALB SG only)
   ↓
Docker container
   ↓
Uvicorn (0.0.0.0:5000)
   ↓
FastAPI routers
   ↓
services (category store, email, OAuth, …)
   ↓
S3CategoryStore / Microsoft Graph / OpenAI
```

## EC2 vs ECS (decision)

**Chosen model: EC2 + Docker** (see `infra/README.md` for comparison table).

Reasons for this repo:

- Existing `Dockerfile` and `docker-compose.yml` already express “container on a host.”
- Phase 6 goal is to understand **ALB → target group → EC2 → Uvicorn**, not orchestration APIs.
- Target group `target_type = instance` with port `5000` matches the current Uvicorn bind.

ECS would add task definitions and service scheduling without changing the FastAPI application; it is deferred.

## Component reference (this application)

| Component | Role |
|-----------|------|
| **Internet Gateway** | Allows traffic between the VPC and the public internet; required for a public ALB. |
| **Public subnet** | Subnet with a route to the IGW; hosts the ALB (not the API containers). |
| **ALB** | Layer-7 load balancer; terminates HTTPS and forwards HTTP to healthy targets. |
| **Listener** | Binds ALB to port 443 and forwards to a target group (default action). |
| **Target group** | Registers EC2 instances; runs health checks; **does not execute FastAPI**. |
| **Security group** | Stateful firewall on ALB and EC2; backend accepts :5000 only from the ALB SG. |
| **Private subnet** | Backend EC2 without public IPs; reachable from ALB via VPC routing. |
| **EC2** | Compute for Docker; one or more instances behind the target group. |
| **Uvicorn** | ASGI server listening on `0.0.0.0:5000`; still required behind the ALB. |
| **FastAPI** | Application framework; routes `/health`, `/login`, uploads, feedback, etc. |
| **S3** | Shared category CSV per `category_session_id`; enables stateless backends. |

## ALB listener design

- **Port / protocol:** 443 HTTPS
- **Certificate:** `var.certificate_arn` placeholder (real deploy: ACM in same region as ALB)
- **TLS termination:** At the ALB; traffic to instances is **HTTP** on port **5000**
- **Default action:** Forward to API target group

## Target group design

| Setting | Value |
|---------|--------|
| Target type | `instance` (EC2) |
| Protocol | HTTP |
| Port | `5000` (same as Uvicorn / `EXPOSE` in Dockerfile) |
| Health check protocol | HTTP |
| Health check path | `/health` |
| Success matcher | `200` |
| Expected body | `{"status":"healthy"}` (ALB checks status code; body is app contract) |

The target group answers: “which EC2 instances are healthy on :5000?” The ALB uses that list for routing.

## Security group relationship

```text
Internet
   ↓ TCP 443 allowed
ALB security group
   ↓ TCP 5000 allowed (source = ALB SG)
Backend security group
   ↓
EC2 / Uvicorn
```

Backend **must not** allow `0.0.0.0/0` on port 5000. Only the ALB security group is a valid source.

## Public / private subnet layout

```text
VPC

Public Subnet A  ──┐
Public Subnet B  ──┼── ALB (multi-AZ)
Private Subnet A ───── EC2-A
Private Subnet B ───── EC2-B
```

EC2 instances use `associate_public_ip_address = false`. Inbound API traffic is only via the ALB.

**Outbound:** Private instances calling Microsoft Graph, OpenAI, or S3 need egress (NAT Gateway, NAT instance, or VPC endpoints). This exercise documents that need but does **not** create NAT.

## Uvicorn and FastAPI roles

- **Uvicorn** — Process that accepts HTTP on the instance; configured in `backend/Dockerfile` as `--host 0.0.0.0 --port 5000` so the ALB can reach the container from another host in the VPC.
- **FastAPI** — Application in `backend/main.py` and `backend/routers/`; implements `/health` and business routes.

The ALB does **not** replace Uvicorn. It sits in front of it.

## Phase 4 shared storage (multi-instance)

```text
                       ALB
                        ↓
                   Target Group
                    /        \
                   ↓          ↓
                EC2-A       EC2-B
                   ↓          ↓
               Uvicorn    Uvicorn
                   ↓          ↓
               FastAPI    FastAPI
                    \        /
                     \      /
                   S3 bucket
         categories/<category_session_id>/categories.csv
```

- Browser holds signed `feedback_session` cookie (`category_session_id` inside).
- Request 1 may hit EC2-A; request 2 may hit EC2-B.
- **Sticky sessions are not required** — session id + S3 key tie uploads together.

## Session and dual-origin (Phase 5)

```text
Browser
   ↓ feedback_session cookie
ALB
   ↓ any healthy target
FastAPI (session middleware)
   ↓ category_session_id
S3 object
```

CORS and cookie settings remain env-driven (`FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `SESSION_COOKIE_*`). See `docs/DUAL_ORIGIN.md`.

## Nginx (retired in Phase 7)

Nginx is **not** part of the target architecture. Legacy config: [`legacy/nginx/`](../legacy/nginx/).  
See [`PHASE_7_CLOUDFRONT.md`](PHASE_7_CLOUDFRONT.md) for the frontend cutover.

## Repository alignment (inspection summary)

| Item | Current state |
|------|----------------|
| Uvicorn port | **5000** (`Dockerfile`, docker-compose healthcheck) |
| Bind address | **0.0.0.0** (appropriate for ALB targets) |
| `/health` | `GET /health` → 200, `{"status":"healthy"}` |
| Docker | `backend/Dockerfile`; compose exposes 5000 internally |
| Terraform before Phase 6 | None |
| Nginx | Retired — archived under `legacy/nginx/` |
| Live host references | `legacy/` only (not in active application code) |
| EC2/ECS in repo | Neither represented until `infra/` (Phase 6) |

## Terraform module

Hypothetical resources live under [`infra/`](../infra/). All IDs are placeholders.

## What was not done (requires real AWS)

- `terraform apply` / `terraform destroy`
- `terraform plan` with live credentials
- ACM issuance, DNS, Route 53
- Creating or querying production ALB, SGs, EC2, target groups
- Deploying containers to EC2
- Replacing Nginx or CloudFront setup

**No live site or real AWS resources were accessed, modified, created, queried, or deployed for Phase 6.**
