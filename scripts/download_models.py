"""Download model .pkl files from Hugging Face Hub.

Single new seam for model delivery: Docker build and CI call this instead of
relying on model binaries committed to git. Fails fast when the download
fails or required files are missing — there is no fallback to bundled files.

Hub layout: files live under the repo's ``pkl_files/`` subfolder and are
flattened into ``assets/pkl_files/`` (where the app loads them from).

Equivalent command:
    hf download Ajiboye/ny2017hospital_predict_model \\
        --include "pkl_files/*.pkl" --local-dir /tmp/hf_models
    # then move /tmp/hf_models/pkl_files/*.pkl to assets/pkl_files/

Env:
    HF_REPO_ID: Hub repo (default Ajiboye/ny2017hospital_predict_model)
    LOS_HF_Token: Hub token, required for private repos, recommended otherwise
"""

import os
import shutil
import sys

REPO_ID = os.environ.get("HF_REPO_ID", "Ajiboye/ny2017hospital_predict_model")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, "assets", "pkl_files")

REQUIRED_FILES = [
    "xgb_modelv1.pkl",
    "xgb_hospital_full_pipeline.pkl",
    "feature_names.pkl",
    "mdc_mapping.pkl",
    "severity_mapping.pkl",
    "mdc_conversion_mapping.pkl",
]


def main():
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is required: pip install huggingface_hub")
        return 1

    token = os.environ.get("LOS_HF_Token")
    print(f"Downloading pkl_files/*.pkl from {REPO_ID} to {TARGET_DIR}")
    try:
        snapshot_download(
            repo_id=REPO_ID,
            repo_type="model",
            allow_patterns=["pkl_files/*.pkl"],
            local_dir=TARGET_DIR,
            token=token,
        )
    except Exception as e:
        print(f"Model download failed: {e}")
        return 1

    nested = os.path.join(TARGET_DIR, "pkl_files")
    if os.path.isdir(nested):
        for name in os.listdir(nested):
            shutil.move(os.path.join(nested, name), os.path.join(TARGET_DIR, name))
        os.rmdir(nested)

    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(TARGET_DIR, f))]
    if missing:
        print(f"Missing required model files after download: {missing}")
        return 1

    print(f"All {len(REQUIRED_FILES)} required model files present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
