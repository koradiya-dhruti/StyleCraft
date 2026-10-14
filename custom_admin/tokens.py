import hashlib
from datetime import timedelta, datetime, timezone
from clothing.models import AdminUser, AdminToken
import jwt
from django.conf import settings
from clothing.models import AdminToken


def create_admin_token(admin):

    current_time = datetime.now(timezone.utc)
    expiry_time = current_time + timedelta(days=30)

    payload = {
        "user_id": admin.id,
        "exp": expiry_time,
        "iat": current_time
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    AdminToken.objects.create(
        user_id=admin,
        token=token,
        expiry_time=expiry_time
    )

    return token



def verify_admin_token(token):

    if not token:
        return {
            "status": "error",
            "message": "Token is required."
        }

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )

        admin_token = AdminToken.objects.get(
            token=token,
            expiry_time__gt=datetime.now(timezone.utc)
        )

        if admin_token.user_id_id != payload.get("user_id"):
            return {
                "status": "error",
                "message": "Invalid token."
            }

        return admin_token.user_id

    except jwt.ExpiredSignatureError:
        AdminToken.objects.filter(token=token).delete()

        return {
            "status": "error",
            "message": "Token has expired."
        }

    except jwt.InvalidTokenError:
        return {
            "status": "error",
            "message": "Invalid token."
        }

    except AdminToken.DoesNotExist:
        return {
            "status": "error",
            "message": "Token does not exist or has been revoked."
        }



def delete_admin_token(token):

    if not token:
        return False

    deleted_count, details = AdminToken.objects.filter(
        token=token
    ).delete()

    return deleted_count > 0
