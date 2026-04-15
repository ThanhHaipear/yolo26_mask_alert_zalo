# Mask Detection Backend

FastAPI backend for mask violation detection using an ONNX model. The service accepts an uploaded image, runs inference, stores alert records in a database, optionally uploads annotated images to Google Cloud Storage, and optionally sends alerts through Zalo OA.

## Folder structure

```text
backend/
  app/
    config.py
    db.py
    main.py
    models.py
    schemas.py
    routes/
      predict.py
      webhook.py
    services/
      alert_service.py
      model_service.py
      storage_service.py
      zalo_service.py
    utils/
      image_utils.py
  best_mask.onnx
  requirements.txt
  Dockerfile
  .env.example
  README.md
```

## Local setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The default `DB_URL` uses SQLite for local development. For Cloud SQL, replace it with a MySQL or PostgreSQL SQLAlchemy URL.
`CONF_THRESHOLD` controls score filtering and `IOU_THRESHOLD` controls NMS suppression for overlapping boxes.

## Environment variables

- `APP_ENV`: application environment label
- `DB_URL`: SQLAlchemy database URL
- `ZALO_BOT_TOKEN`: Zalo Bot API token
- `ZALO_CHAT_ID`: default Zalo chat id that receives alerts
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `CORS_ORIGINS`: comma-separated frontend origins
- `ENABLE_GCS_UPLOAD`: enable annotated image upload
- `ENABLE_ZALO_ALERT`: enable Zalo message sending
- `WEBHOOK_VERIFY_TOKEN`: token used by `GET /webhook/zalo`
- `CONTINUOUS_VIOLATION_SECONDS`: how long a violation must continue before realtime alerting fires. Set it to `3` locally for quick testing and raise it later for production.
- `VIOLATION_GRACE_SECONDS`: allowed gap between violating frames before the timer resets

## Endpoints

- `GET /`: service status
- `GET /health`: health check
- `POST /predict`: upload one image and optionally create an alert
- `POST /predict-frame`: send one webcam frame with `session_id` and trigger an alert only after continuous violation
- `GET /webhook/zalo`: verify webhook token
- `POST /webhook/zalo`: receive webhook payload and store Zalo user ids

## Example predict request

```powershell
curl -X POST http://localhost:8080/predict `
  -F "file=@sample.jpg" `
  -F "camera_name=lobby-cam"
```

## Cloud Run notes

- Keep `best_mask.onnx` inside `backend/`
- Build the image from the `backend/` directory
- Provide database, Zalo, and GCS credentials through environment variables and Google service account permissions
