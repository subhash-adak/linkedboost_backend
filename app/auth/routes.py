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

router = APIRouter()

@router.get("/")
async def health_check():
    return JSONResponse(content={"status": "Backend API server is running"}, status_code=200)


@router.post("/register")
async def register(user: RegisterUser):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

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
    return {"msg": "Verification email sent to your registered mail"}

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
        raise HTTPException(status_code=403, detail="Email is not verified")

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
        raise HTTPException(status_code=404, detail="User not registered with this email")

    if user.get("is_verified"):
        raise HTTPException(status_code=400, detail="Email is already verified")

    # Generate a new token and update it
    new_token = str(uuid.uuid4())
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"verification_token": new_token}}
    )

    await send_verification_email(request.email, new_token)
    return {"msg": "Verification email resent sucessfully"}


from datetime import datetime

@router.post("/forgot-password")
async def forgot_password(
    email: str = Body(...),
    puzzle_a: int = Body(...),
    puzzle_b: int = Body(...),
    puzzle_answer: int = Body(...)
):
    if puzzle_answer != puzzle_a * puzzle_b:
        raise HTTPException(status_code=400, detail="Puzzle verification failed.")

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email is not found.")

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
        raise HTTPException(status_code=404, detail="Email is not found")

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
