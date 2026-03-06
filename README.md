<<<<<<< HEAD
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
=======
# VisionGuard – AI-Based Crime Detection System

![React](https://img.shields.io/badge/Frontend-React-blue)
![Tailwind](https://img.shields.io/badge/UI-TailwindCSS-38B2AC)
![Flask](https://img.shields.io/badge/Backend-Flask-black)
![OpenCV](https://img.shields.io/badge/ComputerVision-OpenCV-green)
![JWT](https://img.shields.io/badge/Auth-JWT-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

VisionGuard is a **full-stack AI-powered surveillance system** designed to detect suspicious activities in supermarkets or retail environments using CCTV feeds.

The system analyzes video streams in real time, generates alerts for suspicious behavior, stores evidence clips, and provides analytics through an interactive dashboard.

This project demonstrates the use of **computer vision, AI monitoring, and modern full-stack development** to enhance retail security.

---
---

# Features

### Live Camera Monitoring

* Connects to **webcam or CCTV feed**
* Displays live video stream in dashboard
* Real-time frame processing using OpenCV

### Suspicious Activity Detection

* Uses **motion detection and object detection**
* Can be extended with **YOLOv8 models**

### Real-Time Alerts

* Instant alert when suspicious activity is detected
* Alert includes:

  * Timestamp
  * Detection confidence
  * Event type

### Evidence Recording

* Automatically saves **10–15 second video clips**
* Stored as evidence for later review
* Clips can be **downloaded from dashboard**

### Analytics Dashboard

Displays:

* Alerts per day
* Threat distribution
* System activity
* Detection statistics

### Authentication

* Admin login / register
* JWT authentication
* Protected routes

---

# Tech Stack

## Frontend

* React (Vite)
* Tailwind CSS
* React Router
* Axios
* Framer Motion
* Recharts

## Backend

* Flask
* OpenCV
* JWT Authentication
* REST APIs

## Database

* Local JSON storage (`backend/storage/db.json`)
* Optional MongoDB support

---

# Project Architecture

```
Camera / CCTV
       │
       ▼
OpenCV Frame Processing
       │
       ▼
Suspicious Activity Detection
       │
       ├── Alert Generation
       │
       ├── Evidence Recording
       │
       ▼
Flask Backend API
       │
       ▼
React Dashboard
       │
       ├── Live Feed
       ├── Alerts
       ├── Evidence
       └── Analytics
```

---

# Project Structure

```
VisionGuard/
│
├── frontend/           # React dashboard
│
├── backend/
│   ├── app/
│   │   ├── server.py
│   │   ├── routes/
│   │   ├── services/
│   │   └── camera_processing/
│   │
│   ├── storage/
│   │   └── db.json
│   │
│   └── evidence/
│
└── README.md
```

---

# Backend Setup

```bash
cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

python app/server.py
```

Backend runs on:

```
http://localhost:5000
```

---

# Frontend Setup

```bash
cd frontend

npm install

cp .env.example .env

npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

# API Endpoints

| Method | Endpoint           | Description        |
| ------ | ------------------ | ------------------ |
| POST   | /api/auth/login    | Login user         |
| POST   | /api/auth/register | Register admin     |
| GET    | /api/alerts        | Fetch alerts       |
| GET    | /api/analytics     | Fetch analytics    |
| POST   | /api/start-camera  | Start monitoring   |
| POST   | /api/stop-camera   | Stop camera        |
| GET    | /api/evidence      | Get evidence clips |
| GET    | /api/system-status | System health      |
| GET    | /api/video-feed    | Live video stream  |

---

# Screenshots

Add screenshots of your project here.

Example:

/screenshots
dashboard.png
alerts.png
analytics.png

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Alerts

![Alerts](screenshots/alerts.png)

### Analytics

![Analytics](screenshots/analytics.png)

---

# Demo GIF

Record a demo of:

* Starting camera
* Detecting suspicious activity
* Alert popup
* Evidence clip saved

Then add:

```
![Demo](screenshots/demo.gif)
```

---

# Environment Variables

## Backend (.env)

```
JWT_SECRET=
JWT_EXPIRE_HOURS=

CORS_ORIGINS=

DATA_MODE=local
MONGO_URI=
MONGO_DB=

CAMERA_SOURCE=0

ALERTS_DIR=

SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=
ALERT_EMAIL_TO=
```

---

## Frontend (.env)

```
VITE_API_BASE_URL=http://localhost:5000
```

---

# Future Improvements

* YOLOv8 detection model
* Face recognition
* Mobile push notifications
* Cloud storage (AWS S3)
* Multi-camera monitoring
* WebSocket real-time alerts
* AI behavioral analysis

---

# Team

### Ankit Patel

* UI Development
* Flask integration
* JWT Authentication
* OpenCV integration
* System architecture

### Uttam Singh

* Backend development
* API implementation
* Server logic

### Yuvraj Jindal

* Alert system development
* Backend alert handling
* Notification system

---

# Contributing

Contributions are welcome.

Steps:

1. Fork the repository

2. Create a new branch

```
git checkout -b feature-name
```

3. Commit changes

```
git commit -m "Added new feature"
```

4. Push branch

```
git push origin feature-name
```

5. Open a Pull Request

---

# License

This project is developed for **educational and research purposes**.
>>>>>>> 6eb5a8a7cd5b654e6d331f58756a452c628c65ea
