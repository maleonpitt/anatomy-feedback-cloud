# ------------------------------------------------------------------------------
# AWS Secrets Manager — API runtime secrets (not frontend, not AWS access keys)
#
# Real values are set AFTER apply (CLI/console). Terraform only creates the
# secret container + a one-time placeholder version (then ignore_changes).
# EKS sync: External Secrets Operator → K8s Secret (see k8s/external-secret.yaml).
#
# Learning model only — DO NOT terraform apply without explicit authorization.
# ------------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "api" {
  name                    = var.api_secrets_manager_name
  description             = "Anatomy feedback API secrets (Microsoft, OpenAI, session)"
  recovery_window_in_days = 7

  tags = {
    Name    = var.api_secrets_manager_name
    Project = var.project_name
    Tier    = "secrets"
  }
}

# Placeholder JSON only — replace with real values after authorized apply:
#   aws secretsmanager put-secret-value --secret-id ... --secret-string file://secrets.json
resource "aws_secretsmanager_secret_version" "api" {
  secret_id = aws_secretsmanager_secret.api.id
  secret_string = jsonencode({
    SESSION_SECRET_KEY      = "REPLACE_ME_SET_AFTER_APPLY"
    MICROSOFT_CLIENT_ID     = "REPLACE_ME_SET_AFTER_APPLY"
    MICROSOFT_CLIENT_SECRET = "REPLACE_ME_SET_AFTER_APPLY"
    MICROSOFT_TENANT_ID     = "REPLACE_ME_SET_AFTER_APPLY"
    MICROSOFT_REDIRECT_URI  = "https://api.example.com/callback"
    OPENAI_API_KEY          = "REPLACE_ME_SET_AFTER_APPLY"
    CATEGORY_BUCKET_NAME    = var.category_data_bucket_name
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
