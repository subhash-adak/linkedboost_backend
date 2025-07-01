import os
from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi import HTTPException
import httpx
from ..config import settings

class GoogleAuth:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        if not self.client_id:
            raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
    
    async def verify_google_token(self, token: str) -> dict:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            # Check if token is from Google
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid Google token: {str(e)}")
    
    async def get_google_user_info(self, access_token: str) -> dict:
        """Alternative method using Google's userinfo endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Invalid Google access token")
                
                user_info = response.json()
                return {
                    'google_id': user_info['id'],
                    'email': user_info['email'],
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture', ''),
                    'email_verified': user_info.get('verified_email', False)
                }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get Google user info: {str(e)}")
