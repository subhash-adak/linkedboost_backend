from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from ..config import settings
from ..database import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# def create_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + expires_delta
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
from ..config import settings  # already used above

def create_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def is_token_blacklisted(token: str):
    return await db.blacklisted_tokens.find_one({"token": token}) is not None


from jose import jwt, JWTError
from bson import ObjectId
from fastapi import Request, HTTPException
from ..config import settings

def get_user_id_from_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token payload missing 'sub'")
        return ObjectId(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# import hashlib
# import bcrypt

# def multi_encrypt(value: str, rounds: int = 10) -> str:
#     result = value.encode("utf-8")
#     for _ in range(rounds):
#         result = hashlib.sha256(result).digest()
#         result = bcrypt.hashpw(result, bcrypt.gensalt())
#     return result.decode()
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import hashlib
# 32-byte secret key using SHA-256 of JWT_SECRET
SECRET_KEY = hashlib.sha256(settings.JWT_SECRET.encode()).digest()

def encrypt_value(value: str) -> str:
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(value.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_value(encrypted: str) -> str:
    data = base64.b64decode(encrypted.encode())
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(SECRET_KEY, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()
