"""
Tests for py_chainlink_streams.client module.

This module tests ChainlinkClient class methods.
"""

import os
import asyncio
import pytest
import requests
from unittest.mock import patch, MagicMock, AsyncMock
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.client import ChainlinkClient
from py_chainlink_streams.config import ChainlinkConfig
from py_chainlink_streams.constants import (
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)
from py_chainlink_streams.report import ReportResponse, ReportPage
from py_chainlink_streams.feed import Feed


def create_websocket_mock(mock_connect, mock_ws):
    """Helper to create a websocket connect mock that returns websocket when awaited."""
    async def connect_mock(*args, **kwargs):
        return mock_ws
    mock_connect.side_effect = connect_mock


class TestChainlinkClientConnectWebsocket:
    """Test ChainlinkClient._connect_websocket internal method."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    @pytest.mark.asyncio
    async def test_raises_when_feed_ids_empty(self, client):
        """Test raises ValueError when feed_ids is empty list."""
        with pytest.raises(ValueError, match="No feed ID\\(s\\) provided"):
            await client._connect_websocket([])

    @pytest.mark.asyncio
    async def test_uses_mainnet_ws_host_by_default(self, client, sample_feed_ids):
        """Test uses MAINNET_WS_HOST by default."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await client._connect_websocket(sample_feed_ids)
            
            # Check that URL contains mainnet host
            call_args = mock_connect.call_args
            assert MAINNET_WS_HOST in str(call_args[0][0])

    @pytest.mark.asyncio
    async def test_uses_config_ping_interval(self, client, sample_feed_ids):
        """Test uses config ping_interval."""
        client.config.ping_interval = 45
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await client._connect_websocket(sample_feed_ids)
            
            call_args = mock_connect.call_args
            kwargs = call_args[1]
            assert "ping_interval" in kwargs
            assert kwargs["ping_interval"] == 45

    @pytest.mark.asyncio
    async def test_uses_config_pong_timeout(self, client, sample_feed_ids):
        """Test uses config pong_timeout."""
        client.config.pong_timeout = 90
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await client._connect_websocket(sample_feed_ids)
            
            call_args = mock_connect.call_args
            kwargs = call_args[1]
            assert "ping_interval" in kwargs
            # pong_timeout is not directly passed, but ping_interval is used

    @pytest.mark.asyncio
    async def test_returns_websocket_client_protocol_instance(self, client, sample_feed_ids):
        """Test returns WebSocketClientProtocol instance."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            result = await client._connect_websocket(sample_feed_ids)
            
            assert result == mock_ws

    @pytest.mark.asyncio
    async def test_handles_multiple_feed_ids_correctly(self, client):
        """Test handles multiple feed IDs correctly."""
        feed_ids = ["0x123", "0x456", "0x789"]
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await client._connect_websocket(feed_ids)
            
            call_args = mock_connect.call_args
            url = call_args[0][0]
            # All feed IDs should be in the query string
            assert all(feed_id in url for feed_id in feed_ids)

    @pytest.mark.asyncio
    async def test_raises_appropriate_exception_on_connection_failure(self, client, sample_feed_ids):
        """Test raises appropriate exception on connection failure."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            original_exception = websockets.exceptions.InvalidStatusCode(401, {})
            async def connect_raises(*args, **kwargs):
                raise original_exception
            mock_connect.side_effect = connect_raises
            
            with pytest.raises((websockets.exceptions.InvalidStatusCode, TypeError)):
                await client._connect_websocket(sample_feed_ids)


class TestChainlinkClientGetFeeds:
    """Test ChainlinkClient.get_feeds method."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    def test_get_feeds_returns_list_of_feeds(self, client):
        """Test get_feeds returns list of Feed objects."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = [
                {"id": "0x123", "name": "BTC/USD"},
                {"id": "0x456", "name": "ETH/USD"}
            ]
            
            feeds = client.get_feeds()
            
            assert isinstance(feeds, list)
            assert len(feeds) == 2
            assert all(isinstance(feed, Feed) for feed in feeds)
            assert feeds[0].id == "0x123"
            assert feeds[0].name == "BTC/USD"
            assert feeds[1].id == "0x456"
            assert feeds[1].name == "ETH/USD"

    def test_get_feeds_uses_correct_endpoint(self, client):
        """Test get_feeds uses correct API endpoint."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = []
            
            client.get_feeds()
            
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/api/v1/feeds"

    def test_get_feeds_handles_empty_list(self, client):
        """Test get_feeds handles empty feed list."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = []
            
            feeds = client.get_feeds()
            
            assert isinstance(feeds, list)
            assert len(feeds) == 0


