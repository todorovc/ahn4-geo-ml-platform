variable "cluster_name" { type = string }
variable "oidc_provider_arn" { type = string }
variable "oidc_provider_url" { type = string }
variable "s3_bucket_arn" { type = string }
variable "namespace" { type = string }
variable "ingest_service_account_name" { type = string }
variable "process_service_account_name" { type = string }

locals {
  oidc_subject_prefix = "${replace(var.oidc_provider_url, "https://", "")}:sub"
}

resource "aws_iam_policy" "ingest_s3" {
  name = "${var.cluster_name}-ingest-s3-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = [var.s3_bucket_arn]
      },
      {
        Effect = "Allow",
        Action = ["s3:GetObject", "s3:PutObject"],
        Resource = ["${var.s3_bucket_arn}/raw/*"]
      }
    ]
  })
}

resource "aws_iam_policy" "process_s3" {
  name = "${var.cluster_name}-process-s3-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = [var.s3_bucket_arn]
      },
      {
        Effect = "Allow",
        Action = ["s3:GetObject"],
        Resource = ["${var.s3_bucket_arn}/raw/*"]
      },
      {
        Effect = "Allow",
        Action = ["s3:PutObject"],
        Resource = ["${var.s3_bucket_arn}/processed/*", "${var.s3_bucket_arn}/features/*"]
      }
    ]
  })
}

resource "aws_iam_role" "ingest" {
  name = "${var.cluster_name}-ahn-ingest-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Federated = var.oidc_provider_arn },
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "${local.oidc_subject_prefix}" = "system:serviceaccount:${var.namespace}:${var.ingest_service_account_name}"
        }
      }
    }]
  })
}

resource "aws_iam_role" "processing" {
  name = "${var.cluster_name}-ahn-processing-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Federated = var.oidc_provider_arn },
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "${local.oidc_subject_prefix}" = "system:serviceaccount:${var.namespace}:${var.process_service_account_name}"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ingest" {
  role       = aws_iam_role.ingest.name
  policy_arn = aws_iam_policy.ingest_s3.arn
}

resource "aws_iam_role_policy_attachment" "processing" {
  role       = aws_iam_role.processing.name
  policy_arn = aws_iam_policy.process_s3.arn
}

output "ingest_role_arn" { value = aws_iam_role.ingest.arn }
output "processing_role_arn" { value = aws_iam_role.processing.arn }
