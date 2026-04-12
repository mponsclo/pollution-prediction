variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region — Seoul, colocated with all resources"
  type        = string
  default     = "asia-northeast3"
}

variable "billing_account" {
  description = "GCP Billing Account ID (used for budget alerts)"
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository (owner/repo) for Workload Identity Federation"
  type        = string
  default     = "mponsclo/bigquery-air-quality-forecasting"
}

variable "collaborator_emails" {
  description = "Collaborator emails who need KMS encrypt/decrypt access for SOPS"
  type        = list(string)
  default     = []
}

variable "cloud_run_image" {
  description = "Container image URL for Cloud Run deployment"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