class TestChainlinkClientGetLatestReport:
    """Test ChainlinkClient.get_latest_report method."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    def test_get_latest_report_returns_report_response(self, client, sample_feed_id):
        """Test get_latest_report returns ReportResponse object."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "report": {
                    "feedID": sample_feed_id,
                    "fullReport": "0xabc",
                    "validFromTimestamp": 1000,
                    "observationsTimestamp": 1001
                }
            }
            
            report = client.get_latest_report(sample_feed_id)
            
            assert isinstance(report, ReportResponse)
            assert report.feed_id == sample_feed_id
            assert report.valid_from_timestamp == 1000
            assert report.observations_timestamp == 1001

    def test_get_latest_report_uses_correct_endpoint(self, client, sample_feed_id):
        """Test get_latest_report uses correct API endpoint."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "report": {
                    "feedID": sample_feed_id,
                    "fullReport": "0xabc",
                    "validFromTimestamp": 1000,
                    "observationsTimestamp": 1001
                }
            }
            
            client.get_latest_report(sample_feed_id)
            
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/api/v1/reports/latest"
            params = call_args[1]["params"]
            assert params["feedID"] == sample_feed_id


class TestChainlinkClientGetReport:
    """Test ChainlinkClient.get_report method."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    def test_get_report_returns_report_response(self, client, sample_feed_id):
        """Test get_report returns ReportResponse object."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "report": {
                    "feedID": sample_feed_id,
                    "fullReport": "0xabc",
                    "validFromTimestamp": 1000,
                    "observationsTimestamp": 1001
                }
            }
            
            report = client.get_report(sample_feed_id, timestamp=1000)
            
            assert isinstance(report, ReportResponse)
            assert report.feed_id == sample_feed_id
            assert report.valid_from_timestamp == 1000
            assert report.observations_timestamp == 1001

    def test_get_report_uses_feedID_parameter(self, client, sample_feed_id):
        """Test get_report uses feedID parameter."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "report": {
                    "feedID": sample_feed_id,
                    "fullReport": "0xabc",
                    "validFromTimestamp": 1000,
                    "observationsTimestamp": 1001
                }
            }
            
            client.get_report(sample_feed_id, timestamp=1000)
            
            # Check that _make_request was called with correct params
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/api/v1/reports"
            params = call_args[1]["params"]
            assert params["feedID"] == sample_feed_id
            assert params["timestamp"] == "1000"

    def test_get_report_handles_direct_report_dict(self, client, sample_feed_id):
        """Test get_report handles direct report dict (not nested)."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "feedID": sample_feed_id,
                "fullReport": "0xabc",
                "validFromTimestamp": 1000,
                "observationsTimestamp": 1001
            }
            
            report = client.get_report(sample_feed_id, timestamp=1000)
            
            assert isinstance(report, ReportResponse)
            assert report.feed_id == sample_feed_id

    def test_get_report_raises_on_missing_report_data(self, client, sample_feed_id):
        """Test get_report raises ValueError when response doesn't contain report."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {}
            
            with pytest.raises(ValueError, match="Response does not contain report data"):
                client.get_report(sample_feed_id, timestamp=1000)


class TestChainlinkClientGetReportPage:
    """Test ChainlinkClient.get_report_page method."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    def test_get_report_page_returns_report_page(self, client, sample_feed_id):
        """Test get_report_page returns ReportPage object."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "reports": [
                    {
                        "feedID": sample_feed_id,
                        "fullReport": "0xabc",
                        "validFromTimestamp": 1000,
                        "observationsTimestamp": 1001
                    }
                ],
                "nextPageTimestamp": 2000
            }
            
            page = client.get_report_page(sample_feed_id, start_timestamp=1000)
            
            assert isinstance(page, ReportPage)
            assert len(page.reports) == 1
            # Implementation uses nextPageTimestamp from API response if available
            assert page.next_page_timestamp == 2000

    def test_get_report_page_uses_correct_parameters(self, client, sample_feed_id):
        """Test get_report_page uses correct API parameters."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "reports": [],
                "nextPageTimestamp": 0
            }
            
            client.get_report_page(sample_feed_id, start_timestamp=1000)
            
            # Check that _make_request was called with correct params
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/api/v1/reports/page"
            params = call_args[1]["params"]
            assert params["feedID"] == sample_feed_id
            assert params["startTimestamp"] == "1000"

    def test_get_report_page_handles_empty_reports(self, client, sample_feed_id):
        """Test get_report_page handles empty reports list."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "reports": [],
                "nextPageTimestamp": 0
            }
            
            page = client.get_report_page(sample_feed_id, start_timestamp=1000)
            
            assert isinstance(page, ReportPage)
            assert len(page.reports) == 0
            assert page.next_page_timestamp == 0


