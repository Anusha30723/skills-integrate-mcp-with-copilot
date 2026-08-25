"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import base64
import hashlib
import hmac
import secrets
import time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

TOKEN_TTL_SECONDS = 60 * 60 * 8
PASSWORD_ITERATIONS = 600_000
TOKEN_SECRET = secrets.token_bytes(32)
users = {}
sessions = {}
bearer_scheme = HTTPBearer(auto_error=False)


class AuthRequest(BaseModel):
    email: str
    password: str


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ITERATIONS
    )
    return f"{salt.hex()}${password_hash.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, expected_hash = stored_hash.split("$", 1)
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(actual_hash.hex(), expected_hash)


def _create_token(email: str) -> str:
    expires_at = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{email}|{expires_at}".encode()
    encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(TOKEN_SECRET, encoded_payload.encode(), hashlib.sha256).hexdigest()
    token = f"{encoded_payload}.{signature}"
    sessions[token] = email
    return token


def _get_authenticated_email(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            TOKEN_SECRET, encoded_payload.encode(), hashlib.sha256
        ).hexdigest()
        payload = base64.urlsafe_b64decode(encoded_payload + "===").decode()
        email, expires_at = payload.rsplit("|", 1)
        expires_at = int(expires_at)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    if expires_at < int(time.time()) or sessions.get(token) != email:
        raise HTTPException(status_code=401, detail="Authentication token expired")
    return email


@app.post("/auth/register", status_code=201)
def register(request: AuthRequest):
    email = request.email.strip().lower()
    if "@" not in email or not request.password:
        raise HTTPException(status_code=400, detail="A valid email and password are required")
    if email in users:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    users[email] = _hash_password(request.password)
    return {"message": "Account created", "email": email}


@app.post("/auth/login")
def login(request: AuthRequest):
    email = request.email.strip().lower()
    stored_hash = users.get(email)
    if stored_hash is None or not _verify_password(request.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"access_token": _create_token(email), "token_type": "bearer", "email": email}


@app.post("/auth/logout")
def logout(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    _get_authenticated_email(credentials)
    sessions.pop(credentials.credentials, None)
    return {"message": "Logged out"}

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: Annotated[str, Depends(_get_authenticated_email)],
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: Annotated[str, Depends(_get_authenticated_email)],
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
