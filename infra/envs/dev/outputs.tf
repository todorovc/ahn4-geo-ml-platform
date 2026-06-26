output "vpc_id" {
  value = module.networking.vpc_id
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "data_bucket_name" {
  value = module.s3_data_lake.bucket_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "ingest_irsa_role_arn" {
  value = module.iam_irsa.ingest_role_arn
}

output "processing_irsa_role_arn" {
  value = module.iam_irsa.processing_role_arn
}
