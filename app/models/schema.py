import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="queued", index=True) # queued, processing, completed, failed
    priority = Column(Float, default=1.0)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    emails = relationship("Email", back_populates="domain_rel")
    patterns = relationship("Pattern", back_populates="domain_rel")

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"))
    status = Column(String, default="unknown", index=True) # valid, invalid, risky, unknown
    confidence = Column(Float, default=0.0) # 0.0 to 1.0 (High, Medium, Low equivalent)
    source = Column(String, nullable=False) # e.g. scraper, pattern
    is_used = Column(Boolean, default=False, index=True)
    person_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    domain_rel = relationship("Domain", back_populates="emails")

class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"))
    inferred_pattern = Column(String, nullable=False) # e.g. first.last
    source_email = Column(String, nullable=False)

    domain_rel = relationship("Domain", back_populates="patterns")

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    monthly_limit = Column(Integer, default=50000)
    daily_limit = Column(Integer, default=5000)
    is_active = Column(Boolean, default=True)
    last_reset_date = Column(DateTime, default=datetime.datetime.utcnow)

