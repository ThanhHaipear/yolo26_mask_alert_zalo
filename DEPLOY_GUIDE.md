# Deployment Guide

## 1. Project structure

- `backend/`: FastAPI + ONNX + SQLAlchemy + Google Cloud Storage + Zalo Bot API
- `frontend/`: React + Vite + Firebase Hosting

## 2. Run backend locally

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Quick checks:

- `GET http://localhost:8000/`
- `GET http://localhost:8000/health`
- `POST http://localhost:8000/predict`

## 3. Run frontend locally

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Frontend local URL:

- `http://localhost:5173`

## 4. Configure Zalo Bot API

The backend now uses the same Zalo Bot API style as `sendMessage.js`.

Fill these variables in `backend/.env`:

```env
ENABLE_ZALO_ALERT=true
ZALO_BOT_TOKEN=your_real_bot_token
ZALO_CHAT_ID=your_real_chat_id
```

If you want to send a photo with the alert, the backend also needs a public image URL. That means GCS upload must be enabled and the uploaded image must be publicly reachable.

## 5. Configure Google Cloud Storage

Fill these variables in `backend/.env`:

```env
ENABLE_GCS_UPLOAD=true
GCS_BUCKET_NAME=your_bucket_name
```

The Cloud Run service account must have permission to write to the bucket.

## 6. Deploy backend to Cloud Run

### 6.1 Enable required services

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 6.2 Create Artifact Registry

```bash
gcloud artifacts repositories create mask-repo \
  --repository-format=docker \
  --location=asia-southeast1 \
  --description="Docker repo for mask api"
```

### 6.3 Build the backend image

Run inside `backend/`:

```bash
gcloud builds submit \
  --tag asia-southeast1-docker.pkg.dev/YOUR_PROJECT_ID/mask-repo/mask-api
```

### 6.4 Deploy to Cloud Run

```bash
gcloud run deploy mask-api \
  --image asia-southeast1-docker.pkg.dev/YOUR_PROJECT_ID/mask-repo/mask-api \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --set-env-vars APP_NAME="Mask Detection Backend",APP_VERSION="1.0.0",APP_ENV="production",CORS_ORIGINS="https://YOUR_FIREBASE_DOMAIN",DB_URL="YOUR_CLOUD_SQL_OR_SQLALCHEMY_URL",MODEL_PATH="best_mask.onnx",INPUT_SIZE="640",CONF_THRESHOLD="0.4",IOU_THRESHOLD="0.45",ALERT_COOLDOWN_SECONDS="30",DEFAULT_CAMERA_NAME="cloud-run-camera",ENABLE_ZALO_ALERT="true",ZALO_BOT_TOKEN="YOUR_ZALO_BOT_TOKEN",ZALO_CHAT_ID="YOUR_ZALO_CHAT_ID",ENABLE_GCS_UPLOAD="true",GCS_BUCKET_NAME="YOUR_BUCKET_NAME",WEBHOOK_VERIFY_TOKEN="YOUR_VERIFY_TOKEN"
```

Notes:

- Cloud Run must listen on port `8080`
- If you use Cloud SQL, provide a valid SQLAlchemy connection string in `DB_URL`
- `best_mask.onnx` must stay inside `backend/`

## 7. Webhook URL

After backend deploy, your webhook URL is:

```text
https://YOUR_CLOUD_RUN_URL/webhook/zalo
```

Verify URL example:

```text
https://YOUR_CLOUD_RUN_URL/webhook/zalo?verify_token=YOUR_VERIFY_TOKEN
```

## 8. Deploy frontend to Firebase Hosting

```bash
npm install -g firebase-tools
firebase login
cd frontend
Copy-Item .env.example .env
npm install
npm run build
firebase deploy
```

Before building for production, set:

```env
VITE_API_URL=https://YOUR_CLOUD_RUN_URL
```

## 9. End-to-end test checklist

1. Open the frontend from Firebase Hosting or local Vite.
2. Upload one image with no violation.
3. Upload one image with one clear violation.
4. Confirm `violation_count` and `detections` look correct.
5. Confirm alert rows are created in the database.
6. Confirm Zalo receives a message.
7. If GCS is enabled, confirm the backend stores an image URL and Bot API can use it.

## 10. Important notes

- Do not keep secrets in frontend files.
- Do not hard-code Zalo tokens in source code.
- The backend currently sends photo alerts only when it has an image URL available.
- If you keep `ENABLE_GCS_UPLOAD=false`, the backend falls back to text alerts.
