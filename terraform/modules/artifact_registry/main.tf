resource "google_artifact_registry_repository" "docker" {
  repository_id = "pollution-prediction"
  format        = "DOCKER"
  description   = "Docker images for the pollution-prediction API"
  project       = var.project_id
  location      = var.region

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s" # 7 days
    }
  }

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
}
