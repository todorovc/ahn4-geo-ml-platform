# Gap fix plan

Implemented in this bundle:

1. Ingest no longer hard-caps to 5 rows and supports either a CSV catalog or explicit tile URLs.
2. Inference is a real FastAPI service loading an MLflow model URI and exposing `/healthz` and `/predict`.
3. Kustomize overlay added as a first step toward eliminating manual placeholder patching.
4. CI adds Python test execution and a Trivy filesystem scan.

Still needs environment-specific wiring after Terraform apply:

- set real ECR image URIs in Kustomize or CI substitutions;
- configure `MODEL_URI` for the promoted MLflow model;
- choose the authoritative AHN source catalog URL for your desired DSM/DTM product;
- add a real label source for supervised training, for example flood exposure, land-use, or risk outcomes.
