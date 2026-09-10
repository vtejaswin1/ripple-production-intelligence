import firebase_admin
from firebase_admin import auth, credentials

from fastapi import Header, HTTPException


def _initialize_firebase():
    if firebase_admin._apps:
        return

    # Uses Google Application Default Credentials (ADC),
    # which you already configured on this machine.
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(
        cred,
        {
            "projectId": "ripple-production-intelligence",
        },
    )


_initialize_firebase()


def get_current_user(
    authorization: str | None = Header(default=None),
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header.",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
        }

    except Exception as exc:
        print("Firebase token verification failed:", exc)

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token.",
        )