"""
Chainlink Data Streams API client for HTTP REST and WebSocket connections.

This module provides authentication and client functionality for both HTTP REST API
and WebSocket connections to Chainlink Data Streams.
"""

import asyncio
import hmac
import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Callable, Tuple, Any
import requests
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.constants import (
    MAINNET_API_HOST,
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


def fetch_single_report(
    feed_id: str,
    host: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Fetch the latest report for a specific feed via HTTP REST API.
    
    Args:
        feed_id: Chainlink feed ID (hex string, e.g., "0x000359843a543ee2fe414dc14c7e7920ef10f4372990b79d6361cdc0dd1ba782")
        host: API host (default: MAINNET_API_HOST)
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        Dictionary containing the report data with keys:
        - feedID: Feed identifier
        - validFromTimestamp: Timestamp when report becomes valid
        - observationsTimestamp: Timestamp of observations
        - fullReport: Full report data (hex encoded)
        
    Raises:
        ValueError: If API credentials are not set
        requests.RequestException: If HTTP request fails
    """
    # Get API credentials
    api_key, api_secret = get_api_credentials()
    
    # Use mainnet host by default
    if host is None:
        host = MAINNET_API_HOST
    
    # Build URL
    path = "/api/v1/reports/latest"
    params = {"feedID": feed_id}
    url = f"https://{host}{path}"
    
    # Build query string for path (needed for signature)
    from urllib.parse import urlencode
    query_string = urlencode(params)
    path_with_params = f"{path}?{query_string}"
    
    # Generate authentication headers
    headers = generate_auth_headers("GET", path_with_params, api_key, api_secret)
    
    # Make request
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    return response.json()


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


async def stream_reports(
    websocket: WebSocketClientProtocol,
    callback: Callable[[Dict[str, Any]], None],
    stop_event: Optional[asyncio.Event] = None
) -> None:
    """
    Continuously read and process reports from WebSocket connection.
    
    Args:
        websocket: Active WebSocket connection
        callback: Async or sync function to process each report
                 Should accept a dict with report data
        stop_event: Optional asyncio.Event to signal when to stop streaming
                   If None, will run until connection closes
                   
    The callback will receive a dictionary with report data including:
    - feedID: Feed identifier
    - validFromTimestamp: Timestamp when report becomes valid
    - observationsTimestamp: Timestamp of observations
    - fullReport: Full report data (hex encoded)
    """
    try:
        async for message in websocket:
            try:
                # Parse JSON message
                report_data = json.loads(message)
                
                # Call callback with report data
                if asyncio.iscoroutinefunction(callback):
                    await callback(report_data)
                else:
                    callback(report_data)
                
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    break
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing message: {e}")
                print(f"Raw message: {message}")
                continue
            except Exception as e:
                print(f"Error in callback: {e}")
                continue
                
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")
    except Exception as e:
        print(f"WebSocket read error: {e}")


async def ping_loop(
    websocket: WebSocketClientProtocol,
    ping_interval: int,
    stop_event: asyncio.Event
) -> None:
    """
    Send periodic ping messages to keep WebSocket connection alive.
    
    Args:
        websocket: WebSocket connection
        ping_interval: Seconds between ping messages
        stop_event: Event to signal when to stop pinging
    """
    while not stop_event.is_set():
        try:
            await asyncio.sleep(ping_interval)
            if not stop_event.is_set():
                await websocket.ping()
        except Exception as e:
            print(f"Error sending ping: {e}")
            break


async def stream_reports_with_keepalive(
    feed_ids: List[str],
    callback: Callable[[Dict[str, Any]], None],
    host: Optional[str] = None,
    ping_interval: int = DEFAULT_PING_INTERVAL,
    pong_timeout: int = DEFAULT_PONG_TIMEOUT
) -> None:
    """
    High-level function to stream reports with automatic keepalive and reconnection.
    
    This function handles:
    - WebSocket connection establishment
    - Automatic ping/pong keepalive
    - Message streaming
    - Graceful shutdown on interrupt
    
    Args:
        feed_ids: List of feed IDs to subscribe to
        callback: Function to process each report (can be async or sync)
        host: WebSocket host (default: MAINNET_WS_HOST)
        ping_interval: Seconds between ping messages (default: 30)
        pong_timeout: Seconds to wait for pong before timeout (default: 60)
    """
    stop_event = asyncio.Event()
    
    try:
        # Connect to WebSocket
        websocket = await connect_websocket(feed_ids, host, ping_interval, pong_timeout)
        print(f"WebSocket connection established for feeds: {feed_ids}")
        
        # Start ping loop in background
        ping_task = asyncio.create_task(ping_loop(websocket, ping_interval, stop_event))
        
        # Stream reports
        await stream_reports(websocket, callback, stop_event)
        
    except KeyboardInterrupt:
        print("\nInterrupt signal received, closing connection...")
        stop_event.set()
    except Exception as e:
        print(f"Error in stream_reports_with_keepalive: {e}")
        stop_event.set()
    finally:
        if 'websocket' in locals():
            await websocket.close()
        if 'ping_task' in locals():
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

