from fastapi import APIRouter, HTTPException
from ..schemas import RegisterUser, LoginUser
from ..database import db
from ..auth.utils import hash_password, verify_password, create_token
from ..auth.email_verification import send_reset_otp, send_verification_email
import uuid
import random, string
from fastapi import Request, Body
from ..auth.email_verification import send_verification_email  # reusing for OTP email
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr


from fastapi import APIRouter, HTTPException, Depends
from ..schemas import RegisterUser, LoginUser, GoogleAuthRequest, GoogleAccessTokenRequest
from ..database import db
from ..auth.utils import create_token
from ..auth.google_auth import GoogleAuth
from bson import ObjectId
import uuid
from datetime import datetime
# Add this import at the top of your routes.py file
from ..auth.utils import get_user_id_from_token

# Here's your corrected routes.py with all the missing imports:
from fastapi import APIRouter, HTTPException, Request, Body
from ..schemas import (
    RegisterUser, LoginUser, GoogleAuthRequest, GoogleAccessTokenRequest,
    ResendEmailRequest, DeepEncryptInput, CampaignConfig
)
from ..database import db
from ..auth.utils import (
    hash_password, verify_password, create_token, 
    get_user_id_from_token, encrypt_value, decrypt_value
)
from ..auth.email_verification import send_reset_otp, send_verification_email
from ..auth.google_auth import GoogleAuth
from ..auth.linkedin_connector import LinkedInConnector
import uuid
import random
import string
from datetime import datetime, timedelta
from bson import ObjectId
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Initialize Google Auth
google_auth = GoogleAuth()

# Your existing routes continue here...
# (I notice you have the link-google-account and unlink-google-account routes 
# but they're missing the import for get_user_id_from_token)

@router.post("/link-google-account")
async def link_google_account(request: GoogleAuthRequest, current_user_request: Request):
    """Link Google account to existing user"""
    try:
        # Get current user
        user_id = get_user_id_from_token(current_user_request)
        
        # Verify Google token
        google_user = await google_auth.verify_google_token(request.id_token)
        
        # Check if Google account is already linked to another user
        existing_google_user = await db.users.find_one({"google_id": google_user['google_id']})
        if existing_google_user and str(existing_google_user["_id"]) != str(user_id):
            raise HTTPException(
                status_code=400, 
                detail="This Google account is already linked to another user"
            )
        
        # Link Google account to current user
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "google_id": google_user['google_id'],
                    "picture": google_user['picture'],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"msg": "Google account linked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/unlink-google-account")
