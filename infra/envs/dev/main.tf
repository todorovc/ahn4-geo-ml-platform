terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "networking" {
  source               = "../../modules/networking"
  name                 = var.project_name
  vpc_cidr             = var.vpc_cidr
  availability_zones   = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "s3_data_lake" {
  source      = "../../modules/s3_data_lake"
  bucket_name = var.data_bucket_name
}

module "ecr" {
  source = "../../modules/ecr"
  repositories = [
    "ahn4-ingest",
    "ahn4-processing",
    "ahn4-training",
    "ahn4-inference"
  ]
}

module "eks" {
  source             = "../../modules/eks"
  cluster_name       = "${var.project_name}-eks"
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
}

module "iam_irsa" {
  source                       = "../../modules/iam_irsa"
  cluster_name                 = module.eks.cluster_name
  oidc_provider_arn            = module.eks.oidc_provider_arn
  oidc_provider_url            = module.eks.oidc_provider_url
  s3_bucket_arn                = module.s3_data_lake.bucket_arn
  namespace                    = "data-platform"
  ingest_service_account_name  = "ahn-ingest-sa"
  process_service_account_name = "ahn-processing-sa"
}
