"""
ChainlinkClient class for object-oriented API access.

This module provides the ChainlinkClient class that implements a client interface
similar to the Go SDK's Client, with methods for all Chainlink Data Streams API operations.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlencode
import requests
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from py_chainlink_streams.config import ChainlinkConfig
from py_chainlink_streams.auth import generate_auth_headers, generate_hmac
from py_chainlink_streams.report import ReportResponse, ReportPage
from py_chainlink_streams.feed import Feed


class ChainlinkClient:
    """
    Client for Chainlink Data Streams API.
    
    Provides methods for all Chainlink Data Streams operations:
    - GetFeeds: List all available feeds
    - GetLatestReport: Fetch latest report for a feed
    - GetReport: Fetch a report for a feed at a specific timestamp
    - GetReportPage: Paginate through reports
    - Stream: Create real-time report stream
    - StreamWithStatusCallback: Stream with connection status callbacks
    
    Example:
        ```python
        import os
        from py_chainlink_streams import ChainlinkClient, ChainlinkConfig
        
        # Create config from environment variables
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        
        # Create client
        client = ChainlinkClient(config)
        
        # Get all feeds
        feeds = client.get_feeds()
        
        # Get latest report
        report = client.get_latest_report("0x0003...")
        ```
    """
    
    def __init__(self, config: ChainlinkConfig):
        """
        Initialize ChainlinkClient with configuration.
        
        Args:
            config: ChainlinkConfig instance with API credentials and settings
        """
        if not config.api_key or not config.api_secret:
            raise ValueError("api_key and api_secret are required")
        
        self.config = config
        
        # Create requests session with timeout
        self._session = requests.Session()
        self._session.timeout = config.timeout
    
    async def _connect_websocket(
        self,
        feed_ids: List[str],
        ping_interval: Optional[int] = None,
        pong_timeout: Optional[int] = None
    ) -> WebSocketClientProtocol:
        """
        Internal method to establish an authenticated WebSocket connection to Chainlink Data Streams.
        
        This is an internal method used by the client for streaming. For external use,
        use the stream() or stream_with_status_callback() methods.
        
        Args:
            feed_ids: List of feed IDs to subscribe to
            ping_interval: Seconds between ping messages (default: from config)
            pong_timeout: Seconds to wait for pong before timeout (default: from config)
            
        Returns:
            WebSocket connection object
            
        Raises:
            ValueError: If feed_ids is empty
            websockets.exceptions.InvalidStatusCode: If WebSocket connection fails
        """
        # Validate feed IDs
        if not feed_ids:
            raise ValueError("No feed ID(s) provided")
        
        # Use config defaults if not provided
        if ping_interval is None:
            ping_interval = self.config.ping_interval
        if pong_timeout is None:
            pong_timeout = self.config.pong_timeout
        
        # Build query string
        query_string = f"feedIDs={','.join(feed_ids)}"
        path = "/api/v1/ws"
        full_path = f"{path}?{query_string}"
        
        # Generate authentication signature and timestamp
        signature, timestamp = generate_hmac(
            "GET",
            full_path,
            b"",
            self.config.api_key,
            self.config.api_secret
        )
        
        # Create HTTP headers for WebSocket connection
        headers = {
            "Authorization": self.config.api_key,
            "X-Authorization-Timestamp": str(timestamp),
            "X-Authorization-Signature-SHA256": signature
        }
        
        # Create WebSocket URL
        ws_url = f"wss://{self.config.ws_host}{full_path}"
        
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
    
    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: bytes = b""
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Chainlink API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/api/v1/reports/latest")
            params: Query parameters
            body: Request body as bytes
            
        Returns:
            JSON response as dictionary
        """
        # Build URL
        url = f"https://{self.config.api_host}{path}"
        
        # Build query string for path (needed for signature)
        path_with_params = path
        if params:
            query_string = urlencode(params)
            path_with_params = f"{path}?{query_string}"
        
        # Generate authentication headers
        headers = generate_auth_headers(
            method,
            path_with_params,
            self.config.api_key,
            self.config.api_secret,
            body
        )
        
        # Make request with retry logic
        last_exception = None
        for attempt in range(self.config.http_max_retries + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    data=body,
                    verify=not self.config.insecure_skip_verify
                )
                
                # Provide better error messages with API response details
                if not response.ok:
                    # Don't retry on 4xx errors (client errors) - raise immediately
                    if 400 <= response.status_code < 500:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", error_data.get("message", response.text))
                        except:
                            error_msg = response.text
                        error = requests.HTTPError(
                            f"{response.status_code} {response.reason}: {error_msg}",
                            response=response
                        )
                        error.response_text = response.text
                        raise error
                    
                    # For 5xx errors, raise HTTPError to trigger retry logic
                    raise requests.HTTPError(
                        f"{response.status_code} {response.reason}",
                        response=response
                    )
                
                return response.json()
                
            except (requests.RequestException, requests.HTTPError) as e:
                last_exception = e
                
                # Don't retry on 4xx errors (client errors) - raise immediately
                if isinstance(e, requests.HTTPError) and hasattr(e, 'response') and e.response is not None:
                    if 400 <= e.response.status_code < 500:
                        # Already formatted in the if not response.ok block above
                        raise
                
                # Don't retry on last attempt
                if attempt >= self.config.http_max_retries:
                    # If it's an HTTPError with response, provide better error message
                    if isinstance(e, requests.HTTPError) and hasattr(e, 'response') and e.response is not None:
                        try:
                            error_data = e.response.json()
                            error_msg = error_data.get("error", error_data.get("message", e.response.text))
                        except:
                            error_msg = e.response.text
                        error = requests.HTTPError(
                            f"{e.response.status_code} {e.response.reason}: {error_msg}",
                            response=e.response
                        )
                        error.response_text = e.response.text
                        raise error
                    raise
                
                # Calculate exponential backoff delay
                delay = self.config.http_backoff_factor ** attempt
                self.config._log(
                    f"HTTP request failed (attempt {attempt + 1}/{self.config.http_max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise requests.RequestException("Request failed after retries")
    
    def get_feeds(self) -> List[Feed]:
        """
        List all feeds available to this client.
        
        Returns:
            List of Feed objects
            
        Raises:
            requests.RequestException: If HTTP request fails
        """
        response = self._make_request("GET", "/api/v1/feeds")
        
        # Handle nested structure
        if "feeds" in response:
            feeds_data = response["feeds"]
        else:
            feeds_data = response
        
        if not feeds_data:
            return []
        
        return [Feed(feed_data) for feed_data in feeds_data]
    
    def get_latest_report(self, feed_id: str) -> ReportResponse:
        """
        Fetch the latest report available for the given feedID.
        
        Args:
            feed_id: Chainlink feed ID (hex string)
            
        Returns:
            ReportResponse object
            
        Raises:
            requests.RequestException: If HTTP request fails
            ValueError: If response doesn't contain report data
        """
        params = {"feedID": feed_id}
        response = self._make_request("GET", "/api/v1/reports/latest", params=params)
        
        # Handle nested structure
        if "report" in response:
            report_data = response["report"]
        else:
            report_data = response
        
        if not report_data:
            raise ValueError("Response does not contain report data")
        
        return ReportResponse.from_dict(report_data)
    
    def get_report(
        self,
        feed_id: str,
        timestamp: int
    ) -> ReportResponse:
        """
        Fetch a report for the given feedID at the specified timestamp.
        
        Args:
            feed_id: Feed ID (hex string)
            timestamp: Unix timestamp (seconds)
            
        Returns:
            ReportResponse object
            
        Raises:
            requests.RequestException: If HTTP request fails
            ValueError: If response doesn't contain report data
        """
        # Use feedID (singular) parameter, matching get_latest_report pattern
        params = {
            "feedID": feed_id,
            "timestamp": str(timestamp)
        }
        response = self._make_request("GET", "/api/v1/reports", params=params)
        
        # Handle nested structure - API returns {"report": {...}} for single report
        if "report" in response:
            report_data = response["report"]
            if isinstance(report_data, dict):
                return ReportResponse.from_dict(report_data)
        elif isinstance(response, dict) and ("feedID" in response or "feedId" in response):
            # Direct report dict
            return ReportResponse.from_dict(response)
        
        raise ValueError("Response does not contain report data")
    
    def get_report_page(
        self,
        feed_id: str,
        start_timestamp: int
    ) -> ReportPage:
        """
        Paginate reports for the given feedID starting from the specified timestamp.
        
        Args:
            feed_id: Chainlink feed ID (hex string)
            start_timestamp: Unix timestamp (seconds) to start pagination from
            
        Returns:
            ReportPage object with reports and next_page_timestamp
            
        Raises:
            requests.RequestException: If HTTP request fails
        """
        params = {
            "feedID": feed_id,
            "startTimestamp": str(start_timestamp)
        }
        response = self._make_request("GET", "/api/v1/reports/page", params=params)
        
        # Handle nested structure
        if "reports" in response:
            reports_data = response["reports"]
        else:
            reports_data = response.get("reports", [])
        
        reports = []
        if reports_data:
            # Handle both flat and nested structures
            for r in reports_data:
                if isinstance(r, dict):
                    # If it already has feedID at top level, use as-is
                    if "feedID" in r:
                        reports.append(ReportResponse.from_dict(r))
                    # Otherwise wrap it
                    else:
                        reports.append(ReportResponse.from_dict({"report": r}))
                else:
                    # Shouldn't happen, but handle gracefully
                    continue
        
        # Get next page timestamp from API response if available, otherwise calculate from last report
        next_page_timestamp = 0
        if "nextPageTimestamp" in response:
            next_page_timestamp = response["nextPageTimestamp"]
        elif reports:
            # Fallback: calculate from last report's observations timestamp
            next_page_timestamp = reports[-1].observations_timestamp + 1
        
        return ReportPage(reports=reports, next_page_timestamp=next_page_timestamp)
    
    async def stream(
        self,
        feed_ids: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Create real-time report stream for the given feedIDs.
        
        This is a convenience method that calls stream_with_status_callback with no status callback.
        
        Args:
            feed_ids: List of feed IDs to subscribe to
            callback: Function to process each report (can be async or sync)
        """
        await self.stream_with_status_callback(feed_ids, callback, None)
    
    async def stream_with_status_callback(
        self,
        feed_ids: List[str],
        callback: Callable[[Dict[str, Any]], None],
        status_callback: Optional[Callable[[bool, str, str], None]] = None
    ) -> None:
        """
        Create real-time report stream with connection status callbacks and automatic reconnection.
        
        This method automatically retries WebSocket connections with exponential backoff when
        the connection is lost. It will attempt to reconnect up to ws_max_reconnect times.
        
        Args:
            feed_ids: List of feed IDs to subscribe to
            callback: Function to process each report (can be async or sync)
            status_callback: Optional function called on connection status changes.
                           Can be sync or async. Signature: (is_connected: bool, host: str, origin: str) -> None
        """
        stop_event = asyncio.Event()
        reconnect_count = 0
        
        def _call_status_callback(is_connected: bool, host: str, origin: str) -> None:
            """Helper to call status callback (sync or async)."""
            if status_callback:
                if asyncio.iscoroutinefunction(status_callback):
                    # Create a task for async callbacks
                    asyncio.create_task(status_callback(is_connected, host, origin))
                else:
                    status_callback(is_connected, host, origin)
        
        while not stop_event.is_set() and reconnect_count <= self.config.ws_max_reconnect:
            websocket = None
            ping_task = None
            
            try:
                # Connect to WebSocket
                websocket = await self._connect_websocket(feed_ids)
                
                # Reset reconnect count on successful connection
                if reconnect_count > 0:
                    self.config._log(f"WebSocket reconnected successfully (attempt {reconnect_count})")
                    reconnect_count = 0
                
                # Call status callback if provided
                _call_status_callback(True, self.config.ws_host, "")
                
                self.config._log(f"WebSocket connection established for feeds: {feed_ids}")
                
                # Start ping loop in background
                async def ping_loop():
                    """Send periodic ping messages to keep WebSocket connection alive."""
                    while not stop_event.is_set():
                        try:
                            await asyncio.sleep(self.config.ping_interval)
                            if not stop_event.is_set() and websocket:
                                await websocket.ping()
                        except Exception as e:
                            self.config._log(f"Error sending ping: {e}")
                            break
                
                ping_task = asyncio.create_task(ping_loop())
                
                # Stream reports
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
                            if stop_event.is_set():
                                break
                                
                        except json.JSONDecodeError as e:
                            self.config._log(f"Error parsing message: {e}")
                            continue
                        except Exception as e:
                            self.config._log(f"Error in callback: {e}")
                            continue
                            
                except ConnectionClosed as e:
                    self.config._log(f"WebSocket connection closed: {e}")
                    _call_status_callback(False, self.config.ws_host, "")
                    
                    # Check if we should retry
                    if reconnect_count >= self.config.ws_max_reconnect:
                        self.config._log(f"Maximum reconnection attempts ({self.config.ws_max_reconnect}) reached. Stopping.")
                        break
                    
                    # Calculate exponential backoff delay
                    delay = self.config.ws_reconnect_initial_delay * (self.config.ws_reconnect_backoff_factor ** reconnect_count)
                    reconnect_count += 1
                    self.config._log(
                        f"Attempting to reconnect (attempt {reconnect_count}/{self.config.ws_max_reconnect}) "
                        f"in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    continue  # Retry connection
                    
                except Exception as e:
                    self.config._log(f"WebSocket read error: {e}")
                    _call_status_callback(False, self.config.ws_host, "")
                    
                    # Check if we should retry
                    if reconnect_count >= self.config.ws_max_reconnect:
                        self.config._log(f"Maximum reconnection attempts ({self.config.ws_max_reconnect}) reached. Stopping.")
                        break
                    
                    # Calculate exponential backoff delay
                    delay = self.config.ws_reconnect_initial_delay * (self.config.ws_reconnect_backoff_factor ** reconnect_count)
                    reconnect_count += 1
                    self.config._log(
                        f"Attempting to reconnect (attempt {reconnect_count}/{self.config.ws_max_reconnect}) "
                        f"in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    continue  # Retry connection
                
                # If we exit the message loop normally (not due to error), break
                break
                
            except KeyboardInterrupt:
                self.config._log("\nInterrupt signal received, closing connection...")
                stop_event.set()
                break
            except Exception as e:
                self.config._log(f"Error in stream: {e}")
                _call_status_callback(False, self.config.ws_host, "")
                
                # Check if we should retry
                if reconnect_count >= self.config.ws_max_reconnect:
                    self.config._log(f"Maximum reconnection attempts ({self.config.ws_max_reconnect}) reached. Stopping.")
                    break
                
                # Calculate exponential backoff delay
                delay = self.config.ws_reconnect_initial_delay * (self.config.ws_reconnect_backoff_factor ** reconnect_count)
                reconnect_count += 1
                self.config._log(
                    f"Attempting to reconnect (attempt {reconnect_count}/{self.config.ws_max_reconnect}) "
                    f"in {delay:.2f} seconds..."
                )
                await asyncio.sleep(delay)
                continue  # Retry connection
            finally:
                # Clean up current connection
                if websocket:
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                if ping_task:
                    ping_task.cancel()
                    try:
                        await ping_task
                    except asyncio.CancelledError:
                        pass
        
        # Final status callback
        _call_status_callback(False, self.config.ws_host, "")

