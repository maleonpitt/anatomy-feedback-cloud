# ------------------------------------------------------------------------------
# IRSA — API pods assume this role for category S3 (least privilege)
#
# Attach via ServiceAccount annotation in k8s/serviceaccount.yaml.
# Learning model only — DO NOT terraform apply without explicit authorization.
# ------------------------------------------------------------------------------

data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = {
    Name    = "${var.project_name}-eks-oidc"
    Project = var.project_name
  }
}

locals {
  eks_oidc_issuer_host = replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")
  api_service_account  = "system:serviceaccount:${var.k8s_namespace}:${var.k8s_api_service_account}"
}

data "aws_iam_policy_document" "api_irsa_assume" {
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
      values   = [local.api_service_account]
    }
  }
}

resource "aws_iam_role" "api_irsa" {
  name               = "${var.project_name}-api-irsa"
  assume_role_policy = data.aws_iam_policy_document.api_irsa_assume.json

  tags = {
    Name    = "${var.project_name}-api-irsa"
    Project = var.project_name
    Tier    = "workload"
  }
}

data "aws_iam_policy_document" "api_category_s3" {
  statement {
    sid    = "ListCategoryPrefix"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [aws_s3_bucket.category.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["categories/*"]
    }
  }

  statement {
    sid    = "CategoryObjects"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.category.arn}/categories/*"]
  }
}

resource "aws_iam_role_policy" "api_category_s3" {
  name   = "${var.project_name}-api-category-s3"
  role   = aws_iam_role.api_irsa.id
  policy = data.aws_iam_policy_document.api_category_s3.json
}
