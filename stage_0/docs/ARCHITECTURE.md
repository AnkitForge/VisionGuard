# System Architecture - AI Crime Detection System

## Overview
The AI Crime Detection System for Supermarkets is designed with a modular, scalable architecture that separates concerns across different processing layers. This document outlines the system architecture and component interactions.

## Architecture Layers

### 1. **Data Acquisition Layer**
Handles input from CCTV cameras and video sources.

- **CCTV Camera Module**
  - Captures live video feeds from surveillance cameras
  - Supports multiple camera inputs (up to 16 cameras)
  - Resolution: 1280x720 (720p) to 3840x2160 (4K)
  - Frame Rate: 15-60 FPS (configurable)

- **Input Sources**
  - IP/Network Cameras
  - USB Webcams
  - RTSP/RTMP Streams
  - Local Video Files (for testing)

### 2. **Video Processing Layer**
Processes video frames and prepares them for AI analysis.

- **Frame Extraction**
  - Continuous frame capture from video streams
  - Frame buffering and queue management
  - Resolution optimization

- **Preprocessing**
  - Frame normalization
  - Color space conversion (BGR to RGB)
  - Noise reduction
  - Image enhancement

### 3. **AI Detection Layer**
Core machine learning and computer vision components.

- **Object Detection Module**
  - YOLO (You Only Look Once) models
  - Object identification: Persons, bags, containers, items
  - Real-time bounding box generation
  - Confidence scoring

- **Behavior Recognition Module**
  - Activity classification
  - Gesture detection
  - Pose estimation
  - Trajectory tracking

- **Anomaly Detection Module**
  - Statistical analysis
  - Pattern recognition
  - Unusual behavior identification
  - Outlier detection

### 4. **Alert & Notification Layer**
Manages alerts and notifications.

- **Alert Generator**
  - Processes detection results
  - Determines alert severity (Critical, High, Medium, Low)
  - Alert deduplication
  - Alert throttling

- **Notification Channel**
  - Email notifications
  - SMS alerts
  - In-app notifications
  - Webhook integration

### 5. **Storage Layer**
Handles video evidence and data storage.

- **Local Storage**
  - Short-term video evidence storage
  - Event metadata storage
  - Log files

- **Cloud Storage** (Optional)
  - Long-term archival
  - Redundancy
  - Off-site backup

- **Database**
  - Alert records
  - Camera configurations
  - Detection logs
  - User activity logs

### 6. **User Interface Layer**
Web-based dashboard for monitoring and management.

- **Dashboard**
  - Live camera feed display
  - Real-time statistics
  - Alert log
  - System status

- **Administration Panel**
  - Camera configuration
  - Alert settings
  - Storage management
  - User preferences

## System Components Interaction

```
CCTV Cameras
    ↓
Video Input Module
    ↓
Frame Extraction & Buffering
    ↓
Video Preprocessing
    ↓
AI Detection Engine
    ├── Object Detection (YOLO)
    ├── Behavior Recognition (TensorFlow)
    └── Anomaly Detection
    ↓
Alert Decision Engine
    ↓
│   ├→ Email/SMS Notification
    ├→ In-app Alert
    └→ Logging System
    ↓
Storage Module
    ├→ Local Storage
    ├→ Cloud Storage
    └→ Database
    ↓
Web Dashboard
    ├→ Live Monitoring
    ├→ Alert Review
    └→ System Management
```

## Technology Stack

### Backend (Python)
- **Framework**: Flask / Django
- **AI/ML**: TensorFlow 2.x, PyTorch
- **Computer Vision**: OpenCV 4.5+
- **Object Detection**: YOLO v5/v8, Ultralytics
- **Database**: PostgreSQL / MongoDB
- **Task Queue**: Celery
- **Web Server**: Gunicorn / uWSGI

### Frontend (Web UI)
- **HTML5**, **CSS3**, **JavaScript**
- **Framework**: React / Vue.js (optional for future stages)
- **WebSocket**: Real-time updates
- **REST API**: Backend communication

### Infrastructure
- **OS**: Linux (Ubuntu 20.04+) / Windows
- **Container**: Docker
- **Orchestration**: Docker Compose / Kubernetes
- **Hardware**: GPU support (NVIDIA CUDA recommended)

### Dependencies
```
Python Libraries:
- opencv-python==4.5+
- tensorflow==2.10+
- torch==2.0+
- ultralytics==8.0+
- numpy==1.20+
- pandas==1.3+
- scikit-learn==1.0+
- flask==2.0+
- celery==5.0+
- pillow==8.0+
- requests==2.26+
- pydantic==1.8+
```

## Data Flow

### Alert Generation Flow
1. Video frame captured from camera
2. Frame sent to preprocessing module
3. Preprocessed frame analyzed by YOLO (object detection)
4. Objects passed to behavior recognition model
5. Anomaly detection checks for unusual patterns
6. If suspicious activity detected:
   - Alert triggered
   - Severity level assigned
   - Video segment recorded
   - Notification sent to owner
   - Event logged to database

### Storage Flow
1. Suspicious activity detected
2. Video segment extracted (5-10 seconds before and after)
3. Video compressed for storage efficiency
4. Metadata generated (timestamp, duration, location)
5. Stored to local storage (immediate)
6. Replicated to cloud storage (if configured)
7. Retention policy applied (30-days default)
8. Older files automatically deleted after retention period

## Module Dependencies

### Critical Dependencies
- **OpenCV**: Video capture and processing
- **YOLO**: Real-time object detection
- **TensorFlow**: Behavior recognition and anomaly detection
- **Flask/Django**: Web framework for API and UI

### Optional Dependencies
- **Pytorch**: Alternative ML framework
- **Redis**: Caching and task queue
- **PostgreSQL**: Database
- **Docker**: Containerization

## Performance Metrics

### Target Performance (Stage 1+)
- **Detection Latency**: < 500ms per frame
- **Total System Latency**: < 2 seconds (capture to alert)
- **Throughput**: 30+ FPS per camera
- **Accuracy**: > 85% for theft detection
- **False Positive Rate**: < 5%
- **Availability**: 99% uptime

## Scalability Considerations

### Horizontal Scaling
- Multiple processing nodes
- Load balancing for cameras
- Distributed alert system
- Cloud storage for archival

### Vertical Scaling
- GPU acceleration
- Multi-threading for frame processing
- Database optimization
- Caching layer integration

## Security Architecture

### Authentication & Authorization
- Role-based access control (RBAC)
- User authentication (username/password)
- Session management
- API token authentication

### Data Security
- Encryption at rest (AES-256)
- Encryption in transit (TLS/SSL)
- Secure password hashing (bcrypt)
- API key management

### Video Security
- Watermarking of recorded evidence
- Audit trails for video access
- Secure deletion of recordings
- Compliance with privacy regulations

## Future Enhancements

### Phase 2 Enhancements
- Face recognition capabilities
- Mobile application
- Multi-site management
- Advanced analytics dashboard

### Phase 3 Enhancements
- Cloud-based monitoring
- API marketplace integration
- Machine learning model improvements
- Integration with law enforcement

---
**Document Status**: Stage 0 - Foundation Phase
**Last Updated**: February 28, 2026
