"""Database-backed school announcements and authenticated management."""

from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator

from ..database import announcements_collection
from .auth import require_teacher

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    expires_on: date
    starts_on: date | None = None

    @model_validator(mode="after")
    def validate_schedule(self):
        self.message = self.message.strip()
        if not self.message:
            raise ValueError("Message cannot be blank")
        if self.starts_on and self.starts_on > self.expires_on:
            raise ValueError("Start date must not be after expiration")
        return self

    def document(self):
        return {
            "message": self.message,
            "starts_on": self.starts_on.isoformat() if self.starts_on else None,
            "expires_on": self.expires_on.isoformat(),
        }


def serialize(document):
    return {"id": document["_id"], **{
        key: document.get(key) for key in ("message", "starts_on", "expires_on")
    }}


@router.get("")
def list_active(response: Response):
    """Public announcements, inclusive of both dates in UTC."""
    today = datetime.now(timezone.utc).date().isoformat()
    response.headers["Cache-Control"] = "no-store"
    documents = announcements_collection.find({
        "expires_on": {"$gte": today},
        "$or": [{"starts_on": None}, {"starts_on": {"$lte": today}}],
    }).sort([("expires_on", 1), ("_id", 1)])
    return [serialize(document) for document in documents]


@router.get("/manage", dependencies=[Depends(require_teacher)])
def list_all(response: Response):
    """Include scheduled and expired messages for signed-in teachers."""
    response.headers["Cache-Control"] = "no-store"
    return [serialize(document) for document in announcements_collection.find().sort([
        ("expires_on", -1), ("_id", 1)
    ])]


@router.post("", status_code=201, dependencies=[Depends(require_teacher)])
def create_announcement(announcement: AnnouncementInput):
    document = {"_id": str(uuid4()), **announcement.document()}
    announcements_collection.insert_one(document)
    return serialize(document)


@router.put("/{announcement_id}", dependencies=[Depends(require_teacher)])
def update_announcement(announcement_id: str, announcement: AnnouncementInput):
    result = announcements_collection.update_one(
        {"_id": announcement_id}, {"$set": announcement.document()}
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"id": announcement_id, **announcement.document()}


@router.delete("/{announcement_id}", status_code=204, dependencies=[Depends(require_teacher)])
def delete_announcement(announcement_id: str):
    result = announcements_collection.delete_one({"_id": announcement_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Announcement not found")