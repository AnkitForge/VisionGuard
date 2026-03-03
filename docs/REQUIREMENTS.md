# System Requirements - AI Crime Detection System

## Overview
This document outlines the system requirements for the AI Crime Detection System for Supermarkets, including hardware specifications, software dependencies, and environmental prerequisites.

## Hardware Requirements

### Minimum Hardware (Single Camera, Basic Setup)
- **CPU**: Intel i5 / AMD Ryzen 5 (6-core, 2.4 GHz minimum)
- **RAM**: 8 GB DDR4
- **Storage**: 256 GB SSD
- **GPU**: NVIDIA GTX 1050 (2 GB VRAM) or equivalent
- **Network**: Gigabit Ethernet (RJ-45)
- **Power**: 400W PSU (UPS recommended)

### Recommended Hardware (Multi-Camera, Production Setup)
- **CPU**: Intel i7/i9 or AMD Ryzen 7/9 (8+ cores, 3.5+ GHz)
- **RAM**: 32 GB DDR4
- **Storage**: 1 TB+ SSD (NVMe recommended)
- **GPU**: NVIDIA RTX 2080 Ti / RTX 3090 (8+ GB VRAM)
- **Network**: 10 Gbps Ethernet or dedicated network
- **Power**: 1000W+ PSU with UPS (24/7 operation)

### Storage Requirements
- **Video Storage**: 500 GB - 2 TB (depending on retention policy)
  - 4 cameras × 30 days retention × 24 hours = ~500 GB
  - 8 cameras × 30 days retention × 24 hours = ~1 TB
- **Operating System**: 50 GB
- **Applications/ML Models**: 50 GB
- **Database**: 10-50 GB
- **Backup/Redundancy**: 100% of video storage

## Software Requirements

### Operating System
- **Primary**: Ubuntu 20.04 LTS or later
- **Secondary**: Windows 10/11 Pro (with WSL2)
- **Alternative**: CentOS 8 / RHEL 8+

### Python Environment
- **Python Version**: 3.8, 3.9, 3.10, or 3.11
- **Package Manager**: pip 21.0+
- **Virtual Environment**: venv or conda

### Core Dependencies

#### Computer Vision & ML Libraries
```
opencv-python==4.5.4+
tensorflow==2.10.0+
torch==2.0.0+
torchvision==0.15.0+
ultralytics==8.0.0+
```

#### Data Processing
```
numpy==1.21.0+
pandas==1.3.0+
scipy==1.7.0+
scikit-learn==1.0.0+
scikit-image==0.18.0+
```

#### Web Framework & API
```
flask==2.0.0+
flask-cors==3.0.10+
flask-sqlalchemy==2.5.0+
gunicorn==20.1.0+
```

#### Database
```
psycopg2-binary==2.9.0+
sqlalchemy==1.4.0+
pymongo==4.1.0+ (optional)
```

#### Messaging & Notifications
```
celery==5.1.0+
redis==4.1.0+ (optional)
python-dotenv==0.19.0+
requests==2.26.0+
```

#### Utilities
```
Pillow==8.3.0+
python-dateutil==2.8.2+
pydantic==1.8.0+
tqdm==4.62.0+
```

### System Services
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **cURL**: 7.68+

## Database Requirements

### Primary Database (PostgreSQL)
- **Version**: PostgreSQL 12+
- **User Roles**: 
  - `admin` - Full access
  - `app_user` - Application access
  - `reader` - Read-only access

