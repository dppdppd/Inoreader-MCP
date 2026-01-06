import aiohttp
import asyncio
import base64
from typing import Dict, List, Optional, Any
from cachetools import TTLCache
from config import Config
from oauth_client import OAuth2Handler
import json


class InoreaderClient:
    def __init__(self):
        self.base_url = Config.INOREADER_BASE_URL
        # Type assertions: Config.validate() ensures these are set
        assert Config.INOREADER_APP_ID and Config.INOREADER_APP_KEY
        self.app_id = Config.INOREADER_APP_ID
        self.app_key = Config.INOREADER_APP_KEY
        self.oauth_handler = OAuth2Handler(
            Config.INOREADER_APP_ID, Config.INOREADER_APP_KEY
        )
        self.cache = TTLCache(maxsize=100, ttl=Config.CACHE_TTL)
        self.session = None
        self.access_token = None