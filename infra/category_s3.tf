# ------------------------------------------------------------------------------
# Category data S3 (Phase 4) — backend CSVs only, not the React frontend bucket
#
# API pods access this via IRSA (see irsa_api.tf), not the GitHub deploy role.
# Learning model only — DO NOT terraform apply without explicit authorization.
# ------------------------------------------------------------------------------

resource "aws_s3_bucket" "category" {
  bucket = var.category_data_bucket_name

  tags = {
    Name    = "${var.project_name}-categories"
    Project = var.project_name
    Tier    = "category-data"
  }
}

resource "aws_s3_bucket_public_access_block" "category" {
  bucket = aws_s3_bucket.category.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "category" {
  bucket = aws_s3_bucket.category.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
