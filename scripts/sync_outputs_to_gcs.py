"""Upload prediction CSVs to the artifacts bucket.

Usage: python scripts/sync_outputs_to_gcs.py

The frontend reads these from gs://{bucket}/predictions/. Re-run after any
training refresh that regenerates the CSVs in outputs/.
"""

import os
import sys
from pathlib import Path

from google.api_core.exceptions import Forbidden, NotFound
from google.cloud import storage

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "mpc-pollution-331382")
BUCKET_NAME = os.environ.get("ARTIFACTS_BUCKET", f"{PROJECT_ID}-artifacts")

FILES = [
    ("forecast_predictions.csv", "predictions/forecast_predictions.csv"),
    ("anomaly_predictions.csv", "predictions/anomaly_predictions.csv"),
]


def main() -> int:
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    try:
        if not bucket.exists():
            print(
                f"error: bucket gs://{BUCKET_NAME} does not exist. Run `terraform apply` first to create it.",
                file=sys.stderr,
            )
            return 2
    except Forbidden:
        print(
            f"error: access denied on gs://{BUCKET_NAME}. Check your ADC identity "
            f"has storage.buckets.get (storage.objectAdmin or storage.admin).",
            file=sys.stderr,
        )
        return 2

    uploaded = 0
    missing = []
    for local_name, remote_name in FILES:
        local_path = OUTPUTS / local_name
        if not local_path.exists():
            missing.append(str(local_path))
            continue
        try:
            blob = bucket.blob(remote_name)
            blob.upload_from_filename(str(local_path), content_type="text/csv")
        except (NotFound, Forbidden) as e:
            print(f"error uploading {local_path}: {e}", file=sys.stderr)
            return 2
        print(f"uploaded {local_path} -> gs://{BUCKET_NAME}/{remote_name}")
        uploaded += 1

    if missing:
        print(f"skipped (not found locally): {', '.join(missing)}", file=sys.stderr)

    print(f"done ({uploaded}/{len(FILES)} uploaded)")
    return 0 if uploaded == len(FILES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
