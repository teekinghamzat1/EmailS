from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import io
import csv

import datetime
from app.db.session import get_db
from app.models.schema import Domain, Email, Pattern, SystemSettings
from app.worker.tasks import process_domain_task

router = APIRouter()

class DomainSeed(BaseModel):
    domains: List[str]

@router.post("/domains/seed")
def seed_domains(payload: DomainSeed, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest a list of domains.
    Creates them in the DB and dispatches Background Tasks to process them.
    """
    queued_domains = []
    for d in payload.domains:
        d = d.strip().lower()
        if not d:
            continue
            
        existing = db.query(Domain).filter(Domain.domain == d).first()
        if not existing:
            new_domain = Domain(domain=d)
            db.add(new_domain)
            db.commit()
            db.refresh(new_domain)
            
            # Send to FastAPI Background Tasks instead of Celery for local testing
            background_tasks.add_task(process_domain_task, new_domain.id)
            queued_domains.append(d)
            
    return {"status": "queued", "domains_added": queued_domains}

@router.get("/emails")
def get_emails(domain: str = None, status: str = None, db: Session = Depends(get_db)):
    query = db.query(Email)
    if domain:
        query = query.filter(Email.domain_rel.has(domain=domain))
    if status:
        query = query.filter(Email.status == status)
        
    emails = query.all()
    return [{"email": e.email, "domain": e.domain_rel.domain, "status": e.status, "confidence": e.confidence, "source": e.source} for e in emails]

@router.get("/emails/export")
def export_emails(db: Session = Depends(get_db)):
    """
    Export all valid emails to a downloadable CSV file.
    """
    emails = db.query(Email).filter(Email.status == "valid").all()
    
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Email", "Domain", "Source", "Confidence Level"])
    
    for e in emails:
        writer.writerow([e.email, e.domain_rel.domain, e.source, e.confidence])
        
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=verified_emails_export.csv"
    return response

@router.post("/emails/generate")
def generate_emails(db: Session = Depends(get_db)):
    """
    Fetch 1000 valid and unused emails, mark them as used, and return them.
    This is for the 'Generate' feature requested by the client.
    """
    emails = db.query(Email).filter(
        Email.status == "valid",
        Email.is_used == False
    ).limit(1000).all()
    
    if not emails:
        return []
        
    # Mark as used
    email_ids = [e.id for e in emails]
    db.query(Email).filter(Email.id.in_(email_ids)).update({"is_used": True}, synchronize_session=False)
    db.commit()
    
    return [
        {
            "email": e.email, 
            "domain": e.domain_rel.domain, 
            "source": e.source, 
            "confidence": e.confidence
        } for e in emails
    ]

@router.get("/admin/search")
def search_intelligence(q: str, db: Session = Depends(get_db)):
    q = q.strip().lower()

    # Smart detection: if the query looks like an email, extract the domain from it
    if "@" in q:
        search_domain = q.split("@")[1]
        # Also identify the specific person if it came from an email query
        queried_email = q
    else:
        search_domain = q
        queried_email = None

    # Find matching domains
    domains = db.query(Domain).filter(Domain.domain.contains(search_domain)).limit(10).all()

    results = []
    for d in domains:
        emails = db.query(Email).filter(Email.domain_id == d.id).all()
        patterns = db.query(Pattern).filter(Pattern.domain_id == d.id).all()

        total = len(emails)
        verified_count = sum(1 for e in emails if e.status == "valid")
        named_count    = sum(1 for e in emails if e.person_name)

        email_list = []
        for e in emails:
            is_queried = (queried_email == e.email.lower())
            email_list.append({
                "email":      e.email,
                "person":     e.person_name,
                "status":     e.status,
                "confidence": e.confidence,
                "is_used":    e.is_used,
                "is_queried": is_queried,  # highlight the original email the client searched
            })

        # Sort: put the queried email first, then named contacts, then the rest
        email_list.sort(key=lambda x: (not x["is_queried"], not bool(x["person"]), -x["confidence"]))

        results.append({
            "domain":         d.domain,
            "status":         d.status,
            "patterns":       list({p.inferred_pattern for p in patterns}),
            "total_emails":   total,
            "verified_count": verified_count,
            "named_count":    named_count,
            "emails":         email_list,
        })

    return results

@router.get("/admin/settings")
def get_admin_settings(db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    now = datetime.datetime.utcnow()
    start_of_month = datetime.datetime(now.year, now.month, 1)
    start_of_day = datetime.datetime(now.year, now.month, now.day)
    
    monthly_usage = db.query(Email).filter(Email.created_at >= start_of_month).count()
    daily_usage = db.query(Email).filter(Email.created_at >= start_of_day).count()
    
    return {
        "monthly_limit": settings.monthly_limit,
        "daily_limit": settings.daily_limit,
        "is_active": settings.is_active,
        "monthly_usage": monthly_usage,
        "daily_usage": daily_usage
    }

@router.patch("/admin/settings")
def update_admin_settings(payload: dict, db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings()
        db.add(settings)
        db.commit()
    
    if "monthly_limit" in payload:
        settings.monthly_limit = payload["monthly_limit"]
    if "daily_limit" in payload:
        settings.daily_limit = payload["daily_limit"]
    if "is_active" in payload:
        settings.is_active = payload["is_active"]
        
    db.commit()
    return {"status": "success", "settings": get_admin_settings(db)}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_domains = db.query(Domain).count()
    processing_domains = db.query(Domain).filter(Domain.status == "processing").count()
    completed_domains = db.query(Domain).filter(Domain.status == "completed").count()
    failed_domains = db.query(Domain).filter(Domain.status == "failed").count()
    
    total_emails = db.query(Email).count()
    valid_emails = db.query(Email).filter(Email.status == "valid").count()
    available_emails = db.query(Email).filter(Email.status == "valid", Email.is_used == False).count()
    used_emails = db.query(Email).filter(Email.is_used == True).count()
    pattern_emails = db.query(Email).filter(Email.source == "pattern").count()
    
    return {
        "domains": total_domains,
        "processing_domains": processing_domains,
        "completed_domains": completed_domains,
        "failed_domains": failed_domains,
        "total_emails": total_emails,
        "valid_emails": valid_emails,
        "available_emails": available_emails,
        "used_emails": used_emails,
        "pattern_emails": pattern_emails
    }

