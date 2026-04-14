###############################################################################
# Artifacts Bucket
#
# Stores model-training outputs consumed by the frontend (forecast and anomaly
# prediction CSVs) and anything else that belongs alongside the code but is
# too volatile to check into git.
#
# Layout:
#   gs://{bucket_name}/predictions/forecast_predictions.csv
#   gs://{bucket_name}/predictions/anomaly_predictions.csv
#
# Uploaded manually (`scripts/sync_outputs_to_gcs.py`) or after a training
# run. Versioning is off — overwrites are expected; the training pipeline is
# reproducible from code + BigQuery history.
###############################################################################

resource "google_storage_bucket" "artifacts" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}
