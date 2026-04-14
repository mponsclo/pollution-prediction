output "bucket_name" {
  description = "Artifacts bucket name"
  value       = google_storage_bucket.artifacts.name
}

output "bucket_url" {
  description = "gs:// URL of the artifacts bucket"
  value       = "gs://${google_storage_bucket.artifacts.name}"
}
