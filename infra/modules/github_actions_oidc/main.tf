variable "github_owner" { type = string }
variable "github_repo" { type = string }
variable "role_name" { type = string }
variable "aws_region" { type = string }
variable "ecr_repository_arns" { type = list(string) }
variable "eks_cluster_arn" { type = string }
variable "allow_main_branch_only" {
  type    = bool
  default = true
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

locals {
  github_sub = var.allow_main_branch_only
    ? "repo:${var.github_owner}/${var.github_repo}:ref:refs/heads/main"
    : "repo:${var.github_owner}/${var.github_repo}:*"
}

resource "aws_iam_role" "github_actions" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          },
          StringLike = {
            "token.actions.githubusercontent.com:sub" = local.github_sub
          }
        }
      }
    ]
  })
}

resource "aws_iam_policy" "github_actions" {
  name = "${var.role_name}-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid = "ECRAccess",
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
          "ecr:BatchGetImage"
        ],
        Resource = "*"
      },
      {
        Sid = "ScopedECRRepositories",
        Effect = "Allow",
        Action = [
          "ecr:DescribeRepositories",
          "ecr:DescribeImages",
          "ecr:ListImages"
        ],
        Resource = var.ecr_repository_arns
      },
      {
        Sid = "EKSDescribe",
        Effect = "Allow",
        Action = [
          "eks:DescribeCluster"
        ],
        Resource = var.eks_cluster_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions.arn
}

output "role_arn" {
  value = aws_iam_role.github_actions.arn
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}
