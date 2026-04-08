output "project_id" {
  description = "The GCP project ID"
  value       = google_project.this.project_id
}

output "project_number" {
  description = "The GCP project number (needed for WIF provider path)"
  value       = google_project.this.number
}

output "tfstate_bucket" {
  description = "GCS bucket name for Terraform remote state"
  value       = google_storage_bucket.tfstate.name
}

output "kms_key_id" {
  description = "KMS crypto key ID for SOPS encryption"
  value       = google_kms_crypto_key.sops.id
}

output "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

output "github_actions_sa_email" {
  description = "GitHub Actions service account email"
  value       = google_service_account.github_actions.email
}

output "wif_provider" {
  description = "Workload Identity Federation provider resource name (set as GitHub secret WIF_PROVIDER)"
  value       = google_iam_workload_identity_pool_provider.github.name
}
