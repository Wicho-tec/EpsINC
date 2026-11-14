terraform {
  required_version = ">= 1.5.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.59, < 7.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_ecr_repository" "epsinc" {
  name                 = "epsinc/server"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = "epsinc"
  cidr = "10.0.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)

  public_subnets                 = ["10.0.1.0/24", "10.0.2.0/24"]
  map_public_ip_on_launch        = true
  enable_nat_gateway             = false
  enable_dns_hostnames           = true
  enable_dns_support             = true
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  name                         = "epsinc"
  kubernetes_version           = var.kubernetes_version
  # GitHub-hosted runners have no stable egress IP; IAM authentication still gates API access.
  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.admin_cidrs
  enable_irsa                  = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  access_entries = var.github_actions_role_arn == null ? {} : {
    github_actions = {
      principal_arn = var.github_actions_role_arn
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  eks_managed_node_groups = {
    game = {
      instance_types = var.instance_types
      min_size       = var.min_nodes
      max_size       = var.max_nodes
      desired_size   = var.desired_nodes
      capacity_type  = var.capacity_type
      labels = {
        "agones.dev/agones-system" = "true"
        "app"                      = "epsinc"
      }
    }
  }

  node_security_group_additional_rules = {
    game_tcp = {
      description = "Agones allocated game server TCP ports"
      protocol    = "tcp"
      from_port   = 7000
      to_port     = 8000
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
    game_udp = {
      description = "Agones allocated game server UDP ports"
      protocol    = "udp"
      from_port   = 7000
      to_port     = 8000
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

