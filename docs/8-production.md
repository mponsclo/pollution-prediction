# 8. Production readiness

A portfolio-grade pipeline isn't a production system. This doc is the honest gap between the two: what shipped, and what would have to exist before you could reasonably page on it at 3 a.m. The rest of the docs describe the system as-is; this one names what's missing.

## What shipped

- **Reproducible data pipeline** — dbt on BigQuery, 54/54 tests, uniqueness enforced at every layer, long-format unpivot joined 1:1 with instrument status.
- **Typed REST API** — FastAPI on Cloud Run, Pydantic schemas, 90% prediction intervals calibrated with CQR, live spatial features from BigQuery at request time.
- **Infrastructure as code** — Terraform modules for BigQuery / Cloud Run / Artifact Registry / IAM / KMS, bootstrap separate from main config, Workload Identity Federation (no SA keys).
- **CI/CD with review gates** — PR-gated `terraform plan` comment, `environment: production` reviewer gate on apply, plan artifact archived for audit, CODEOWNERS on `terraform/` and `.github/workflows/`.
- **Secrets hygiene** — `terraform.tfvars.enc` encrypted with SOPS + GCP KMS, decryptable only by identities holding `roles/cloudkms.cryptoKeyDecrypter`.

## Gaps

### 1. Data ingestion

| | |
|---|---|
| **Today** | Static CSV seeds (2021–2023) shipped via `dbt seed`. |
| **Target** | Scheduled Cloud Run Job (or Cloud Composer if the budget exists) pulling hourly from the [AirKorea Open API](https://www.airkorea.or.kr/) into a BigQuery staging table. dbt incremental models merge into `logic.measurements_clean` on a 1-hour cadence. |
| **Why it matters** | The models go stale. Without ingestion, the API serves increasingly irrelevant forecasts as the training distribution drifts from the live stream. |

### 2. Model artifact storage

| | |
|---|---|
| **Today** | `.pkl` pipelines baked into the Docker image at build time. Retraining requires a full image rebuild and redeploy. |
| **Target** | Push serialized pipelines to `gs://<project>-models/<yyyy-mm-dd>/forecast_<station>_<item>.pkl`. Cloud Run downloads the pinned version at startup via a `MODELS_URI` env var. A revision bump swaps model versions without rebuilding the image. |
| **Why it matters** | Decouples the release cadence of code from the release cadence of models. Enables shadow deploys and one-flag rollbacks when a retrain regresses a target. |

### 3. Model monitoring & drift detection

| | |
|---|---|
| **Today** | None. Predictions leave the process and are not observed. |
| **Target** | Cloud Run request middleware logs `(timestamp, station, pollutant, prediction, lower, upper, model_version)` rows into a BigQuery `predictions_log` table. A scheduled query joins actuals (24-hour lag) and computes rolling nRMSE + PI coverage per `(station, pollutant, model_version)`. Separate scheduled query runs PSI / KL divergence on feature distributions vs. training reference. Alert fires on sustained coverage < 85% or PSI > 0.25. |
| **Why it matters** | Calibration is a moving target. Without monitoring, silent degradation shows up as complaints rather than as alerts. |

### 4. Integration & contract tests

| | |
|---|---|
| **Today** | 14 pytest tests — pipeline unit tests with synthetic data and API smoke tests that mock model loading. No CI step hits real BigQuery. |
| **Target** | Nightly CI job that authenticates via the same WIF provider, runs `load_series(206, 0)` against `logic.measurements_clean`, asserts row counts and schema, and invokes the live API endpoint in a staging Cloud Run revision. Failure pages the oncall. |
| **Why it matters** | Unit tests cover the code; contract tests cover the interface with BigQuery and Cloud Run, which is where most incidents actually happen. |

### 5. Alerting & SLOs

| | |
|---|---|
| **Today** | GCP budget alerts only. No uptime or latency SLOs. |
| **Target** | Cloud Monitoring uptime check on `/health` (1-minute frequency, 3 regions). Alert policies on p95 latency > 2 s, 5xx rate > 1%, error log rate > 10/min. Notifications routed to a Slack channel for non-critical, PagerDuty for 5xx rate breaches. Publish an explicit SLO doc: 99.5% monthly availability, p95 < 2 s, forecast PI coverage ≥ 85% on a rolling 7-day window. |
| **Why it matters** | "It's returning 500s" should be the alerting system's discovery, not the user's. |

### 6. Retraining cadence & model registry

| | |
|---|---|
| **Today** | Manual `make train` produces pkl files; nothing tracks which version is deployed where. |
| **Target** | Weekly retrain via the same ingestion scheduler (Cloud Run Job). MLflow registry stores metadata per (station, pollutant, timestamp, metrics). Deployment reads the `prod` tag. Retrain only promotes a model if it beats the incumbent on rolling validation nRMSE and PI coverage. Otherwise alert. |
| **Why it matters** | Champion-challenger is the simplest way to avoid the "we retrained and suddenly everything's worse" failure mode. |

## Deliberate non-goals

Items left out on purpose — they would complicate the system without a clear payoff at this scale:

- **Kubernetes / GKE** — Cloud Run's scale-to-zero and autoscaling are sufficient for the traffic profile. GKE would add operational surface area for no throughput or cost benefit at <100 RPS.
- **Feature store** — features are cheap to recompute and the cross-station spatial features are already fetched live from BigQuery. A feature store would introduce a sync problem without removing an existing one.
- **Multi-region serving** — the stations are in Seoul, clients are regional. Single-region `asia-northeast3` is the right latency envelope.
- **Global unified model** — [Experiment 8](7-experiments.md) already tested this; pollutant heterogeneity made per-(station, pollutant) training strictly better.
