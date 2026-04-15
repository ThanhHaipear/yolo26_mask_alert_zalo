# Mask Detection Frontend

React + Vite frontend for uploading an image to the FastAPI backend and displaying the returned mask-violation result.
The frontend also includes a browser webcam mode that sends one frame per second for realtime monitoring.

## Folder structure

```text
frontend/
  src/
    App.jsx
    main.jsx
    api.js
    styles.css
    components/
      DetectionList.jsx
      ImageUploader.jsx
      ResultPanel.jsx
      StatusMessage.jsx
  public/
  package.json
  vite.config.js
  .env.example
  firebase.json
  README.md
```

## Local development

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

## Build

```powershell
npm run build
```

## Firebase Hosting

```powershell
firebase deploy
```

Make sure Firebase Hosting is configured as a single-page app so every route rewrites to `index.html`. The included `firebase.json` already contains the rewrite rule.
