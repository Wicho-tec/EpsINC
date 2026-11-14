variable "region" {
  description = "AWS region for the EpsInc cluster"
  type        = string
  default     = "us-east-1"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes minor version"
  type        = string
  default     = "1.34"
}

variable "admin_cidrs" {
  description = "Public IPv4 CIDRs allowed to reach the IAM-authenticated Kubernetes API"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "Wicho-tec"
}

variable "github_owner_id" {
  description = "Immutable GitHub owner ID used by the OIDC trust policy"
  type        = string
  default     = "243614440"
}

variable "github_repository" {
  description = "GitHub repository name"
  type        = string
  default     = "EpsINC"
}

variable "github_repository_id" {
  description = "Immutable GitHub repository ID used by the OIDC trust policy"
  type        = string
  default     = "1458250764"
}

variable "instance_types" {
  description = "EC2 instance types for the game node group"
  type        = list(string)
  default     = ["m7i.large"]
}

variable "capacity_type" {
  description = "EKS managed node group capacity type"
  type        = string
  default     = "ON_DEMAND"
  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.capacity_type)
    error_message = "capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "min_nodes" {
  description = "Minimum EC2 nodes"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum EC2 nodes"
  type        = number
  default     = 8
}

variable "desired_nodes" {
  description = "Initial EC2 nodes"
  type        = number
  default     = 2
}