### Database Schemas
```sql
-- Users & Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cameras
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    ip_address VARCHAR(15),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    alert_type VARCHAR(100),
    severity VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    processed BOOLEAN DEFAULT FALSE
);

-- Evidence
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    video_path VARCHAR(255),
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Network Requirements

### Bandwidth
- **CCTV Cameras Bandwidth**:
  - Per 1080p camera @ 30 FPS: 5 Mbps minimum
  - Per 4K camera @ 30 FPS: 15 Mbps minimum
  - 4 cameras (1080p): 20 Mbps minimum
  - 8 cameras (1080p): 40 Mbps minimum

### Network Connectivity
- **Minimum Internet Speed**: 10 Mbps upload/download
- **Network Protocol**: Ethernet (CAT6/CAT6a recommended)
- **Wireless**: Not recommended for camera feeds
- **Latency**: < 50ms for local network

### Firewall & Security
- **Essential Ports**:
  - Port 80: HTTP (UI)
  - Port 443: HTTPS (Encrypted UI)
  - Port 5432: PostgreSQL (Internal only)
  - Port 6379: Redis (Internal only, if used)
  - Port 8000-8100: Application servers

## CCTV Camera Specifications

### Supported Camera Types
- **IP Cameras**: RTSP/RTMP streaming
- **USB Cameras**: Webcams
- **Network Video Recorders**: NVR feeds
- **DVR Systems**: Multicast streams

### Camera Configuration
- **Resolution**: 1280x720 minimum, 1920x1080 recommended
- **Frame Rate**: 15-30 FPS standard, 60 FPS optional
- **Codec**: H.264, H.265
- **Connectivity**: Ethernet (RJ45)
- **Power**: PoE (Power over Ethernet) recommended

## Browser Requirements

### Supported Browsers
- **Chrome**: Version 90+
- **Firefox**: Version 88+
- **Safari**: Version 14+
- **Edge**: Version 90+

### Browser Features Required
- HTML5 support
- WebSocket support
- LocalStorage support
- Canvas rendering

## Storage & Archival

### Local Storage
- **Primary**: SSD for active monitoring
- **Secondary**: HDD for archival (optional)
- **Backup**: External hard drive (weekly)

### Retention Policy
- **Active Storage**: 30 days (configurable)
- **Archival Storage**: 90 days (optional)
- **Permanent Records**: 1 year for critical incidents

### Storage Redundancy
- **RAID Configuration**: RAID 5 or RAID 6 recommended
- **Backup Strategy**: Hourly incremental, daily full backup
- **Offsite Backup**: Weekly cloud backup

## Power Requirements

### UPS (Uninterruptible Power Supply)
- **Capacity**: 5-10 kVA for complete system
- **Backup Time**: Minimum 30 minutes
- **Battery Type**: Lithium-ion recommended

### Power Management
- **Surge Protection**: 6-outlet PDU with surge protection
- **Monitoring**: Real-time power consumption tracking
- **Failover**: Automatic switchover to UPS on power loss

## Environmental Requirements

### Climate Control
- **Temperature**: 10-35°C (50-95°F)
- **Humidity**: 20-80% (non-condensing)
- **Ventilation**: Adequate airflow for cooling

### Physical Space
- **Rack Space**: 3-5 RU for server hardware
- **Dimensions**: Compact form factor preferred
- **Cooling**: Active cooling system (if in closed rack)

## Performance Benchmarks

### Target Specifications (Stage 1+)
- **Frame Processing**: 30+ FPS per camera
- **Detection Latency**: < 500ms
- **Alert Generation**: < 2 seconds
- **UI Responsiveness**: < 1 second per action
- **Database Query Time**: < 100ms average

### Resource Utilization
- **CPU Usage**: 40-60% under normal operation
- **RAM Usage**: 4-8 GB under normal operation
- **Disk I/O**: < 100 MB/s average
- **Network I/O**: See bandwidth requirements

## Compliance & Standards

### Video Surveillance Standards
- **ONVIF Profile S**: For IP camera compatibility
- **RTSP**: Real Time Streaming Protocol
- **MJPEG**: Motion JPEG streaming

### Security Standards
- **OWASP**: Web application security
- **ISO 27001**: Information security management
- **GDPR**: General Data Protection Regulation compliance
- **HIPAA**: Health Insurance Portability and Accountability Act (if applicable)

## Testing Requirements

### Unit Testing
- Python pytest framework
- Minimum 70% code coverage

### Integration Testing
- Multi-camera coordination
- Database operations
- Real-time processing

### Load Testing
- 100+ simultaneous connections
- 8+ concurrent camera processing
- Peak alert scenario handling

## Development Environment

### Required Tools
- **IDE**: VS Code, PyCharm, or similar
- **Version Control**: Git
- **Documentation**: Markdown
- **API Testing**: Postman or similar

### Development Workflow
- Feature branches
- Pull request reviews
- Continuous Integration (GitHub Actions, GitLab CI)
- Automated testing

---
**Document Status**: Stage 0 - Foundation Phase
**Last Updated**: February 28, 2026
