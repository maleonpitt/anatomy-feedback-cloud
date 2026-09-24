output "alb_dns_name" {
  description = "Hypothetical public DNS name for the API ALB."
  value       = aws_lb.api.dns_name
}

output "target_group_arn" {
  description = "Target group receiving forwarded HTTPS traffic (HTTP to instances)."
  value       = aws_lb_target_group.api.arn
}

output "alb_security_group_id" {
  description = "Security group on the ALB (443 from internet)."
  value       = aws_security_group.alb.id
}

output "backend_security_group_id" {
  description = "Security group on EC2 (app port from ALB SG only)."
  value       = aws_security_group.backend.id
}

output "backend_instance_ids" {
  description = "Registered EC2 API instance IDs (EC2-A, EC2-B, ...)."
  value       = aws_instance.api[*].id
}

output "app_port" {
  description = "Uvicorn listen port on backend instances."
  value       = var.app_port
}

output "health_check_path" {
  description = "ALB health check path (FastAPI GET /health)."
  value       = var.health_check_path
}

output "cloudfront_domain_name" {
  description = "Hypothetical CloudFront distribution domain (or use custom alias)."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_bucket_name" {
  description = "Private S3 bucket holding React static build (not category data)."
  value       = aws_s3_bucket.frontend.id
}

output "category_data_bucket_name" {
  description = "Documented placeholder for Phase 4 category storage (backend only)."
  value       = var.category_data_bucket_name
}

output "ecr_repository_url" {
  description = "ECR repo URL pattern for API images (placeholder account in real apply)."
  value       = aws_ecr_repository.api.repository_url
}

output "eks_cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS API endpoint (would be used by kubectl after apply)."
  value       = aws_eks_cluster.main.endpoint
}

output "practice_aws_account_id" {
  description = "Documented practice account — not contacted by this module."
  value       = var.aws_account_id_placeholder
}