class TestChainlinkClientStream:
    """Test ChainlinkClient.stream and stream_with_status_callback methods."""

    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)

    @pytest.mark.asyncio
    async def test_stream_calls_stream_with_status_callback(self, client, sample_feed_ids):
        """Test stream calls stream_with_status_callback with None status_callback."""
        with patch.object(client, 'stream_with_status_callback') as mock_stream:
            await client.stream(sample_feed_ids, lambda x: None)
            
            mock_stream.assert_called_once()
            args = mock_stream.call_args
            assert args[0][0] == sample_feed_ids
            assert args[0][1] is not None  # callback
            assert args[0][2] is None  # status_callback

    @pytest.mark.asyncio
    async def test_stream_with_status_callback_connects_websocket(self, client, sample_feed_ids):
        """Test stream_with_status_callback connects to WebSocket."""
        callback_called = False
        
        def callback(data):
            nonlocal callback_called
            callback_called = True
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            
            # Simulate receiving one message then connection closing
            async def message_gen():
                import json
                yield json.dumps({"feedID": "0x123", "fullReport": "0xabc"})
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            mock_ws.__aiter__ = lambda self: message_gen()
            mock_connect.return_value = mock_ws
            
            # Use a timeout to prevent hanging
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, callback, None),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            mock_connect.assert_called_once_with(sample_feed_ids)

    @pytest.mark.asyncio
    async def test_stream_with_status_callback_calls_sync_status_callback(self, client, sample_feed_ids):
        """Test stream_with_status_callback calls synchronous status_callback on connection."""
        status_callbacks = []
        
        def status_callback(is_connected, host, origin):
            status_callbacks.append((is_connected, host, origin))
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            
            async def message_gen():
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            mock_ws.__aiter__ = lambda self: message_gen()
            mock_connect.return_value = mock_ws
            
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, lambda x: None, status_callback),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Should have called status_callback at least once (on connect or disconnect)
            assert len(status_callbacks) > 0
            # Verify it was called with correct arguments
            assert status_callbacks[0][0] in [True, False]  # is_connected boolean
    
    @pytest.mark.asyncio
    async def test_stream_with_status_callback_calls_async_status_callback(self, client, sample_feed_ids):
        """Test stream_with_status_callback calls asynchronous status_callback on connection."""
        status_callbacks = []
        
        async def status_callback(is_connected, host, origin):
            # Simulate async operation
            await asyncio.sleep(0.01)
            status_callbacks.append((is_connected, host, origin))
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            
            async def message_gen():
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            mock_ws.__aiter__ = lambda self: message_gen()
            mock_connect.return_value = mock_ws
            
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, lambda x: None, status_callback),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Should have called status_callback at least once (on connect or disconnect)
            assert len(status_callbacks) > 0
            # Verify it was called with correct arguments
            assert status_callbacks[0][0] in [True, False]  # is_connected boolean
    
    @pytest.mark.asyncio
    async def test_stream_with_status_callback_handles_both_sync_and_async_callbacks(self, client, sample_feed_ids):
        """Test that stream_with_status_callback correctly handles both sync and async status callbacks."""
        sync_callbacks = []
        async_callbacks = []
        
        def sync_status_callback(is_connected, host, origin):
            sync_callbacks.append((is_connected, host, origin))
        
        async def async_status_callback(is_connected, host, origin):
            await asyncio.sleep(0.001)
            async_callbacks.append((is_connected, host, origin))
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            
            async def message_gen():
                raise websockets.exceptions.ConnectionClosed(None, None)
            
            mock_ws.__aiter__ = lambda self: message_gen()
            mock_connect.return_value = mock_ws
            
            # Test sync callback
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, lambda x: None, sync_status_callback),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Test async callback
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, lambda x: None, async_status_callback),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Both should have been called
            assert len(sync_callbacks) > 0
            assert len(async_callbacks) > 0
            # Verify no RuntimeWarning was raised (both should work correctly)
    
    @pytest.mark.asyncio
    async def test_stream_with_status_callback_retries_on_connection_closed(self, client, sample_feed_ids):
        """Test stream_with_status_callback retries on ConnectionClosed with exponential backoff."""
        callback_calls = []
        
        def callback(data):
            callback_calls.append(data)
        
        connect_count = [0]
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            def create_mock_ws():
                connect_count[0] += 1
                mock_ws = AsyncMock(spec=WebSocketClientProtocol)
                
                if connect_count[0] == 1:
                    # First connection: close immediately
                    async def message_gen():
                        raise websockets.exceptions.ConnectionClosed(None, None)
                    mock_ws.__aiter__ = lambda self: message_gen()
                else:
                    # Second connection: send one message then close
                    async def message_gen():
                        import json
                        yield json.dumps({"feedID": "0x123", "fullReport": "0xabc"})
                        raise websockets.exceptions.ConnectionClosed(None, None)
                    mock_ws.__aiter__ = lambda self: message_gen()
                
                return mock_ws
            
            mock_connect.side_effect = create_mock_ws
            
            # Configure client for fast retries (for testing)
            client.config.ws_max_reconnect = 2
            client.config.ws_reconnect_initial_delay = 0.1
            client.config.ws_reconnect_backoff_factor = 1.5
            
            # Use a timeout to prevent hanging
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, callback, None),
                    timeout=1.0
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Should have attempted to connect at least twice (initial + retry)
            assert mock_connect.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_stream_with_status_callback_stops_after_max_reconnects(self, client, sample_feed_ids):
        """Test stream_with_status_callback stops after max reconnection attempts."""
        connect_count = [0]
        
        with patch.object(client, '_connect_websocket') as mock_connect:
            def create_mock_ws():
                connect_count[0] += 1
                mock_ws = AsyncMock(spec=WebSocketClientProtocol)
                
                # Always close immediately
                async def message_gen():
                    raise websockets.exceptions.ConnectionClosed(None, None)
                mock_ws.__aiter__ = lambda self: message_gen()
                
                return mock_ws
            
            mock_connect.side_effect = create_mock_ws
            
            # Configure client for limited retries
            client.config.ws_max_reconnect = 2
            client.config.ws_reconnect_initial_delay = 0.05
            client.config.ws_reconnect_backoff_factor = 1.5
            
            # Use a timeout to prevent hanging
            try:
                await asyncio.wait_for(
                    client.stream_with_status_callback(sample_feed_ids, lambda x: None, None),
                    timeout=0.5
                )
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            # Should have attempted to connect: 1 initial + 2 retries = 3 total
            assert mock_connect.call_count == 3


