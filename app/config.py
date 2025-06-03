from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    FRONTEND_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
