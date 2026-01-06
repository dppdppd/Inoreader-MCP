#!/usr/bin/env python3
"""
Non-interactive OAuth2 setup script for Inoreader MCP.

Usage:
    python3 setup_oauth_auto.py [redirect_url]

If redirect_url is not provided, only prints the authorization URL.
"""

import sys
import asyncio
import secrets
from pathlib import Path

# Add current directory to path to import local modules
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from oauth_client import OAuth2Handler
from inoreader_client import InoreaderClient


async def verify_tokens(oauth: OAuth2Handler) -> int:
    """
    Verify tokens work by making a test API call.

    Returns:
        Number of subscriptions found (for display purposes)

    Raises:
        Exception if verification fails
    """
    async with InoreaderClient() as client:
        subscriptions = await client.get_subscription_list()
        return len(subscriptions)


async def main():
    """Main setup flow"""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error:\n{e}\n", file=sys.stderr)
        print(
            "Please set the required environment variables in your .env file",
            file=sys.stderr,
        )
        print("See .env.example for reference", file=sys.stderr)
        sys.exit(1)

    # Initialize OAuth handler
    assert Config.INOREADER_APP_ID and Config.INOREADER_APP_KEY
    oauth = OAuth2Handler(Config.INOREADER_APP_ID, Config.INOREADER_APP_KEY)

    # Check command line args
    if len(sys.argv) < 2:
        # Just print auth URL
        state = secrets.token_urlsafe(32)
        auth_url = oauth.get_authorization_url(state)

        print("=" * 70)
        print("STEP 1: Open this URL in your browser:")
        print("=" * 70)
        print(auth_url)
        print("=" * 70)
        print()
        print("STEP 2: After authorizing, copy the redirect URL and run:")
        print(f"  python3 {sys.argv[0]} '<redirect_url>'")
        print()
        print("Example:")
        print(
            f"  python3 {sys.argv[0]} 'http://localhost:8080/callback?code=...&state=...'"
        )
        print("=" * 70)

        # Save state for verification
        state_file = Path.home() / ".config" / "inoreader-mcp" / "oauth_state.txt"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(state)
        state_file.chmod(0o600)

        sys.exit(0)

    redirect_url = sys.argv[1].strip()

    if not redirect_url:
        print("\n❌ Error: No URL provided", file=sys.stderr)
        sys.exit(1)

    # Load saved state
    state_file = Path.home() / ".config" / "inoreader-mcp" / "oauth_state.txt"
    if not state_file.exists():
        print("❌ Error: No state file found", file=sys.stderr)
        print(
            "Run without arguments first to get the authorization URL", file=sys.stderr
        )
        sys.exit(1)

    expected_state = state_file.read_text().strip()

    # Extract authorization code
    code = oauth.extract_code_from_url(redirect_url)
    if not code:
        print(
            "❌ Error: Could not extract authorization code from URL", file=sys.stderr
        )
        print(
            "\nMake sure you copied the complete URL from your browser's address bar.",
            file=sys.stderr,
        )
        print("It should look like:", file=sys.stderr)
        print("  http://localhost:8080/callback?code=...&state=...", file=sys.stderr)
        sys.exit(1)

    # Validate state parameter (CSRF protection)
    url_state = oauth.extract_state_from_url(redirect_url)
    if url_state != expected_state:
        print("❌ Error: State parameter mismatch", file=sys.stderr)
        print("\nThis could indicate a security issue (CSRF attack).", file=sys.stderr)
        print(
            "Please run the setup script again and use a fresh authorization URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Exchange code for tokens
    print("🔄 Exchanging authorization code for tokens...")
    try:
        tokens = await oauth.exchange_code_for_tokens(code)
    except Exception as e:
        print(f"\n❌ Error exchanging authorization code: {e}", file=sys.stderr)
        print("\nPossible causes:", file=sys.stderr)
        print(
            "  - Authorization code already used (codes are single-use)",
            file=sys.stderr,
        )
        print("  - Authorization code expired (they expire quickly)", file=sys.stderr)
        print("  - Network connectivity issue", file=sys.stderr)
        print("  - Invalid client credentials", file=sys.stderr)
        print(
            "\nPlease run the setup script again to get a fresh authorization code.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Save tokens
    print("💾 Saving tokens...")
    try:
        oauth.save_tokens(tokens)
        print(f"   ✓ Saved to: {oauth.token_file}")
    except Exception as e:
        print(f"\n❌ Error saving tokens: {e}", file=sys.stderr)
        print(
            f"\nPlease check that {oauth.token_file.parent} is writable.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify tokens work
    print("🔍 Verifying tokens...")
    try:
        feed_count = await verify_tokens(oauth)
        print(f"   ✓ Verified access to {feed_count} subscriptions")
    except Exception as e:
        print(f"\n⚠️  Warning: Token verification failed: {e}", file=sys.stderr)
        print("\nTokens were saved but could not be verified.", file=sys.stderr)
        print("You may need to run the setup again.", file=sys.stderr)
        sys.exit(1)

    # Clean up state file
    state_file.unlink()

    # Success!
    print()
    print("=" * 70)
    print("✓ Setup Complete!")
    print("=" * 70)
    print(f"Tokens saved to: {oauth.token_file}")
    print("The Inoreader MCP is now configured and ready to use.")
    print("Tokens will automatically refresh when needed.")
    print()
    print("⚠️  IMPORTANT: You must restart OpenCode for changes to take effect!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
