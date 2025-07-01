# from pydantic import BaseModel, EmailStr

# class RegisterUser(BaseModel):
#     name: str
#     email: EmailStr
#     password: str

# class LoginUser(BaseModel):
#     email: EmailStr
#     password: str



# from pydantic import BaseModel, EmailStr

# class GoogleAuthRequest(BaseModel):
#     id_token: str  # For ID token verification
    
# class GoogleAccessTokenRequest(BaseModel):
#     access_token: str  # For access token verification

# class GoogleUserResponse(BaseModel):
#     google_id: str
#     email: EmailStr
#     name: str
#     picture: str
#     email_verified: bool



# 2. Add these schemas to your schemas.py file
from pydantic import BaseModel, EmailStr
from typing import Optional

# Existing schemas (RegisterUser, LoginUser, etc.)
class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str

# Google OAuth schemas
class GoogleAuthRequest(BaseModel):
    id_token: str

class GoogleAccessTokenRequest(BaseModel):
    access_token: str

class GoogleUserResponse(BaseModel):
    google_id: str
    email: EmailStr
    name: str
    picture: str
    email_verified: bool

# Your existing schemas
class ResendEmailRequest(BaseModel):
    email: EmailStr

class DeepEncryptInput(BaseModel):
    email: EmailStr
    password: str

class CampaignConfig(BaseModel):
    keyword: str
    start_page: int
    end_page: int
    requests_per_page: int
    headless: bool = False


from pydantic import BaseModel

class GoogleAuthRequest(BaseModel):
    id_token: str
