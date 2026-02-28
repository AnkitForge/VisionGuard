# System Workflow - AI Crime Detection System

## Overview
This document describes the operational workflows of the AI Crime Detection System, including the complete process from video capture to alert notification.

## Primary Workflows

## 1. Real-Time Monitoring Workflow

### Step-by-Step Process

```
START
  ↓
1. System Initialization
   ├─ Load configuration
   ├─ Initialize cameras
   ├─ Load AI models
   └─ Start monitoring threads
  ↓
2. Video Capture Loop
   ├─ Capture frame from camera
   ├─ Add timestamp and metadata
   └─ Queue frame for processing
  ↓
3. Frame Preprocessing
   ├─ Resize frame
   ├─ Normalize colors
   ├─ Apply filters
   └─ Prepare for AI analysis
  ↓
4. AI Detection Phase
   ├─ Run YOLO object detection
   │  └─ Identify: persons, bags, items, vehicles
   ├─ Run behavior recognition
   │  └─ Classify: normal, suspicious
   ├─ Run anomaly detection
   │  └─ Check for unusual patterns
   └─ Collect results
  ↓
5. Decision Making
   ├─ Analyze detection confidence scores
   ├─ Compare against thresholds
   ├─ Determine alert severity
   └─ Generate alert decision
  ↓
6. Alert Triggered?
   ├─ YES → 7. Alert Generation
   └─ NO → 2. Video Capture Loop (Continue)
  ↓
7. Alert Generation
   ├─ Create alert record
   ├─ Assign ID and timestamp
   ├─ Determine severity level
   ├─ Link to camera and frame
   └─ Queue for notification
  ↓
8. Video Evidence Recording
   ├─ Extract video segment (5s before + 10s after)
   ├─ Compress video (H.264/H.265)
   ├─ Generate evidence metadata
   └─ Save to storage
  ↓
9. Notification Process
   ├─ Format alert message
   ├─ Select notification channels
   │  ├─ Email
   │  ├─ SMS
   │  └─ In-app notification
   ├─ Send notifications
   └─ Log notification status
  ↓
10. Data Persistence
    ├─ Store alert in database
    ├─ Store evidence metadata
    ├─ Log system event
    ├─ Update statistics
    └─ Cleanup old records
  ↓
11. Continue Monitoring
    └─ Return to Step 2: Video Capture Loop
```

## 2. Alert Management Workflow

### Alert Lifecycle

```
Alert Created
  ↓
1. Alert Validation
   ├─ Check alert authenticity
   ├─ Verify camera status
   ├─ Validate detection confidence
   └─ Assign severity level
  ↓
2. Alert Notification
   ├─ Send to shop owner's email
   ├─ Send SMS notification
   └─ Display in dashboard
  ↓
3. Awaiting Response
   ├─ Store in database
   ├─ Make available in alert log
   ├─ Set timer for timeout
   └─ Monitor response status
  ↓
4. Owner Actions
   ├─ VIEW ALERT
   │  ├─ Review video evidence
   │  ├─ Check confidence score
   │  ├─ Read incident description
   │  └─ Return to monitoring
   ├─ MARK AS RESOLVED
   │  ├─ Add notes/comments
   │  ├─ Update incident status
   │  └─ Close alert
   └─ INVESTIGATE FURTHER
      ├─ Download video
      ├─ Generate report
      └─ Contact security
  ↓
5. Alert Closure
   ├─ Update status to "Resolved"
   ├─ Archive alert record
   ├─ Store for compliance
   └─ Update statistics
```

## 3. Configuration Workflow

### System Setup Process

```
START
  ↓
1. Initial Setup
   ├─ Define store name
   ├─ Set location
   └─ Configure basic settings
  ↓
2. Camera Configuration
   ├─ Add camera details
   │  ├─ IP address/URL
   │  ├─ Resolution
   │  ├─ Frame rate
   │  └─ Location
   ├─ Test camera connection
   ├─ Verify video feed
   └─ Repeat for each camera
  ↓
3. AI Model Configuration
   ├─ Select detection model
   │  └─ YOLO v5/v8
   ├─ Set confidence threshold
   │  └─ Default: 70%
   ├─ Configure behavior recognition
   └─ Enable/disable anomaly detection
  ↓
4. Alert Settings Configuration
   ├─ Select notification channels
   ├─ Enter contact information
   │  ├─ Email address
   │  └─ Phone number
   ├─ Set alert delay
   └─ Configure alert filtering
  ↓
5. Storage Configuration
   ├─ Select storage type
   │  ├─ Local storage
   │  ├─ Cloud storage
   │  └─ Hybrid
   ├─ Set retention period
   ├─ Define storage location
   └─ Configure backup strategy
  ↓
6. Test & Validate
   ├─ Test camera connections
   ├─ Test AI models
   ├─ Test alert notifications
   └─ Verify storage access
  ↓
7. Save Configuration
   ├─ Store settings
   ├─ Create backup
   ├─ Update system
   └─ Restart monitoring
  ↓
END - System Ready
```

## 4. Evidence Management Workflow

### Video Evidence Lifecycle

