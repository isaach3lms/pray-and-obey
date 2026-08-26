"""
Database models for Pray and Obey Ministries.

Two tables:
  users        - team members who can sign in to the portal
  applications - every grant application submitted through /apply
"""

import os
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, TypeDecorator
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class UTCDateTime(TypeDecorator):
    """SQLite silently drops timezone info. This forces UTC on both ends,
    so timestamps behave identically on SQLite locally and Postgres in
    production."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(UTCDateTime, default=utcnow, nullable=False)
    last_login_at = db.Column(UTCDateTime)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def is_active(self) -> bool:
        # Flask-Login reads this to block disabled accounts.
        return bool(self.is_active_user)

    def __repr__(self):
        return f"<User {self.email}>"


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

STATUSES = ["New", "Reviewed", "Approved", "Denied"]

STATUS_META = {
    "New": {"tone": "new", "label": "New"},
    "Reviewed": {"tone": "reviewed", "label": "Reviewed"},
    "Approved": {"tone": "approved", "label": "Approved"},
    "Denied": {"tone": "denied", "label": "Denied"},
}


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    submitted_at = db.Column(UTCDateTime, default=utcnow, nullable=False, index=True)

    # Workflow
    status = db.Column(db.String(20), default="New", nullable=False, index=True)
    reviewer_notes = db.Column(db.Text)
    status_changed_at = db.Column(UTCDateTime)
    status_changed_by = db.Column(db.String(120))

    # Section 1: organization and request
    legal_name = db.Column(db.String(255), nullable=False)
    dba_name = db.Column(db.String(255))
    ein = db.Column(db.String(40))
    year_founded = db.Column(db.String(20))
    org_website = db.Column(db.String(255))
    service_area = db.Column(db.String(255))
    contact_name = db.Column(db.String(255))
    email = db.Column(db.String(255), index=True)
    phone = db.Column(db.String(60))
    mailing_address = db.Column(db.String(400))
    org_type = db.Column(db.String(80))
    mission_activities = db.Column(db.Text)
    gospel_sharing = db.Column(db.Text)
    amount_requested = db.Column(db.String(60))
    total_project_budget = db.Column(db.String(60))
    start_date = db.Column(db.String(40))
    end_date = db.Column(db.String(40))
    project_summary = db.Column(db.Text)
    who_served = db.Column(db.Text)

    # Section 2: mission alignment and Bible distribution
    priorities = db.Column(db.Text)
    strongest_fit = db.Column(db.Text)
    activities_timeline = db.Column(db.Text)
    funds_use = db.Column(db.Text)
    bible_willingness = db.Column(db.String(80))
    bible_description = db.Column(db.Text)
    scripture_engagement = db.Column(db.Text)
    assistance = db.Column(db.Text)

    # Section 3: outcomes, finances, certification
    expected_results = db.Column(db.Text)
    sustainability = db.Column(db.Text)
    risks = db.Column(db.Text)
    budget_lines = db.Column(db.Text)
    budget_grand_total = db.Column(db.String(60))
    attachments = db.Column(db.Text)
    authorized_rep = db.Column(db.String(255))
    rep_title = db.Column(db.String(255))
    signature = db.Column(db.String(255))
    certified = db.Column(db.Boolean, default=False)

    @property
    def tone(self) -> str:
        return STATUS_META.get(self.status, {}).get("tone", "new")

    def __repr__(self):
        return f"<Application {self.id} {self.legal_name} [{self.status}]>"


# ---------------------------------------------------------------------------
# Connection string
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Uploaded documents
# ---------------------------------------------------------------------------

# Files are stored in the database rather than on disk. Render's web filesystem
# is ephemeral, so anything written there disappears on the next deploy. At this
# fund's volume the database is the correct home; if volume grows, move the
# `data` column to object storage and keep the rest of this table as the index.

MAX_FILE_BYTES = 10 * 1024 * 1024        # 10 MB per file
MAX_TOTAL_BYTES = 25 * 1024 * 1024       # 25 MB per application
MAX_FILES = 6

# Extension and content type must BOTH be allowed. Checking only one is how
# an executable or an SVG carrying script gets through.
ALLOWED_UPLOADS = {
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    },
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


class ApplicationFile(db.Model):
    __tablename__ = "application_files"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer,
        db.ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(120), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(UTCDateTime, default=utcnow, nullable=False)

    application = db.relationship(
        "Application",
        backref=db.backref(
            "files", cascade="all, delete-orphan", order_by="ApplicationFile.id"
        ),
    )

    @property
    def size_label(self) -> str:
        kb = self.size_bytes / 1024
        if kb < 1024:
            return f"{kb:.0f} KB"
        return f"{kb / 1024:.1f} MB"

    def __repr__(self):
        return f"<ApplicationFile {self.id} {self.filename}>"


def database_uri() -> str:
    """Postgres in production, SQLite locally.

    Render supplies DATABASE_URL beginning with postgres://, which
    SQLAlchemy 2.x no longer accepts. Rewrite the scheme.
    """
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url or "sqlite:///pray_and_obey.db"
