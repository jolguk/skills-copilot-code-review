"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from pydantic import BaseModel, Field

from ..database import teachers_collection, sessions_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


class LoginCredentials(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


def require_teacher(request: Request) -> Dict[str, Any]:
    token = request.cookies.get("school_session", "")
    session = sessions_collection.find_one({
        "_id": sha256(token.encode()).hexdigest(),
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    }) if token else None
    teacher = teachers_collection.find_one({"_id": session["username"]}) if session else None
    if not teacher:
        raise HTTPException(status_code=401, detail="Sign in required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if (origin and origin != str(request.base_url).rstrip("/")) or request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(status_code=403, detail="Request not allowed")
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
    }


@router.post("/login")
def login(credentials: LoginCredentials, request: Request, response: Response) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": credentials.username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), credentials.password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    previous_token = request.cookies.get("school_session")
    if previous_token:
        sessions_collection.delete_one({"_id": sha256(previous_token.encode()).hexdigest()})
    token = token_urlsafe(32)
    sessions_collection.insert_one({
        "_id": sha256(token.encode()).hexdigest(),
        "username": teacher["username"],
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=8),
    })
    response.set_cookie("school_session", token, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", max_age=8 * 60 * 60)

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.get("/check-session")
def check_session(teacher: Dict[str, Any] = Depends(require_teacher)) -> Dict[str, Any]:
    """Check the authenticated session."""
    return teacher


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, teacher=Depends(require_teacher)):
    token = request.cookies.get("school_session", "")
    sessions_collection.delete_one({"_id": sha256(token.encode()).hexdigest()})
    response.delete_cookie("school_session")
