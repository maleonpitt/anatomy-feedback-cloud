# Hypothetical AWS infrastructure (EKS / ECR / CloudFront learning model)
#
# DO NOT run terraform apply or terraform destroy against a real AWS account.
# Safe local commands: terraform fmt, terraform validate (after init -backend=false).
#
# Primary practice path:
#   ECR → EKS nodes → Pods (Uvicorn) + CloudFront → S3 (React)
#
# Alternate learning path (main.tf): ALB → EC2

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
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