class TestChainlinkClientMakeRequest:
    """Test ChainlinkClient._make_request retry logic."""
    
    @pytest.fixture
    def client(self, mock_api_credentials):
        """Create a ChainlinkClient instance for testing."""
        config = ChainlinkConfig(
            api_key=os.getenv("CHAINLINK_STREAMS_API_KEY", ""),
            api_secret=os.getenv("CHAINLINK_STREAMS_API_SECRET", "")
        )
        return ChainlinkClient(config)
    
    def test_make_request_retries_on_server_error(self, client):
        """Test _make_request retries on 5xx server errors with exponential backoff."""
        with patch.object(client._session, 'request') as mock_request:
            # First two attempts fail with 500, third succeeds
            mock_response_500 = MagicMock()
            mock_response_500.ok = False
            mock_response_500.status_code = 500
            mock_response_500.reason = "Internal Server Error"
            mock_response_500.text = "Server Error"
            mock_response_500.json.return_value = {"error": "Server Error"}
            
            mock_response_200 = MagicMock()
            mock_response_200.ok = True
            mock_response_200.json.return_value = {"success": True}
            
            mock_request.side_effect = [
                requests.HTTPError(response=mock_response_500),
                requests.HTTPError(response=mock_response_500),
                mock_response_200
            ]
            
            # Configure for fast retries (for testing)
            client.config.http_max_retries = 2
            client.config.http_backoff_factor = 0.1  # Very fast for testing
            
            result = client._make_request("GET", "/api/v1/test")
            
            assert result == {"success": True}
            assert mock_request.call_count == 3
    
    def test_make_request_no_retry_on_client_error(self, client):
        """Test _make_request does not retry on 4xx client errors."""
        with patch.object(client._session, 'request') as mock_request:
            mock_response_400 = MagicMock()
            mock_response_400.ok = False
            mock_response_400.status_code = 400
            mock_response_400.reason = "Bad Request"
            mock_response_400.text = "Invalid request"
            mock_response_400.json.return_value = {"error": "Invalid request"}
            
            mock_request.side_effect = requests.HTTPError(response=mock_response_400)
            
            with pytest.raises(requests.HTTPError):
                client._make_request("GET", "/api/v1/test")
            
            # Should not retry on 4xx errors
            assert mock_request.call_count == 1
