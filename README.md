# VisionGuard - AI-Based Crime Detection System for Supermarkets

An intelligent surveillance solution that uses AI and computer vision to detect suspicious activities and potential theft in supermarkets using CCTV cameras.

---

## Team Members

| Name | University Roll Number |
|------|------------------------|
| Uttam Singh | 2415500494 |
| Yuvraj Jindal | 2315510118 |
| Ankit Patel | 2415500074 |

---

## Table of Contents

- [Abstract](#abstract)
- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives-of-the-project)
- [Proposed Methodology](#proposed-methodology)
- [System Architecture](#system-architecture)
- [Tools and Technologies](#tools-and-technologies-used)
- [Applications](#applications)
- [Expected Outcomes](#expected-outcomes)
- [Future Scope](#future-scope)
- [Conclusion](#conclusion)

---

## Abstract

Shoplifting and theft are major challenges faced by supermarkets and retail stores. Although CCTV cameras are widely used, continuous manual monitoring is difficult and inefficient. This project proposes an AI-based crime detection system that continuously monitors customer activities using CCTV cameras. When suspicious behavior or theft-related activity is detected, the system automatically generates an alert and records a short video clip. This alert and video evidence are sent to the shop owner to enable quick response and preventive action.

---

## Introduction

With the rapid growth of retail businesses, ensuring customer and product security has become increasingly important. Supermarkets often experience financial losses due to shoplifting and theft. Traditional security methods rely heavily on security guards and manual CCTV monitoring, which are prone to human error. Artificial Intelligence and Computer Vision provide an opportunity to automate surveillance and improve security systems. This project focuses on designing a smart system that can analyze live video feeds and detect suspicious activities in real time.

---

## Problem Statement

Existing security systems in supermarkets have several limitations:

- Manual monitoring of CCTV footage is time-consuming and requires continuous attention
- In crowded environments, theft incidents may go unnoticed
- Security personnel may miss critical moments due to fatigue or distraction

Therefore, there is a strong need for an automated crime detection system that can monitor activities continuously and alert authorities instantly.

---

## Objectives of the Project

The primary objectives of this project are:

- To continuously monitor customer activities using CCTV cameras
- To automatically detect suspicious or theft-related behavior
- To generate real-time alerts for shop owners
- To record and store short video clips as evidence
- To reduce dependency on manual monitoring

---

## Proposed Methodology

The proposed system captures live video streams from CCTV cameras installed inside the supermarket. Each video frame is processed using computer vision techniques. Machine learning models such as object detection and activity recognition are used to identify suspicious behavior. When an abnormal activity is detected, the system triggers an alarm and starts recording a short video clip. The recorded clip and alert notification are then sent to the shop owner through an alert system.

---

## System Architecture

The system architecture consists of the following components:

- **CCTV Cameras**: Capture video input
- **Processing Unit**: Handles video stream processing
- **AI Model**: Analyzes frames for suspicious activities
- **Alert Module**: Sends notifications to shop owner

This modular design allows easy upgrades and scalability.

---

## Tools and Technologies Used

| Component | Technology |
|-----------|-----------|
| **Programming Language** | Python |
| **Computer Vision** | OpenCV |
| **Object Detection** | YOLO |
| **Deep Learning** | TensorFlow |
| **Hardware** | CCTV Camera / Webcam |
| **Storage** | Local Storage / Cloud Storage |
| **Alert System** | Email Notification / Alarm System |

**Key Techniques**: Object Detection, Activity Recognition

---

## Applications

This system can be implemented in various environments such as:

- Supermarkets
- Retail stores
- Shopping malls
- Warehouses
- Departmental stores
- Other public places requiring surveillance

---

## Expected Outcomes

The expected outcomes of this project include:

✓ Accurate detection of theft activities  
✓ Reduced financial losses for shop owners  
✓ Faster response time to security incidents  
✓ Improved overall security infrastructure  
✓ Video evidence for investigation purposes

---

## Future Scope

Future enhancements of this project may include:

- Face recognition capabilities
- Mobile application alerts
- Cloud-based storage integration
- Integration with law enforcement systems
- Improved accuracy using advanced deep learning models
- Real-time dashboard for monitoring
- Multi-camera integration and coordination

---

## Conclusion

The AI-based crime detection system provides an effective and automated solution for supermarket security. By reducing manual effort and improving detection accuracy, the system helps shop owners prevent theft and maintain a safe environment. This project demonstrates the practical application of AI and computer vision in real-world security problems.

---

## Getting Started

For setup and installation instructions, refer to [GETTING_STARTED.md](./stage_0/GETTING_STARTED.md)

For project architecture details, see [ARCHITECTURE.md](./stage_0/docs/ARCHITECTURE.md)
