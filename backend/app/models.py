"""
models.py
─────────
SQLAlchemy ORM models for VisionGuard.
"""

import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def to_dict(self):
        return {"id": self.id, "email": self.email}


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(100), nullable=False, default="Shoplifting")
    confidence = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="high")
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True,
    )
    clip_filename = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "confidence": self.confidence,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() + "Z" if self.timestamp else None,
            "clip": self.clip_filename,
            "download_url": f"/api/evidence/{self.clip_filename}"
            if self.clip_filename
            else None,
        }