```
Suspicious Activity Detected
  ↓
1. Video Segment Extraction
   ├─ Calculate segment boundaries
   │  ├─ Start: 5 seconds before event
   │  └─ End: 10 seconds after event
   ├─ Extract relevant frames
   └─ Validate segment integrity
  ↓
2. Video Compression
   ├─ Select codec (H.264/H.265)
   ├─ Apply quality settings
   ├─ Optimize file size
   └─ Generate compressed file
  ↓
3. Metadata Generation
   ├─ Create evidence record
   ├─ Include timestamps
   ├─ Add camera information
   ├─ Store detection data
   └─ Add forensic details
  ↓
4. Storage Assignment
   ├─ Local Storage Path
   │  ├─ Year/Month/Day structure
   │  ├─ Camera-specific folders
   │  └─ Format: YYYY-MM-DD_HH-MM-SS.mp4
   ├─ Cloud Storage Path (optional)
   └─ Database Reference
  ↓
5. Quality Verification
   ├─ Check file integrity
   ├─ Verify readability
   ├─ Validate metadata
   └─ Confirm storage success
  ↓
6. Access & Retrieval
   ├─ From Dashboard
   │  └─ View embedded player
   ├─ From Alert Log
   │  └─ Download option
   ├─ From Evidence Search
   │  └─ Advanced query
   └─ Via API
      └─ Programmatic access
  ↓
7. Archival & Retention
   ├─ Monitor retention period
   ├─ Archive after 30 days (configurable)
   ├─ Delete based on policy
   └─ Log deletion events
```

## 5. System Maintenance Workflow

### Periodic Maintenance Tasks

```
Daily Tasks
  ├─ Check system health
  ├─ Verify camera connectivity
  ├─ Monitor storage usage
  ├─ Review alerts count
  └─ Check for errors
    ↓
Weekly Tasks
  ├─ Backup database
  ├─ Review system logs
  ├─ Clean old temporary files
  ├─ Update system status report
  └─ Verify alert notification success
    ↓
Monthly Tasks
  ├─ Full system backup
  ├─ Performance analysis
  ├─ Review and adjust thresholds
  ├─ Update AI models (if needed)
  ├─ Compliance & audit review
  └─ Generate performance report
    ↓
Quarterly Tasks
  ├─ AI model retraining
  ├─ Security audit
  ├─ System optimization
  ├─ Equipment maintenance
  └─ Software updates
```

## 6. Troubleshooting Workflow

### System Issue Resolution

```
Issue Detected
  ↓
1. Identify Problem
   ├─ Check system logs
   ├─ Review error messages
   ├─ Note timestamp and details
   └─ Document symptoms
  ↓
2. Diagnose Issue
   ├─ Is it hardware related?
   │  ├─ Check CPU/RAM usage
   │  ├─ Monitor temperature
   │  └─ Verify power supply
   ├─ Is it software related?
   │  ├─ Check application logs
   │  ├─ Review recent changes
   │  └─ Check dependencies
   ├─ Is it network related?
   │  ├─ Test connectivity
   │  ├─ Check camera IPs
   │  └─ Verify bandwidth
   └─ Is it database related?
      ├─ Check database status
      ├─ Verify connections
      └─ Review queries
  ↓
3. Resolve Issue
   ├─ Apply appropriate fix
   ├─ Monitor recovery
   ├─ Verify functionality
   └─ Document solution
  ↓
4. Verify Resolution
   ├─ Run diagnostics
   ├─ Test all systems
   ├─ Check logs for new errors
   └─ Confirm normal operation
  ↓
5. Document & Learn
   ├─ Update issue log
   ├─ Note resolution steps
   ├─ Update procedures
   └─ Prevent future occurrences
```

## User Interaction Workflows

### Shop Owner Dashboard Usage

```
1. Login to Dashboard
   ├─ Enter credentials
   ├─ Authenticate
   └─ Load dashboard

2. Monitor System
   ├─ View live camera feeds
   ├─ Check real-time statistics
   ├─ Review recent alerts
   └─ Monitor system health

3. Review Alerts
   ├─ Click on alert
   ├─ View video evidence
   ├─ Read detection details
   ├─ Take action (resolve/investigate)
   └─ Add notes

4. Manage Settings
   ├─ Access settings page
   ├─ Update configurations
   ├─ Save changes
   └─ Restart if needed

5. Generate Reports
   ├─ Select date range
   ├─ Choose report type
   ├─ View report
   └─ Download/Export

6. Logout
   ├─ End session
   ├─ Save state
   └─ Secure session
```

## Error Handling Workflow

### Exception Management

```
Exception Occurs
  ↓
1. Catch Exception
   ├─ Log error details
   ├─ Record stack trace
   └─ Timestamp event
  ↓
2. Classify Error
   ├─ Critical (Stop operation)
   ├─ High (Alert immediately)
   ├─ Medium (Log and continue)
   └─ Low (Log only)
  ↓
3. Handle Error
   ├─ If Critical
   │  ├─ Stop current operation
   │  ├─ Alert administrator
   │  └─ Save state
   ├─ If High/Medium
   │  ├─ Log error
   │  ├─ Attempt recovery
   │  ├─ If recovery fails → retry
   │  └─ If retry fails → escalate
   └─ If Low
      └─ Log and continue
  ↓
4. Recovery
   ├─ Restart component
   ├─ Reset connections
   ├─ Clear caches
   └─ Resume operation
  ↓
5. Notification
   ├─ Alert admin if critical
   ├─ Update system status
   ├─ Log resolution
   └─ Continue monitoring
```

---
**Document Status**: Stage 0 - Foundation Phase
**Last Updated**: February 28, 2026
