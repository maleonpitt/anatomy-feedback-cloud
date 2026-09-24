# Phase 6 — hypothetical ALB + EC2 backend (learning model only)
#
# DO NOT run terraform apply or terraform destroy against a real AWS account.
# Safe local commands: terraform fmt, terraform validate (after init downloads providers).
#
# This module models:
#   Internet → ALB (public) → Target Group → EC2 (private) → Uvicorn :5000

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Learning exercise — placeholders only. Do not apply without explicit authorization.
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}
