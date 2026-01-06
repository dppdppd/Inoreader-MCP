import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    INOREADER_APP_ID = os.getenv("INOREADER_APP_ID")
    INOREADER_APP_KEY = os.getenv("INOREADER_APP_KEY")

    # API Base URLs
    INOREADER_BASE_URL = "https://www.inoreader.com/reader/api/0"
    OAUTH_TOKEN_URL = "https://www.inoreader.com/oauth2/token"
    OAUTH_AUTH_URL = "https://www.inoreader.com/oauth2/auth"

    # Cache settings
    CACHE_TTL = 300  # 5 minutes

    # Request settings
    REQUEST_TIMEOUT = 10
    MAX_ARTICLES_PER_REQUEST = 50

    @classmethod
    def validate(cls):
        required = ["INOREADER_APP_ID", "INOREADER_APP_KEY"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please set these in your .env file or environment.\n"
                f"See .env.example for reference."
            )

        # Check for old credentials (migration helper)
        if os.getenv("INOREADER_USERNAME") or os.getenv("INOREADER_PASSWORD"):
            import sys

            print(
                """
⚠️  AUTHENTICATION METHOD CHANGED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This version uses OAuth2 instead of username/password.

ACTION REQUIRED:
  1. Run: python3 /opt/mcp-servers/inoreader-mcp/setup_oauth.py
  2. Remove INOREADER_USERNAME and INOREADER_PASSWORD from .env
  3. Restart OpenCode

Your old credentials are no longer used.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
                file=sys.stderr,
            )
            sys.exit(1)

        return True
