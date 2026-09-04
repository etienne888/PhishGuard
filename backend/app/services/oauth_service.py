import os
from urllib.parse import urlencode

import requests


class OAuthService:
    """Provider integrations for OAuth-based authentication."""

    def get_google_auth_url(self) -> str:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        if not client_id or not redirect_uri:
            raise RuntimeError('Google OAuth is not configured')

        query = urlencode({
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
        })
        return f'https://accounts.google.com/o/oauth2/v2/auth?{query}'

    def exchange_google_code(self, code: str) -> dict | None:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        if not client_id or not client_secret or not redirect_uri:
            raise RuntimeError('Google OAuth is not configured')

        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')
        if not access_token:
            return None

        user_response = requests.get(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        return {'email': user_info.get('email')}

    def get_whatsapp_auth_url(self, phone: str) -> str:
        raise RuntimeError('WhatsApp login requires a configured provider')

    def exchange_whatsapp_code(self, code: str, phone: str) -> dict | None:
        raise RuntimeError('WhatsApp login requires a configured provider')
