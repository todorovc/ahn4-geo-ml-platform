# AHN4 Geo ML Platform

Production-style starter platform for processing AHN4 elevation data, extracting terrain features, training a baseline geospatial ML model, and preparing Kubernetes-based batch and inference workflows on AWS.

## Overview

This repository provides an end-to-end skeleton for a GeoAI / MLOps project built around AHN4 elevation tiles:

- **Infrastructure as Code** with Terraform for AWS networking, EKS, ECR, S3, and IRSA
- **Kubernetes workloads** for AHN4 ingest, processing, and scheduled refresh jobs
- **Feature engineering** for terrain-derived raster and grid features
- **Baseline model training** with MLflow tracking
- **Extensible structure** for future inference and model serving workflows

The current implementation is intentionally starter-friendly: it focuses on a clean architecture, deployable building blocks, and a credible platform story rather than a finished production deployment.

## Architecture

```text
AHN4 source tiles
      |
      v
  ingest job  -------------------------------> S3 raw/
      |
      v
processing job --> slope/aspect rasters ----> S3 processed/
      |
      v
grid feature generation --------------------> S3 features/
      |
      v
training job --------------------------------> MLflow model + metrics
      |
      v
future inference API -----------------------> predictions
```

### Core layers

- `infra/` — Terraform modules and environment configuration for AWS
- `k8s/` — Kubernetes manifests for service accounts, jobs, cronjobs, and deployment foundations
- `apps/ingest/` — Data acquisition container skeleton
- `apps/processing/` — Terrain feature extraction pipeline
- `apps/training/` — Baseline ML training with MLflow logging
- `apps/inference/` — Placeholder inference API service
- `docs/` — Architecture and platform notes

## Repository structure

```text
ahn4-geo-ml-platform/
├── .github/workflows/
├── infra/
│   ├── envs/dev/
│   └── modules/
├── k8s/
│   ├── base/
│   └── overlays/
├── apps/
│   ├── ingest/
│   ├── processing/
│   ├── training/
│   └── inference/
├── ml/
├── docs/
├── tests/
└── scripts/
```

## Implemented infrastructure

The Terraform layer currently includes:

- VPC with public/private subnets, internet gateway, NAT gateway, and route tables
- EKS cluster with managed node group
- ECR repositories for ingest, processing, training, and inference images
- S3 data lake bucket with versioning and server-side encryption
- IRSA roles and policies for ingest and processing service accounts

The Kubernetes layer currently includes:

- `ahn-ingest-sa` and `ahn-processing-sa` service accounts with IRSA role placeholders
- `ahn4-ingest` batch job
- `ahn4-processing` batch job
- `ahn4-refresh-weekly` cronjob

## Processing pipeline

The processing app currently supports:

- Reading AHN4 GeoTIFF tiles from S3
- Converting nodata values to `NaN`
- Computing slope and aspect rasters
- Computing grid-level summary features such as:
  - mean elevation
  - min/max elevation
  - standard deviation of elevation
  - mean/max slope
  - mean aspect
  - relief
  - roughness
- Writing derived rasters and parquet feature tables back to S3

### Current S3 layout

```text
s3://<bucket>/
├── raw/ahn4/dsm/
├── processed/ahn4/dsm-features/
└── features/terrain_grid/
```

## Training pipeline

The training app currently provides a baseline workflow that:

- Reads parquet feature files from S3
- Builds a synthetic starter label based on low elevation and low slope
- Trains a `RandomForestClassifier`
- Logs parameters, metrics, and the model to MLflow

