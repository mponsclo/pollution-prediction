###############################################################################
# Service Accounts & IAM Role Bindings
#
# Service accounts are created in bootstrap (chicken-and-egg: WIF needs the SA
# to exist). This module imports them as data sources and manages role bindings
# that the main Terraform config controls.
###############################################################################

data "google_service_account" "cloud_run" {
  account_id = "cloud-run-sa"
  project    = var.project_id
}

data "google_service_account" "github_actions" {
  account_id = "github-actions-sa"
  project    = var.project_id
}

# ---------------------------------------------------------------------------
# Cloud Run SA — runtime permissions
# ---------------------------------------------------------------------------

locals {
  cloud_run_roles = [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/cloudtrace.agent",
  ]
}

resource "google_project_iam_member" "cloud_run" {
  for_each = toset(local.cloud_run_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.cloud_run.email}"
}

# ---------------------------------------------------------------------------
# GitHub Actions SA — CI/CD permissions
# ---------------------------------------------------------------------------

locals {
  # Least-privilege roles for the CI/CD service account. Scoped to the
  # resources each workflow step needs:
  #   - storage.objectAdmin        -> read/write the Terraform state bucket
  #   - artifactregistry.writer    -> push Docker images
  #   - run.admin                  -> deploy Cloud Run revisions (supersedes run.developer)
  #   - cloudkms.cryptoKeyDecrypter-> decrypt SOPS-encrypted tfvars
  #   - iam.serviceAccountUser     -> impersonate cloud-run-sa during deploy
  #   - bigquery.metadataViewer    -> terraform plan can read dataset metadata
  # roles/viewer was removed: far broader than anything CI needs.
  github_actions_roles = [
    "roles/storage.objectAdmin",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/cloudkms.cryptoKeyDecrypter",
    "roles/iam.serviceAccountUser",
    "roles/bigquery.metadataViewer",
  ]
}

resource "google_project_iam_member" "github_actions" {
  for_each = toset(local.github_actions_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${data.google_service_account.github_actions.email}"
}