async def unlink_google_account(current_user_request: Request):
    """Unlink Google account from current user"""
    try:
        user_id = get_user_id_from_token(current_user_request)
        
        # Check if user has a password (to ensure they can still login)
        user = await db.users.find_one({"_id": user_id})
        if not user.get("hashed_password"):
            raise HTTPException(
                status_code=400,
                detail="Cannot unlink Google account. Please set a password first."
            )
        
        # Unlink Google account
        await db.users.update_one(
            {"_id": user_id},
            {
                "$unset": {"google_id": "", "picture": ""},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {"msg": "Google account unlinked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
google_auth = GoogleAuth()

# @router.post("/google-auth")
# async def google_login(request: GoogleAuthRequest):
#     try:
#         google_user = await google_auth.verify_google_token(request.id_token)

#         user = await db.users.find_one({"email": google_user["email"]})

#         if not user:
#             user_data = {
#                 "email": google_user["email"],
#                 "name": google_user["name"],
#                 "google_id": google_user["google_id"],
#                 "picture": google_user.get("picture", ""),
#                 "is_verified": True,
#                 "created_at": datetime.utcnow(),
#                 "updated_at": datetime.utcnow()
#             }
#             result = await db.users.insert_one(user_data)
#             user_id = result.inserted_id
#         else:
#             user_id = user["_id"]

#         access_token = create_token({"sub": str(user_id)})

#         return {
#             "access_token": access_token,
#             "email": google_user["email"],
#             "name": google_user["name"]
#         }

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Google sign-in failed: {str(e)}")


@router.post("/google-login")
async def google_login_only(request: GoogleAuthRequest):
    """
    Google Sign-In for LOGIN page only - does NOT create new users
    """
    try:
        google_user = await google_auth.verify_google_token(request.id_token)

        # Check if user exists - DO NOT CREATE if not found
        user = await db.users.find_one({"email": google_user["email"]})

        if not user:
            # User doesn't exist - return error instead of creating
            raise HTTPException(
                status_code=404, 
                detail="No account found with this Google account. Please register first or use email/password login."
            )

        # User exists - generate token and return
        user_id = user["_id"]
        access_token = create_token({"sub": str(user_id)})

        return {
            "access_token": access_token,
            "email": google_user["email"],
            "name": google_user["name"],
            "message": "Login successful"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")


# Updated /google-auth endpoint for REGISTRATION page only
@router.post("/google-auth")
async def google_register_only(request: GoogleAuthRequest):
    """
    Google Sign-In for REGISTRATION page only - creates new users, rejects existing ones
    """
    try:
        google_user = await google_auth.verify_google_token(request.id_token)

        # Check if user already exists
        user = await db.users.find_one({"email": google_user["email"]})

        if user:
            # User already exists - return error for registration page
            raise HTTPException(
                status_code=409,  # Conflict status code
                detail="An account with this Google email already exists. Please use the login page instead."
            )

        # User doesn't exist - create new user for registration flow
        user_data = {
            "email": google_user["email"],
            "name": google_user["name"],
            "google_id": google_user["google_id"],
            "picture": google_user.get("picture", ""),
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.users.insert_one(user_data)
        user_id = result.inserted_id

        access_token = create_token({"sub": str(user_id)})

        return {
            "access_token": access_token,
            "email": google_user["email"],
            "name": google_user["name"],
            "message": "Registration successful"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google registration failed: {str(e)}")


# Rest of your existing routes remain the same...
@router.post("/register")
async def register(user: RegisterUser):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    token = str(uuid.uuid4())

    await db.users.insert_one({
        "name": user.name,
        "email": user.email,
        "hashed_password": hashed,
        "is_verified": False,
        "verification_token": token
    })

    await send_verification_email(user.email, token)
    return {"msg": "Verification email sent"}

# @router.get("/verify-email")
# async def verify_email(token: str):
#     user = await db.users.find_one({"verification_token": token})
#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid token")

#     await db.users.update_one(
#         {"_id": user["_id"]},
#         {"$set": {"is_verified": True}, "$unset": {"verification_token": ""}}
#     )
#     return {"msg": "Email verified successfully"}

@router.get("/verify-email")
async def verify_email(token: str):
    user = await db.users.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_verified": True}, "$unset": {"verification_token": ""}}
    )

    # ✅ Generate access token after verification              
    access_token = create_token({"sub": str(user["_id"])})

    return {
        "msg": "Email verified successfully",
        "access_token": access_token
        # "email": user["email"]  # optional: helpful for frontend
    }


@router.post("/login")
async def login(user: LoginUser):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not db_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Email not verified")

    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_token({"sub": str(db_user["_id"])})
    return {"access_token": token}

@router.post("/logout")
async def logout():
    return {"msg": "Logged out successfully"}

def generate_otp(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# @router.post("/forgot-password")
# async def forgot_password(email: str = Body(...), puzzle_answer: int = Body(...)):
#     # Step 1: Puzzle check (simple human check)
#     if puzzle_answer != 42:
#         raise HTTPException(status_code=400, detail="Puzzle failed. Are you human?")

#     user = await db.users.find_one({"email": email})
#     if not user:
#         raise HTTPException(status_code=404, detail="Email not found")

#     otp = generate_otp()
#     await db.users.update_one({"email": email}, {"$set": {"reset_otp": otp}})

#     # Reuse existing email sender
#     await send_verification_email(email, otp)
#     return {"msg": "OTP sent to your email"}


# @router.post("/forgot-password")
# async def forgot_password(
#     email: str = Body(...),
#     puzzle_a: int = Body(...),
#     puzzle_b: int = Body(...),
#     puzzle_answer: int = Body(...)
# ):
#     # Dynamically validate the answer
#     if puzzle_answer != puzzle_a * puzzle_b:
#         raise HTTPException(status_code=400, detail="Puzzle failed. Are you human?")

#     user = await db.users.find_one({"email": email})
#     if not user:
#         raise HTTPException(status_code=404, detail="Email not found")

#     otp = generate_otp()
#     await db.users.update_one({"email": email}, {"$set": {"reset_otp": otp}})

#     await send_reset_otp(email, otp)
#     return {"msg": "OTP sent to your registered email"}


# @router.post("/reset-password")
# async def reset_password(email: str = Body(...), otp: str = Body(...), new_password: str = Body(...)):
#     user = await db.users.find_one({"email": email, "reset_otp": otp})
#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid OTP or email")

#     hashed = hash_password(new_password)
#     await db.users.update_one(
#         {"email": email},
#         {"$set": {"hashed_password": hashed}, "$unset": {"reset_otp": ""}}
#     )
#     return {"msg": "Password updated successfully"}

class ResendEmailRequest(BaseModel):
    email: EmailStr
@router.post("/resend-verification")
async def resend_verification(request: ResendEmailRequest):
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Generate a new token and update it
    new_token = str(uuid.uuid4())
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"verification_token": new_token}}
    )

    await send_verification_email(request.email, new_token)
    return {"msg": "Verification email resent"}


from datetime import datetime

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(...),
    puzzle_a: int = Body(...),
    puzzle_b: int = Body(...),
    puzzle_answer: int = Body(...)
):
    if puzzle_answer != puzzle_a * puzzle_b:
        raise HTTPException(status_code=400, detail="Puzzle failed. Are you human?")

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = generate_otp()
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "reset_otp": otp,
                "reset_otp_created_at": datetime.utcnow()
            }
        }
    )

    await send_reset_otp(email, otp)
    return {"msg": "OTP sent to your registered email"}


