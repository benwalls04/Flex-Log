import jwt
import os

def lambda_handler(event, context):
    # HTTP API (v2) passes token(s) in identitySource (e.g. from Authorization header)
    identity_sources = event.get("identitySource") or []
    token = identity_sources[0] if identity_sources else None
    if not token:
        return {"isAuthorized": False}

    # Strip "Bearer " if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(
            token,
            os.environ["SUPABASE_JWT_SECRET"],
            algorithms=["HS256"],
            audience="authenticated",
        )
        sub = payload.get("sub")
        if not sub:
            return {"isAuthorized": False}

        # HTTP API (v2) format: isAuthorized + context (context values must be strings)
        return {
            "isAuthorized": True,
            "context": {
                "user_id": str(sub),
            },
        }
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return {"isAuthorized": False}
    except Exception:
        return {"isAuthorized": False}
