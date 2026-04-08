###############################################################################
# BigQuery Datasets — one per DBT layer (landing, logic, presentation)
#
# Storage billing model: LOGICAL
#
# Why not PHYSICAL for this project:
#   - Physical billing charges for active bytes (compressed) PLUS time-travel
#     (7 days) and fail-safe (7 days) storage, which adds ~30-40% overhead.
#   - At small data volumes (~3.7M rows, well under 1 TB), that overhead
#     exceeds the savings from columnar compression.
#   - Physical billing only pays off at scale (multi-TB) where compression
#     ratios of 5-10x more than offset the time-travel/fail-safe surcharge.
#   - For a project on the free $300 credit tier, logical is the cheaper option.
#
# No table or partition expirations — this is historical reference data
# (2021-2023 air quality measurements) that should be retained indefinitely.
###############################################################################

resource "google_bigquery_dataset" "landing" {
  dataset_id    = "landing"
  friendly_name = "Landing"
  description   = "Raw seed data loaded by DBT — views over CSV seeds"
  project       = var.project_id
  location      = var.region

  storage_billing_model = "LOGICAL"

  # default_table_expiration_ms     — unset (never expire)
  # default_partition_expiration_ms — unset (never expire)
}

resource "google_bigquery_dataset" "logic" {
  dataset_id    = "logic"
  friendly_name = "Logic"
  description   = "Cleaned and transformed data — measurements_long, measurements_with_status, measurements_clean"
  project       = var.project_id
  location      = var.region

  storage_billing_model = "LOGICAL"
}

resource "google_bigquery_dataset" "presentation" {
  dataset_id    = "presentation"
  friendly_name = "Presentation"
  description   = "Dashboard-ready wide-format data — dashboard_wide"
  project       = var.project_id
  location      = var.region

  storage_billing_model = "LOGICAL"
}
