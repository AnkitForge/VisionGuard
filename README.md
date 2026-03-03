# VisionGuard - AI-Based Crime Detection System

A full-stack web application for monitoring live camera feeds and generating suspicious activity alerts with evidence capture and analytics.

## Stack
- Frontend: React (Vite), Tailwind CSS, React Router, Axios, Framer Motion, Recharts
- Backend: Flask, OpenCV, JWT Auth, REST APIs
- Database: Local JSON storage by default (`backend/storage/db.json`), optional MongoDB via env

## Project Structure
- `frontend/` React dashboard
- `backend/` Flask API, camera processing loop, alert/evidence storage

## Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app/server.py
```

## Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## API Endpoints
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/alerts`
- `GET /api/analytics`
- `POST /api/start-camera`
- `POST /api/stop-camera`
- `GET /api/evidence`
- `GET /api/system-status`
- `GET /api/video-feed`

## Environment Variables
### Backend (`backend/.env`)
- `JWT_SECRET`, `JWT_EXPIRE_HOURS`
- `CORS_ORIGINS`
- `DATA_MODE=local|mongo`, `MONGO_URI`, `MONGO_DB`
- `CAMERA_SOURCE`
- `ALERTS_DIR`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ALERT_EMAIL_TO`

### Frontend (`frontend/.env`)
- `VITE_API_BASE_URL=http://localhost:5000`

## Notes
- Camera detection uses OpenCV person detection + motion heuristic as a YOLO-compatible demo pipeline.
- For production, replace `_detect_suspicious` with a YOLO model inference service.
- JWT is sent using Authorization headers; for image/video tags, token is passed as query param.
