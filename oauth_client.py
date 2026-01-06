"""
OAuth2 client for Inoreader API authentication.

Handles OAuth2 authorization flow, token management, and automatic token refresh.
"""

import json
import time
import secrets
import aiohttp
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode, urlparse, parse_qs


class OAuth2Handler:
    """Handles OAuth2 authentication flow and token management for Inoreader."""

    def __init__(self, app_id: str, app_key: str):
        """
        Initialize OAuth2 handler.

        Args:
            app_id: Inoreader APP_ID from app registration
            app_key: Inoreader APP_KEY from app registration
        """
        self.app_id = app_id
        self.app_key = app_key
        self.token_file = Path.home() / ".config" / "inoreader-mcp" / "tokens.json"
        self.auth_url = "https://www.inoreader.com/oauth2/auth"
        self.token_url = "https://www.inoreader.com/oauth2/token"

    def get_authorization_url(
        self, state: str, redirect_uri: str = "http://localhost:8080/callback"
    ) -> str:
        """
        Generate OAuth2 authorization URL for user to visit.

        Args:
            state: Random state parameter for CSRF protection
            redirect_uri: OAuth redirect URI (must match app registration)

        Returns:
            Full authorization URL for user to visit in browser
        """
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "read write",
            "state": state,
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self, code: str, redirect_uri: str = "http://localhost:8080/callback"
    ) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth redirect URI (must match authorization request)

        Returns:
            Dict containing access_token, refresh_token, expires_at, scope

        Raises:
            Exception: If token exchange fails
        """
        data = {
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.app_id,
            "client_secret": self.app_key,
            "grant_type": "authorization_code",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Token exchange failed: {resp.status} - {text}")

                result = await resp.json()

                # Calculate absolute expiration timestamp
                expires_at = int(time.time()) + result.get("expires_in", 3600)

                return {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "expires_at": expires_at,
                    "scope": result.get("scope", "read write"),
                }

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh an expired access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict containing new access_token, refresh_token, expires_at, scope

        Raises:
            Exception: If token refresh fails
        """
        data = {
            "client_id": self.app_id,
            "client_secret": self.app_key,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Token refresh failed: {resp.status} - {text}")

                result = await resp.json()

                # Calculate absolute expiration timestamp
                expires_at = int(time.time()) + result.get("expires_in", 3600)

                return {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "expires_at": expires_at,
                    "scope": result.get("scope", "read write"),
                }

    def load_tokens(self) -> Optional[Dict]:
        """
        Load OAuth tokens from disk.

        Returns:
            Dict containing tokens, or None if file doesn't exist
        """
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Failed to load tokens from {self.token_file}: {e}")

    def save_tokens(self, tokens: Dict):
        """
        Save OAuth tokens to disk with secure permissions.

        Args:
            tokens: Dict containing access_token, refresh_token, expires_at, scope
        """
        # Create parent directory if it doesn't exist
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

        # Write tokens to file
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)

        # Set secure permissions (owner read/write only)
        self.token_file.chmod(0o600)

    def is_token_expired(self, tokens: Dict, buffer_seconds: int = 300) -> bool:
        """
        Check if access token is expired or will expire soon.

        Args:
            tokens: Dict containing expires_at timestamp
            buffer_seconds: Consider token expired if within this many seconds of expiration

        Returns:
            True if token is expired or will expire within buffer period
        """
        expires_at = tokens.get("expires_at", 0)
        current_time = int(time.time())
        return current_time >= (expires_at - buffer_seconds)

    def extract_code_from_url(self, url: str) -> Optional[str]:
        """
        Extract authorization code from OAuth redirect URL.

        Args:
            url: Full redirect URL pasted by user

        Returns:
            Authorization code, or None if not found
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            codes = query_params.get("code", [])
            return codes[0] if codes else None
        except Exception:
            return None

    def extract_state_from_url(self, url: str) -> Optional[str]:
        """
        Extract state parameter from OAuth redirect URL.

        Args:
            url: Full redirect URL pasted by user

        Returns:
            State parameter, or None if not found
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            states = query_params.get("state", [])
            return states[0] if states else None
        except Exception:
            return None
