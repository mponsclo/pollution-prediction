variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Bucket location"
  type        = string
}

variable "bucket_name" {
  description = "Artifacts bucket name (globally unique)"
  type        = string
}
