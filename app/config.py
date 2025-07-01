# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     MONGO_URI: str
#     JWT_SECRET: str
#     JWT_ALGORITHM: str
#     EMAIL_USER: str
#     EMAIL_PASSWORD: str
#     FRONTEND_URL: str

#     class Config:
#         env_file = ".env"

# settings = Settings()
# 1. Update your config.py file to include Google settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    FRONTEND_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
print("✅ Loaded GOOGLE_CLIENT_ID:", settings.GOOGLE_CLIENT_ID)
