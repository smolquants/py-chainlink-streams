"""
Chainlink Data Streams API client authentication and connection management.

This module provides authentication functions (HMAC-SHA256 signature generation),
credential management, and WebSocket connection establishment for Chainlink Data Streams API.
"""

import asyncio
import hmac
import hashlib
import os
import time
from typing import Dict, List, Optional, Tuple
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.constants import (
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


def get_api_credentials() -> Tuple[str, str]:
    """
    Retrieve and validate API credentials from environment variables.
    
    Returns:
        Tuple of (api_key, api_secret)
        
    Raises:
        ValueError: If CHAINLINK_STREAMS_API_KEY or CHAINLINK_STREAMS_API_SECRET are not set
    """
    api_key = os.getenv("CHAINLINK_STREAMS_API_KEY")
    api_secret = os.getenv("CHAINLINK_STREAMS_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError(
            "API credentials not set. Please set CHAINLINK_STREAMS_API_KEY and "
            "CHAINLINK_STREAMS_API_SECRET environment variables"
        )
    
    return api_key, api_secret


def generate_hmac(
    method: str,
    path: str,
    body: bytes,
    api_key: str,
    api_secret: str
) -> Tuple[str, int]:
    """
    Generate HMAC-SHA256 signature for Chainlink Data Streams API authentication.
    
    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path with query parameters (e.g., "/api/v1/reports/latest?feedID=...")
        body: Request body as bytes (empty bytes for GET requests)
        api_key: API key from Chainlink
        api_secret: API secret from Chainlink
        
    Returns:
        Tuple of (signature_hex_string, timestamp_milliseconds)
    """
    # Generate timestamp (milliseconds since Unix epoch)
    timestamp = int(time.time() * 1000)
    
    # Generate body hash
    body_hash = hashlib.sha256(body).hexdigest()
    
    # Create string to sign
    string_to_sign = f"{method} {path} {body_hash} {api_key} {timestamp}"
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp


def generate_auth_headers(
    method: str,
    path_with_params: str,
    api_key: str,
    api_secret: str,
    body: bytes = b""
) -> Dict[str, str]:
    """
    Generate HTTP headers with Chainlink Data Streams authentication.
    
    Args:
        method: HTTP method (e.g., "GET", "POST")
        path_with_params: Request path with query parameters
        api_key: API key from Chainlink
        api_secret: API secret from Chainlink
        body: Request body as bytes (default: empty)
        
    Returns:
        Dictionary of HTTP headers for authentication
    """
    signature, timestamp = generate_hmac(method, path_with_params, body, api_key, api_secret)
    
    headers = {
        "Authorization": api_key,
        "X-Authorization-Timestamp": str(timestamp),
        "X-Authorization-Signature-SHA256": signature
    }
    
    return headers


async def connect_websocket(
    feed_ids: List[str],
    host: Optional[str] = None,
    ping_interval: int = DEFAULT_PING_INTERVAL,
    pong_timeout: int = DEFAULT_PONG_TIMEOUT
) -> WebSocketClientProtocol:
    """
    Establish an authenticated WebSocket connection to Chainlink Data Streams.
    
    Args:
        feed_ids: List of feed IDs to subscribe to
        host: WebSocket host (default: MAINNET_WS_HOST)
        ping_interval: Seconds between ping messages (default: 30)
        pong_timeout: Seconds to wait for pong before timeout (default: 60)
        
    Returns:
        WebSocket connection object
        
    Raises:
        ValueError: If API credentials are not set or feed_ids is empty
        websockets.exceptions.InvalidStatusCode: If WebSocket connection fails
    """
    # Get API credentials
    api_key, api_secret = get_api_credentials()
    
    # Validate feed IDs
    if not feed_ids:
        raise ValueError("No feed ID(s) provided")
    
    # Use mainnet host by default
    if host is None:
        host = MAINNET_WS_HOST
    
    # Build query string
    query_string = f"feedIDs={','.join(feed_ids)}"
    path = "/api/v1/ws"
    full_path = f"{path}?{query_string}"
    
    # Generate authentication signature and timestamp
    signature, timestamp = generate_hmac("GET", full_path, b"", api_key, api_secret)
    
    # Create HTTP headers for WebSocket connection
    headers = {
        "Authorization": api_key,
        "X-Authorization-Timestamp": str(timestamp),
        "X-Authorization-Signature-SHA256": signature
    }
    
    # Create WebSocket URL
    ws_url = f"wss://{host}{full_path}"
    
    # Connect to WebSocket server
    try:
        websocket = await websockets.connect(
            ws_url,
            additional_headers=headers,
            ping_interval=ping_interval,
            ping_timeout=pong_timeout
        )
        return websocket
    except websockets.exceptions.InvalidStatusCode as e:
        raise websockets.exceptions.InvalidStatusCode(
            e.status_code,
            e.headers,
            f"WebSocket connection error (HTTP {e.status_code}): {e}"
        )

