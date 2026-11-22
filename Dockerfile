# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir huggingface_hub

COPY app.py cleaning_script.py ./
COPY templates ./templates
COPY assets/css ./assets/css
COPY assets/js ./assets/js
COPY assets/data ./assets/data
COPY scripts/download_models.py ./scripts/download_models.py

ARG APP_VERSION=dev
ARG LOS_HF_Token
ARG HF_REPO_ID=Ajiboye/ny2017hospital_predict_model
RUN LOS_HF_Token=$LOS_HF_Token HF_REPO_ID=$HF_REPO_ID python scripts/download_models.py

ENV APP_VERSION=${APP_VERSION}

EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} --timeout 120 app:app"]