This is intended as a first platform milestone. In a more realistic setup, the synthetic label should be replaced by a domain-grounded target such as flood exposure proxy labels, land-use labels, or downstream risk labels.

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/todorovc/ahn4-geo-ml-platform.git
cd ahn4-geo-ml-platform
```

### 2. Prerequisites

Install and configure:

- Terraform 1.6+
- AWS CLI
- kubectl
- Docker
- Python 3.10+
- An AWS account with permissions for VPC, EKS, IAM, ECR, and S3

### 3. Configure Terraform variables

Review and adjust values in:

```text
infra/envs/dev/variables.tf
```

Pay special attention to:

- `aws_region`
- `data_bucket_name`
- CIDR ranges for VPC and subnets
- Kubernetes version

### 4. Deploy infrastructure

```bash
cd infra/envs/dev
terraform init
terraform plan
terraform apply
```

After apply, capture outputs such as:

- EKS cluster name
- ECR repository URLs
- S3 bucket name
- IRSA role ARNs

### 5. Update kubeconfig

```bash
aws eks update-kubeconfig --region eu-west-1 --name ahn4-geo-ml-platform-eks
```

### 6. Patch Kubernetes manifests

Before applying the Kubernetes manifests, replace the following placeholders:

- `REPLACE_WITH_INGEST_IRSA_ROLE_ARN`
- `REPLACE_WITH_PROCESSING_IRSA_ROLE_ARN`
- `REPLACE_WITH_ECR_URI`

Files to patch:

- `k8s/base/serviceaccounts/ahn-ingest-sa.yaml`
- `k8s/base/serviceaccounts/ahn-processing-sa.yaml`
- `k8s/base/jobs/ahn-ingest-job.yaml`
- `k8s/base/jobs/ahn-processing-job.yaml`
- `k8s/base/cronjobs/ahn-refresh-cronjob.yaml`

### 7. Build and push images

Example for processing:

```bash
aws ecr get-login-password --region eu-west-1 \
  | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-1.amazonaws.com

docker build -t ahn4-processing ./apps/processing
docker tag ahn4-processing:latest <ecr-uri>/ahn4-processing:latest
docker push <ecr-uri>/ahn4-processing:latest
```

Repeat the same pattern for:

- `ahn4-ingest`
- `ahn4-training`
- `ahn4-inference`

### 8. Apply Kubernetes manifests

```bash
kubectl apply -f k8s/base/namespaces/
kubectl apply -f k8s/base/serviceaccounts/
kubectl apply -f k8s/base/jobs/
kubectl apply -f k8s/base/cronjobs/
```

### 9. Run workloads

Trigger the processing job manually if needed:

```bash
kubectl create job --from=job/ahn4-processing ahn4-processing-manual -n data-platform
kubectl logs job/ahn4-processing-manual -n data-platform -f
```

## Local development

### Processing app

```bash
cd apps/processing
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Training app

```bash
cd apps/training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/train.py
```

The local entrypoints expect compatible AWS credentials and accessible S3 paths.

## Current limitations

This repository is a strong starter platform, but several parts are still intentionally incomplete:

- ingest source discovery is still placeholder-level
- processing currently handles a simple subset flow and only iterates through a limited number of objects
- model labels are synthetic and meant only for baseline experimentation
- inference service is still a placeholder
- Kubernetes manifests still require Terraform output injection or templating
- no GitOps or automated manifest promotion flow yet
- no observability stack deployment yet

## CI/CD workflows

The repository now includes starter GitHub Actions workflows for:

- `terraform-plan.yml` — validates and plans Terraform changes for the dev environment
- `build-processing-image.yml` — builds and pushes the processing image to ECR on changes to `apps/processing`
- `build-training-image.yml` — builds and pushes the training image to ECR on changes to `apps/training`
- `deploy-processing-job.yml` — manually deploys the processing Kubernetes job with a chosen image tag

### Required GitHub configuration

To make these workflows operational, configure:

- `AWS_GITHUB_ACTIONS_ROLE_ARN` as a GitHub Actions secret
- AWS IAM trust for GitHub OIDC
- Existing ECR repositories and EKS cluster from Terraform apply

These workflows are starter-grade and intentionally simple. A stronger production setup would add test stages, reusable workflow templates, protected environments, and manifest templating.

## Recommended next steps

1. Replace placeholder AHN tile discovery with a real source catalog workflow
2. Add Kustomize or Helm for environment-specific manifest rendering
3. Introduce Terraform remote state and separate dev/prod configuration
4. Add MLflow backend store and model registry persistence
5. Implement a real inference API that loads a trained model artifact
6. Add evaluation notebooks and richer geospatial validation metrics
7. Add monitoring for jobs, model quality, and data freshness
8. Extend CI/CD with test, security scan, and deployment promotion stages

## Why this project is useful

This project is intentionally shaped as a portfolio-grade GeoAI / Platform / MLOps repository. It demonstrates:

- cloud infrastructure design for geospatial workloads
- containerized data and ML pipelines
- IRSA-based least-privilege access in EKS
- feature engineering from raster elevation data
- baseline experiment tracking with MLflow
- a clean foundation for future training and serving workflows

## License

Add your preferred open-source license before broader distribution.
