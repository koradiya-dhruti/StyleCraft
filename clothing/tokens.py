import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from .models import Token, DeliveryToken
from django.http import JsonResponse

def create_token(user):

    current_time = datetime.now(timezone.utc)
    expiry_time = current_time + timedelta(days=30)

    payload = {
        'user_id' : user.id,
        'exp' : expiry_time,
        'iat' : current_time
    }

    token = jwt.encode (
        payload,
        settings.SECRET_KEY,
        algorithm = 'HS256'
    )

    Token.objects.create(
        user_id = user,
        token = token,
        expiry_time = expiry_time
    )

    return token

def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms = ["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return {"status":"error", "error" : "Toekn is Expired!"}
    except jwt.InvalidTokenError:
        return {"status":"error", "error" : "Toekn is Invalid!"}
    try:
        tokenobj = Token.objects.get(token=token)
        return payload["user_id"]
    except Token.DoesNotExist:
        return {'status':'error', 'error':'Token does not exist!'}

    # try:
        #     payload = jwt.decode(
        #         token,
        #         settings.SECRET_KEY,
        #         algorithms = ["HS256"]
        #     )
        #     try:
        #         tokenObj = Token.objects.get(token=token)s
        #     except Token.DoesNotExist:
        #         return JsonResponse({"error": "Token not found."}, status=401)
        #     return payload["user_id"]
        
        # except jwt.ExpiredSignatureError:
        #     return JsonResponse({"error": "Token Expired."}, status=401)
        #     # return None
        
        # except jwt.InvalidTokenError:
        #     return JsonResponse({"error": "Invalid Token."}, status=401)
        #     # return None

def create_delivery_token(deliveryPartner):

    current_time = datetime.now(timezone.utc)
    expiry_time = current_time + timedelta(days=30)

    payload = {
        'deliveryPartner_id' : deliveryPartner.id,
        'exp' : expiry_time,
        'iat' : current_time
    }

    token = jwt.encode (
        payload,
        settings.SECRET_KEY,
        algorithm = 'HS256'
    )

    DeliveryToken.objects.create(
        deliveryPartner_id = deliveryPartner,
        token = token,
        expiry_time = expiry_time
    )

    return token

def verify_delivery_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms = ["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return {"status":"error", "error" : "Toekn is Expired!"}
    except jwt.InvalidTokenError:
        return {"status":"error", "error" : "Toekn is Invalid!"}
    try:
        tokenobj = DeliveryToken.objects.get(token=token)
        return payload["deliveryPartner_id"]
    except Token.DoesNotExist:
        return {'status':'error', 'error':'Token does not exist!'}