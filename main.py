#!/usr/bin/env python3
"""
Minimal MCP server for Inoreader - Based on working examples
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any
from config import Config
from tools import (
    list_feeds_tool,
    list_articles_tool,
    search_articles_tool,
    get_content_tool,
    mark_as_read_tool,
    summarize_article_tool,
    analyze_articles_tool,
    get_stats_tool,
    add_feed_tool,
    edit_feed_tool,
    unsubscribe_feed_tool,
    list_tags_tool,
    rename_tag_tool,
    delete_tag_tool,
    mark_all_as_read_tool,
    star_article_tool,
    unstar_article_tool,
    broadcast_article_tool,
    like_article_tool,
    tag_article_tool,
    untag_article_tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


class MinimalMCPServer:
    def __init__(self):
        pass

    async def send_response(self, response: Dict[str, Any]):
        """Send JSON response to stdout"""
        json_str = json.dumps(response)
        print(json_str, flush=True)

    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message"""
        method = message.get("method", "")
        params = message.get("params", {})
        msg_id = message.get("id", 0)

        logger.info(f"Received method: {method}")

        try:
            if method == "initialize":
                await self.handle_initialize(msg_id, params)
            elif method == "tools/list":
                await self.handle_list_tools(msg_id)
            elif method == "tools/call":
                await self.handle_call_tool(msg_id, params)
            else:
                await self.send_error(msg_id, -32601, f"Unknown method: {method}")

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            await self.send_error(msg_id, -32603, str(e))

    async def handle_initialize(self, msg_id: Any, params: Dict):
        """Handle initialize"""
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "inoreader-mcp", "version": "1.0.0"},
            },
        }
        await self.send_response(response)

    async def handle_list_tools(self, msg_id: Any):
        """List available tools"""
        tools = [
            {
                "name": "inoreader_list_feeds",
                "description": "List all subscribed feeds in Inoreader",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "inoreader_list_articles",
                "description": "List recent articles with optional filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of articles to return (default: 20)",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Articles from last N days (default: 7)",
                        },
                        "feed_id": {
                            "type": "string",
                            "description": "Optional feed ID to filter articles",
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "Only show unread articles (default: true)",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "inoreader_search",
                "description": "Search for articles by keyword",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "days": {
                            "type": "integer",
                            "description": "Search within the last N days (default: 7)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of articles to return (default: 50)",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "inoreader_get_content",
                "description": "Get full content of a specific article",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_id": {
                            "type": "string",
                            "description": "Article ID to get content for",
                        }
                    },
                    "required": ["article_id"],
                },
            },
            {
                "name": "inoreader_mark_as_read",
                "description": "Mark articles as read",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to mark as read",
                        }
                    },
                    "required": ["article_ids"],
                },
            },
            {
                "name": "inoreader_stats",
                "description": "Get statistics about unread articles",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "inoreader_add_feed",
                "description": "Subscribe to new feed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "feed_url": {
                            "type": "string",
                            "description": "URL of the feed to subscribe to",
                        }
                    },
                    "required": ["feed_url"],
                },
            },
            {
                "name": "inoreader_edit_feed",
                "description": "Edit feed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stream_id": {
                            "type": "string",
                            "description": "Stream ID of the feed to edit",
                        },
                        "new_title": {
                            "type": "string",
                            "description": "New title for the feed",
                        },
                        "add_to_folder": {
                            "type": "string",
                            "description": "Folder to add feed to",
                        },
                        "remove_from_folder": {
                            "type": "string",
                            "description": "Folder to remove feed from",
                        },
                    },
                    "required": ["stream_id"],
                },
            },
            {
                "name": "inoreader_unsubscribe_feed",
                "description": "Unsubscribe from feed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stream_id": {
                            "type": "string",
                            "description": "Stream ID of the feed to unsubscribe from",
                        }
                    },
                    "required": ["stream_id"],
                },
            },
            {
                "name": "inoreader_list_tags",
                "description": "List all folders/tags",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "inoreader_rename_tag",
                "description": "Rename a tag/folder",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Current tag name",
                        },
                        "destination": {
                            "type": "string",
                            "description": "New tag name",
                        },
                    },
                    "required": ["source", "destination"],
                },
            },
            {
                "name": "inoreader_delete_tag",
                "description": "Delete a tag/folder",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tag_name": {
                            "type": "string",
                            "description": "Name of the tag to delete",
                        }
                    },
                    "required": ["tag_name"],
                },
            },
            {
                "name": "inoreader_mark_all_as_read",
                "description": "Mark all articles in a stream/folder as read",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stream_id": {
                            "type": "string",
                            "description": "Stream ID to mark all as read",
                        },
                        "timestamp": {
                            "type": "integer",
                            "description": "Optional Unix timestamp - mark as read up to this time",
                        },
                    },
                    "required": ["stream_id"],
                },
            },
            {
                "name": "inoreader_star_article",
                "description": "Star articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to star",
                        }
                    },
                    "required": ["article_ids"],
                },
            },
            {
                "name": "inoreader_unstar_article",
                "description": "Unstar articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to unstar",
                        }
                    },
                    "required": ["article_ids"],
                },
            },
            {
                "name": "inoreader_broadcast_article",
                "description": "Broadcast articles (share publicly)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to broadcast",
                        }
                    },
                    "required": ["article_ids"],
                },
            },
            {
                "name": "inoreader_like_article",
                "description": "Like articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to like",
                        }
                    },
                    "required": ["article_ids"],
                },
            },
            {
                "name": "inoreader_tag_article",
                "description": "Add custom tag to articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to tag",
                        },
                        "tag_name": {
                            "type": "string",
                            "description": "Tag name to add",
                        },
                    },
                    "required": ["article_ids", "tag_name"],
                },
            },
            {
                "name": "inoreader_untag_article",
                "description": "Remove custom tag from articles",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "article_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of article IDs to untag",
                        },
                        "tag_name": {
                            "type": "string",
                            "description": "Tag name to remove",
                        },
                    },
                    "required": ["article_ids", "tag_name"],
                },
            },
        ]

        response = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
        await self.send_response(response)

    async def handle_call_tool(self, msg_id: Any, params: Dict):
        """Handle tool call"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        logger.info(f"Calling tool: {tool_name}")

        try:
            if tool_name == "inoreader_list_feeds":
                result = await list_feeds_tool()
            elif tool_name == "inoreader_list_articles":
                limit = arguments.get("limit", 20)
                days = arguments.get("days", 7)
                feed_id = arguments.get("feed_id")
                unread_only = arguments.get("unread_only", True)
                result = await list_articles_tool(
                    feed_id=feed_id, limit=limit, unread_only=unread_only, days=days
                )
            elif tool_name == "inoreader_search":
                query = arguments.get("query", "")
                days = arguments.get("days", 7)
                limit = arguments.get("limit", 50)
                result = await search_articles_tool(query=query, limit=limit, days=days)
            elif tool_name == "inoreader_get_content":
                article_id = arguments.get("article_id", "")
                result = await get_content_tool(article_id)
            elif tool_name == "inoreader_mark_as_read":
                article_ids = arguments.get("article_ids", [])
                result = await mark_as_read_tool(article_ids)
            elif tool_name == "inoreader_summarize":
                article_id = arguments.get("article_id", "")
                result = await summarize_article_tool(article_id)
            elif tool_name == "inoreader_analyze":
                article_ids = arguments.get("article_ids", [])
                analysis_type = arguments.get("analysis_type", "summary")
                result = await analyze_articles_tool(article_ids, analysis_type)
            elif tool_name == "inoreader_stats":
                result = await get_stats_tool()
            elif tool_name == "inoreader_add_feed":
                feed_url = arguments.get("feed_url", "")
                result = await add_feed_tool(feed_url)
            elif tool_name == "inoreader_edit_feed":
                stream_id = arguments.get("stream_id", "")
                new_title = arguments.get("new_title")
                add_to_folder = arguments.get("add_to_folder")
                remove_from_folder = arguments.get("remove_from_folder")
                result = await edit_feed_tool(
                    stream_id=stream_id,
                    new_title=new_title,
                    add_to_folder=add_to_folder,
                    remove_from_folder=remove_from_folder,
                )
            elif tool_name == "inoreader_unsubscribe_feed":
                stream_id = arguments.get("stream_id", "")
                result = await unsubscribe_feed_tool(stream_id)
            elif tool_name == "inoreader_list_tags":
                result = await list_tags_tool()
            elif tool_name == "inoreader_rename_tag":
                source = arguments.get("source", "")
                destination = arguments.get("destination", "")
                result = await rename_tag_tool(source, destination)
            elif tool_name == "inoreader_delete_tag":
                tag_name = arguments.get("tag_name", "")
                result = await delete_tag_tool(tag_name)
            elif tool_name == "inoreader_mark_all_as_read":
                stream_id = arguments.get("stream_id", "")
                timestamp = arguments.get("timestamp")
                result = await mark_all_as_read_tool(stream_id, timestamp)
            elif tool_name == "inoreader_star_article":
                article_ids = arguments.get("article_ids", [])
                result = await star_article_tool(article_ids)
            elif tool_name == "inoreader_unstar_article":
                article_ids = arguments.get("article_ids", [])
                result = await unstar_article_tool(article_ids)
            elif tool_name == "inoreader_broadcast_article":
                article_ids = arguments.get("article_ids", [])
                result = await broadcast_article_tool(article_ids)
            elif tool_name == "inoreader_like_article":
                article_ids = arguments.get("article_ids", [])
                result = await like_article_tool(article_ids)
            elif tool_name == "inoreader_tag_article":
                article_ids = arguments.get("article_ids", [])
                tag_name = arguments.get("tag_name", "")
                result = await tag_article_tool(article_ids, tag_name)
            elif tool_name == "inoreader_untag_article":
                article_ids = arguments.get("article_ids", [])
                tag_name = arguments.get("tag_name", "")
                result = await untag_article_tool(article_ids, tag_name)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": result}]},
            }

        except Exception as e:
            logger.error(f"Tool error: {e}")
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True,
                },
            }

        await self.send_response(response)

    async def send_error(self, msg_id: Any, code: int, message: str):
        """Send error response"""
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
        await self.send_response(response)

    async def run(self):
        """Main server loop"""
        logger.info("Starting minimal MCP server...")

        # Read from stdin
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)

        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                if not line_str:
                    continue

                try:
                    message = json.loads(line_str)
                    await self.handle_message(message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line_str}")

            except Exception as e:
                logger.error(f"Server loop error: {e}")


async def main():
    server = MinimalMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
