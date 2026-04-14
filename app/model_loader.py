"""Load pre-trained model pipelines from disk."""

import glob
import logging
import os

import joblib

logger = logging.getLogger(__name__)


def load_models(models_dir: str = "outputs/models") -> dict[tuple[str, int, int], dict]:
    """Load all pickled pipelines from the models directory.

    Returns dict keyed by (model_type, station_code, item_code).
    """
    pipelines: dict[tuple[str, int, int], dict] = {}

    if not os.path.isdir(models_dir):
        return pipelines

    for path in glob.glob(os.path.join(models_dir, "*.pkl")):
        filename = os.path.basename(path)
        # Format: forecast_206_0.pkl or anomaly_205_0.pkl
        parts = filename.replace(".pkl", "").split("_")
        if len(parts) != 3:
            continue

        model_type = parts[0]
        station_code = int(parts[1])
        item_code = int(parts[2])

        try:
            pipeline = joblib.load(path)
            pipelines[(model_type, station_code, item_code)] = pipeline
        except Exception as e:
            logger.warning("Failed to load %s: %s", path, e)

    return pipelines
