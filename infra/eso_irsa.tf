# ------------------------------------------------------------------------------
# IRSA for External Secrets Operator (syncs Secrets Manager → K8s Secret)
#
# Install ESO on the cluster, annotate its ServiceAccount with eso_irsa_role_arn,
# then apply k8s/secretstore.yaml + k8s/external-secret.yaml.
# Learning model only — DO NOT terraform apply without explicit authorization.
# ------------------------------------------------------------------------------

locals {
  eso_service_account = "system:serviceaccount:${var.k8s_namespace}:${var.k8s_eso_service_account}"
}

data "aws_iam_policy_document" "eso_irsa_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_issuer_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.eks_oidc_issuer_host}:sub"
      values   = [local.eso_service_account]
    }
  }
}

resource "aws_iam_role" "eso_irsa" {
  name               = "${var.project_name}-eso-irsa"
  assume_role_policy = data.aws_iam_policy_document.eso_irsa_assume.json

  tags = {
    Name    = "${var.project_name}-eso-irsa"
    Project = var.project_name
    Tier    = "secrets-sync"
  }
}

data "aws_iam_policy_document" "eso_secrets" {
  statement {
    sid    = "ReadApiSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = [aws_secretsmanager_secret.api.arn]
  }
}

resource "aws_iam_role_policy" "eso_secrets" {
  name   = "${var.project_name}-eso-secrets"
  role   = aws_iam_role.eso_irsa.id
  policy = data.aws_iam_policy_document.eso_secrets.json
}
