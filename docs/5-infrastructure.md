# 5. Infrastructure (Terraform + GCP)

Every GCP resource is managed as code. Bootstrap runs once locally; ongoing changes flow through GitHub Actions.

## Layout

```
terraform/
├── bootstrap/              One-time setup, local state
│   ├── project creation, API enablement
│   ├── GCS state bucket (mpc-pollution-331382-tf-state)
│   ├── KMS keyring + sops-key
│   ├── Workload Identity Federation pool + provider
│   └── Service accounts (cloud-run-sa, github-actions-sa)
├── modules/                Reusable modules
│   ├── bigquery/           landing / logic / presentation datasets
│   ├── cloud_run/          API service, scale 0-3
│   ├── artifact_registry/  Docker image repo
│   ├── iam/                Role bindings
│   ├── kms/                Collaborator access
│   └── workload_identity/  GitHub Actions ↔ GCP binding
├── main.tf                 Stitches modules together
├── terraform.tfvars.enc    SOPS-encrypted, committable
└── .terraform.lock.hcl
```

## Bootstrap (one-time)

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

Creates the GCP project, enables APIs, provisions the KMS key, WIF pool, and service accounts, and creates the GCS bucket for main-config state. The bootstrap itself uses local state, committed and encrypted.

## Main Config

Run from the repo root after bootstrap:

```bash
cd terraform
sops --decrypt terraform.tfvars.enc > terraform.tfvars
terraform init
terraform plan
terraform apply
```

State lives in `gs://mpc-pollution-331382-tf-state` (versioned, uniform bucket-level access). Locking is handled by GCS's strong consistency.

## Workload Identity Federation (no SA keys)

GitHub Actions authenticates to GCP via WIF — a short-lived OIDC token is exchanged for a GCP access token with the `github-actions-sa` identity. No service account JSON keys exist in the repo or in GitHub secrets.

Relevant settings in GitHub Actions workflows:

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.GH_ACTIONS_SA_EMAIL }}
```

## Secrets (SOPS + KMS)

`terraform.tfvars.enc` is encrypted with SOPS using the GCP KMS key `sops-key` in keyring `sops-keyring`. The `.sops.yaml` config rules determine which files are encrypted.

Decrypt:
```bash
sops --decrypt terraform/terraform.tfvars.enc > terraform/terraform.tfvars
```

Encrypt after edits:
```bash
sops --encrypt terraform/terraform.tfvars > terraform/terraform.tfvars.enc
```

Only identities with `roles/cloudkms.cryptoKeyDecrypter` on the KMS key can decrypt — managed through Terraform.

## CODEOWNERS

[`.github/CODEOWNERS`](../.github/CODEOWNERS) requires explicit review for any changes under `terraform/`, `terraform/bootstrap/`, `.github/workflows/`, or `.sops.yaml`. These are the project's "fail loud and slow" surfaces.

## CI/CD Workflows

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `terraform-validate.yml` | PR on `terraform/**` | `terraform fmt -check` + `terraform validate` |
| `terraform-plan.yml` | PR on `terraform/**` | Decrypts tfvars, runs plan, posts as PR comment |
| `terraform-apply.yml` | Push to `main` on `terraform/**` | Applies with manual approval gate (GitHub Environment) |
| `docker-build-deploy.yml` | Push to `main` on `app/**`, `src/**`, `Dockerfile`, `requirements.txt` | Build → push to Artifact Registry → deploy to Cloud Run |
| `lint.yml` | PR / push on `**.py` or `pyproject.toml` | Ruff check + format check |

## BigQuery Billing

Datasets use **LOGICAL** billing (cheaper at this data volume — ~3.7M rows). No table expirations set. The `logic.measurements_clean` table is the hot path and is queried by both the training pipeline and the live API.
