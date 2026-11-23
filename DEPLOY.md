# Releases & model updates

## Secrets (GitHub repo settings → Secrets and variables → Actions)

| Secret | Purpose |
| --- | --- |
| `LOS_HF_Token` | Read access to `Ajiboye/ny2017hospital_predict_model`. Required if the repo is private, recommended if public. Used by CI test setup and CD Docker build. |
| `RENDER_DEPLOY_HOOK` | Render deploy hook that pulls the GHCR image. Called last in CD, only after push + smoke pass. |

`GITHUB_TOKEN` is ephemeral and needs no setup (GHCR push uses `packages:write`).

## Fresh clone (local dev)

```bash
pip install -r requirements.txt -r requirements-dev.txt huggingface_hub
python scripts/download_models.py   # pulls *.pkl from Ajiboye/ny2017hospital_predict_model
python -m pytest tests/ -q
python app.py
```

Equivalent one-liner: `hf download Ajiboye/ny2017hospital_predict_model --include "pkl_files/*.pkl" --local-dir /tmp/hf_models` then move `/tmp/hf_models/pkl_files/*.pkl` to `assets/pkl_files/`.

## Update the model

```bash
hf upload Ajiboye/ny2017hospital_predict_model assets/pkl_files/xgb_modelv1.pkl
```

Repeat per changed file. Required set (fail-fast checked by `scripts/download_models.py`):
`xgb_modelv1.pkl`, `xgb_hospital_full_pipeline.pkl`, `feature_names.pkl`,
`mdc_mapping.pkl`, `severity_mapping.pkl`, `mdc_conversion_mapping.pkl`.

## How releases happen

- **Code change**: merge to `main` → build → push `ghcr.io/<owner>/<repo>:latest` + `:sha-<short>` → container smoke (`/api/health` must report `model_loaded: true`) → Render hook. Docs-only edits (`*.md`, `docs/`, `.scratch/`) never deploy.
- **Model change**: upload new `.pkl`s to the Hub repo — nothing to do here. The monthly poll (1st, 03:00 UTC) notices the new Hub revision and cuts a model-refresh release automatically.
- **Right now**: Actions → CD → Run workflow (or push to `main`).

Images and `APP_VERSION` are stamped with the commit SHA, so `/api/health` tells you exactly which commit is live.

## Verify without noisy deploys

- Keep the branch PR green in CI first (install + download + pytest runs there too).
- Locally: `docker build --build-arg APP_VERSION=dev --build-arg LOS_HF_Token=$LOS_HF_Token -t los:local .`
  then `docker run -p 8000:8000 los:local` and `curl localhost:8000/api/health`.
- Don't push empty commits to test CD — every `main` push publishes an image and hits Render.

## Troubleshooting

- `Model download failed` / `Missing required model files`: Hub repo lacks files or `LOS_HF_Token` can't read it. Re-upload missing `.pkl`s or fix the token.
- Smoke `model_loaded: false`: image built without models — check the download step log, not the app.
- Render didn't update: confirm the CD run reached the hook step; replay the hook manually with `curl -X POST`.