@router.post("/resend-otp")
async def resend_otp(email: str = Body(...)):
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    if not user.get("reset_otp"):
        raise HTTPException(status_code=400, detail="No OTP request found. Please use forgot-password first.")

    otp = generate_otp()
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "reset_otp": otp,
                "reset_otp_created_at": datetime.utcnow()
            }
        }
    )
    await send_reset_otp(email, otp)
    return {"msg": "OTP resent to your registered email"}


from datetime import datetime, timedelta

@router.post("/reset-password")
async def reset_password(email: str = Body(...), otp: str = Body(...), new_password: str = Body(...)):
    user = await db.users.find_one({"email": email, "reset_otp": otp})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP or email")

    created_at = user.get("reset_otp_created_at")
    if not created_at:
        raise HTTPException(status_code=400, detail="OTP timestamp missing")

    if datetime.utcnow() > created_at + timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    hashed = hash_password(new_password)
    await db.users.update_one(
        {"email": email},
        {
            "$set": {"hashed_password": hashed},
            "$unset": {"reset_otp": "", "reset_otp_created_at": ""}
        }
    )
    return {"msg": "Password updated successfully"}

from pydantic import BaseModel, EmailStr
from fastapi import Request, HTTPException
from ..auth.utils import  get_user_id_from_token
from ..database import db

class DeepEncryptInput(BaseModel):
    email: EmailStr
    password: str


@router.post("/test-token")
async def test_token(request: Request):
    try:
        user_id = get_user_id_from_token(request)
        return {"msg": "Token is valid", "user_id": str(user_id)}
    except Exception as e:
        return {"error": str(e)}


from ..auth.utils import encrypt_value  # not multi_encrypt
@router.post("/store-encrypted-credentials")
async def store_encrypted_credentials(request: Request, data: DeepEncryptInput):
    try:
        user_id = get_user_id_from_token(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # encrypted_email = multi_encrypt(data.email, rounds=2)
    # encrypted_password = multi_encrypt(data.password, rounds=2)
    encrypted_email = encrypt_value(data.email)
    encrypted_password = encrypt_value(data.password)


    result = await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "encript_email": encrypted_email,
                "encript_password": encrypted_password
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no changes applied")

    return {"msg": "Encrypted credentials saved successfully"}

@router.get("/check-encrypted-credentials")
async def check_encrypted_credentials(request: Request):
    try:
        user_id = get_user_id_from_token(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"_id": user_id}, {"encript_email": 1, "encript_password": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    has_email = bool(user.get("encript_email"))
    has_password = bool(user.get("encript_password"))

    if has_email and has_password:
        return {"encrypted_credentials_present": True}
    else:
        return {"encrypted_credentials_present": False}


from ..auth.linkedin_connector import LinkedInConnector

# Define CampaignConfig if not already defined elsewhere
from pydantic import BaseModel

class CampaignConfig(BaseModel):
    keyword: str
    start_page: int
    end_page: int
    requests_per_page: int
    headless: bool = False



from ..auth.utils import decrypt_value
@router.post("/send-connection-requests")
async def send_connection_requests(request: Request, config: CampaignConfig):
    try:
        user_id = get_user_id_from_token(request)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"_id": user_id}, {"encript_email": 1, "encript_password": 1})
    if not user or not user.get("encript_email") or not user.get("encript_password"):
        raise HTTPException(status_code=404, detail="Encrypted credentials not found")

    # email = user["encript_email"]
    # password = user["encript_password"]
    email = decrypt_value(user["encript_email"])
    password = decrypt_value(user["encript_password"])

    # Blocking execution (or put into background thread if needed)
    total_sent = 0
    try:
        connector = LinkedInConnector(email, password, headless=config.headless)
        if connector.login():
            total_sent = connector.run_multi_page_campaign(
                keyword=config.keyword,
                start_page=config.start_page,
                end_page=config.end_page,
                requests_per_page=config.requests_per_page
            )
        connector.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LinkedIn campaign failed: {e}")

    return {
        "msg": "Connection request campaign completed",
        "total_sent": total_sent,
        "pages_processed": config.end_page - config.start_page + 1
    }




@app.get("/")
async def health_check():
    return {
        "status": "Backend API Server is running",
        "timestamp": datetime.utcnow().isoformat()
    }

