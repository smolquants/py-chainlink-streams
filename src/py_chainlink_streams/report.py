"""
Chainlink Data Streams report fetching and streaming functionality.

This module provides high-level functions for fetching and streaming reports
via both HTTP REST API and WebSocket connections.

Report functions accept a WebSocket connection (from client.connect_websocket)
or use client authentication functions for HTTP requests.
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
import requests
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.client import (
    get_api_credentials,
    generate_auth_headers,
    connect_websocket,
)
from py_chainlink_streams.constants import (
    MAINNET_API_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


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


async def stream_reports(
    websocket: WebSocketClientProtocol,
    callback: Callable[[Dict[str, Any]], None],
    stop_event: Optional[asyncio.Event] = None
) -> None:
    """
    Continuously read and process reports from a WebSocket connection.
    
    This function processes reports from an already-established WebSocket connection.
    Use client.connect_websocket() to create the connection first.
    
    Args:
        websocket: Active WebSocket connection (from client.connect_websocket)
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


async def _ping_loop(
    websocket: WebSocketClientProtocol,
    ping_interval: int,
    stop_event: asyncio.Event
) -> None:
    """
    Send periodic ping messages to keep WebSocket connection alive.
    
    Internal helper function for stream_reports_with_keepalive.
    
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
        ping_task = asyncio.create_task(_ping_loop(websocket, ping_interval, stop_event))
        
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

