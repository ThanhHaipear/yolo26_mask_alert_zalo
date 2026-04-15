# Mask Alert Zalo

Full-stack real-time mask violation monitoring system built with FastAPI, React, ONNX Runtime, and Zalo Bot integration.

This project detects face mask violations from uploaded images and live webcam frames, tracks continuous violations over time, stores alert records in a database, uploads annotated evidence images, and sends notifications through Zalo when configured thresholds are reached.

## Overview

This repository is designed as a practical deployment-style computer vision application rather than a standalone model demo. It combines inference, state tracking, alert management, web UI, and notification delivery into one workflow suitable for portfolio review and CV presentation.

## Key Highlights

- Built a full-stack mask violation monitoring system with a FastAPI backend and React frontend
- Ran ONNX-based object detection for mask compliance checking on uploaded images and realtime webcam frames
- Implemented continuous violation tracking with threshold and grace-period logic to reduce false or premature alerts
- Added alert cooldown logic to prevent duplicate notifications during repeated violations
- Stored alert history in a database and supported annotated image upload for alert evidence
- Integrated Zalo Bot messaging for automated text or image-based notifications
- Added webhook handling to capture and store Zalo user information
- Included automated backend tests for prediction, webhook, and service flows

## Demo

Add your screenshots, GIFs, or demo links here before submitting the project in your CV.

Suggested layout:

```md
![Realtime Monitoring](assets/demo/realtime-monitor.jpg)
![Alert Result](assets/demo/alert-result.jpg)
[Watch demo video](https://your-demo-link)
```

## System Architecture

### Frontend

The frontend is built with React and Vite. It provides:

- realtime webcam monitoring through the browser
- manual image upload for one-off checks and debugging
- live result panels for detections, violations, and alert state
- status messages for backend connectivity and prediction responses

Core frontend files include:

- `frontend/src/App.jsx`
- `frontend/src/components/WebcamMonitor.jsx`
- `frontend/src/components/ImageUploader.jsx`
- `frontend/src/components/ResultPanel.jsx`
- `frontend/src/components/DetectionList.jsx`

### Backend

The backend is built with FastAPI and organized into routes, services, models, and utilities. It provides:

- `/predict` for single-image inference
- `/predict-frame` for realtime frame-by-frame monitoring
- `/webhook/zalo` for Zalo webhook verification and event ingestion
- database-backed alert persistence
- configurable cooldown, threshold, and grace-period alert logic
- optional Google Cloud Storage upload for annotated alert images
- optional Zalo Bot notification delivery

Core backend files include:

- `backend/app/main.py`
- `backend/app/routes/predict.py`
- `backend/app/routes/webhook.py`
- `backend/app/services/model_service.py`
- `backend/app/services/realtime_state_service.py`
- `backend/app/services/alert_service.py`
- `backend/app/services/zalo_service.py`
- `backend/app/services/storage_service.py`

## Detection And Alert Flow

1. A user uploads an image or starts realtime webcam monitoring from the frontend.
2. The backend receives the image frame and runs inference through an ONNX model.
3. Detected classes are post-processed into mask compliance results.
4. If a violation is detected, the realtime state service tracks how long the violation has remained active.
5. Once the configured threshold is reached, an alert can be created.
6. The system stores the alert in the database, optionally uploads an annotated image to Google Cloud Storage, and optionally sends a Zalo notification.
7. Cooldown logic prevents repeated alerts from being sent too frequently for the same camera.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- ONNX Runtime
- OpenCV
- React
- Vite
- Axios
- Zalo Bot API
- Google Cloud Storage
- Pytest

## Project Structure

```text
mask_zalo/
|- backend/
|  |- app/
|  |  |- routes/
|  |  |- services/
|  |  |- utils/
|  |  |- config.py
|  |  |- db.py
|  |  |- main.py
|  |  |- models.py
|  |  \- schemas.py
|  |- tests/
|  |- best_mask.onnx
|  |- requirements.txt
|  \- Dockerfile
|- frontend/
|  |- src/
|  |  |- components/
|  |  |- api.js
|  |  |- App.jsx
|  |  \- main.jsx
|  |- package.json
|  \- vite.config.js
|- DEPLOY_GUIDE.md
|- README.md
\- mask_alerts.db
```

## Configuration

Important backend settings are defined in `backend/app/config.py` and can be provided through environment variables:

- `MODEL_PATH`
- `INPUT_SIZE`
- `CONF_THRESHOLD`
- `IOU_THRESHOLD`
- `CLASS_NAMES`
- `ALERT_COOLDOWN_SECONDS`
- `CONTINUOUS_VIOLATION_SECONDS`
- `VIOLATION_GRACE_SECONDS`
- `ENABLE_ZALO_ALERT`
- `ZALO_BOT_TOKEN`
- `ZALO_CHAT_ID`
- `ENABLE_GCS_UPLOAD`
- `GCS_BUCKET_NAME`
- `WEBHOOK_VERIFY_TOKEN`

## How To Run

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

Backend tests are included for prediction routes, webhook routes, and service logic.

```bash
cd backend
pytest
```

## Why This Project Is Strong For A CV

This project shows more than model inference. It demonstrates the ability to build an end-to-end applied AI system with:

- model serving and inference integration
- realtime state management
- backend API design
- frontend product interface development
- alert workflow design and anti-spam controls
- third-party messaging integration
- cloud storage integration
- testing and deployment readiness

## CV-Ready Summary

You can describe this project on your CV with wording like:

> Built a full-stack mask violation monitoring system using FastAPI, React, ONNX Runtime, and Zalo Bot integration, enabling realtime webcam detection, alert persistence, configurable violation thresholds, and automated notification delivery.

Shorter version:

> Developed a full-stack mask detection and alerting application with realtime monitoring and Zalo notification integration.

## Suggested Next Improvements

- add deployment screenshots and a demo video to the README
- document measured model performance and latency
- support role-based admin views for alert history
- add Docker Compose for one-command local startup
- move SQLite to PostgreSQL for production deployment
- add authentication and camera source management

## Author

**Le Thanh Hai**

- GitHub: [ThanhHaipear](https://github.com/ThanhHaipear)
