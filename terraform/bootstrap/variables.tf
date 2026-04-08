variable "org_id" {
  description = "GCP Organization ID"
  type        = string
  # Passed via -var or bootstrap.tfvars (gitignored)
}

variable "billing_account" {
  description = "GCP Billing Account ID"
  type        = string
  sensitive   = true
  # Passed via -var or bootstrap.tfvars (gitignored)
}

variable "project_id" {
  description = "GCP Project ID to create (must be globally unique)"
  type        = string
  default     = "mpc-pollution-331382"
}

variable "region" {
  description = "GCP region — Seoul, closest to South Korean source data"
  type        = string
  default     = "asia-northeast3"
}

variable "github_repo" {
  description = "GitHub repository (owner/repo) for Workload Identity Federation"
  type        = string
  default     = "mponsclo/pollution-prediction"
}
