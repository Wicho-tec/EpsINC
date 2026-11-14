output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS Kubernetes API endpoint"
  value       = module.eks.cluster_endpoint
}

output "github_actions_role_arn" {
  description = "ARN to store as the GitHub Actions AWS_ROLE_ARN secret"
  value       = aws_iam_role.github_actions.arn
}

output "cluster_autoscaler_role_arn" {
  description = "IAM role used by Cluster Autoscaler through EKS IRSA"
  value       = aws_iam_role.cluster_autoscaler.arn
}

output "image_repository_url" {
  description = "Private ECR repository for the game server"
  value       = aws_ecr_repository.epsinc.repository_url
}

output "connect_command" {
  description = "Command to configure kubectl for the cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
