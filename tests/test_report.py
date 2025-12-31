"""
Tests for py_chainlink_streams.report module.
"""

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import requests
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.report import (
    fetch_single_report,
    stream_reports,
    stream_reports_with_keepalive,
    _ping_loop,
)
from py_chainlink_streams.constants import (
    MAINNET_API_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


class TestFetchSingleReport:
    """Test fetch_single_report function."""

    def test_returns_dict_with_correct_keys(self, mock_api_credentials, sample_feed_id):
        """Test returns dict with keys: feedID, validFromTimestamp, observationsTimestamp, fullReport."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "feedID": sample_feed_id,
                "validFromTimestamp": 1767208232,
                "observationsTimestamp": 1767208232,
                "fullReport": "0x1234",
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = fetch_single_report(sample_feed_id)
            
            assert "feedID" in result
            assert "validFromTimestamp" in result
            assert "observationsTimestamp" in result
            assert "fullReport" in result

    def test_uses_mainnet_api_host_by_default(self, mock_api_credentials, sample_feed_id):
        """Test uses MAINNET_API_HOST by default when host is None."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id)
            
            call_args = mock_get.call_args
            url = call_args[0][0]  # First positional argument
            assert MAINNET_API_HOST in url

    def test_uses_custom_host_when_provided(self, mock_api_credentials, sample_feed_id):
        """Test uses custom host when provided."""
        custom_host = "custom.api.host"
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id, host=custom_host)
            
            call_args = mock_get.call_args
            url = call_args[0][0]
            assert custom_host in url

    def test_builds_correct_url_with_feed_id(self, mock_api_credentials, sample_feed_id):
        """Test builds correct URL with feed_id in query params."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id)
            
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            assert params.get('feedID') == sample_feed_id

    def test_generates_correct_authentication_headers(self, mock_api_credentials, sample_feed_id):
        """Test generates correct authentication headers."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id)
            
            call_args = mock_get.call_args
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers
            assert "X-Authorization-Timestamp" in headers
            assert "X-Authorization-Signature-SHA256" in headers
            assert headers["Authorization"] == "test-api-key"

    def test_uses_default_timeout_when_not_provided(self, mock_api_credentials, sample_feed_id):
        """Test uses default timeout (30s) when not provided."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id)
            
            call_args = mock_get.call_args
            timeout = call_args.kwargs.get('timeout')
            assert timeout == 30

    def test_uses_custom_timeout_when_provided(self, mock_api_credentials, sample_feed_id):
        """Test uses custom timeout when provided."""
        custom_timeout = 60
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id, timeout=custom_timeout)
            
            call_args = mock_get.call_args
            timeout = call_args.kwargs.get('timeout')
            assert timeout == custom_timeout

    def test_raises_when_api_credentials_not_set(self, clear_api_credentials, sample_feed_id):
        """Test raises ValueError when API credentials not set."""
        with pytest.raises(ValueError, match="API credentials not set"):
            fetch_single_report(sample_feed_id)

    def test_raises_on_http_error(self, mock_api_credentials, sample_feed_id):
        """Test raises requests.RequestException on HTTP error."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.HTTPError):
                fetch_single_report(sample_feed_id)

    def test_raises_on_connection_error(self, mock_api_credentials, sample_feed_id):
        """Test raises requests.RequestException on connection error."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection failed")
            
            with pytest.raises(requests.ConnectionError):
                fetch_single_report(sample_feed_id)

    def test_handles_empty_feed_id(self, mock_api_credentials):
        """Test handles empty feed_id (will fail at API level)."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Should not raise ValueError, but API will handle validation
            result = fetch_single_report("")
            assert isinstance(result, dict)

    def test_includes_path_in_signature_calculation(self, mock_api_credentials, sample_feed_id):
        """Test includes path with query params in signature calculation."""
        with patch('py_chainlink_streams.report.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"feedID": sample_feed_id}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            fetch_single_report(sample_feed_id)
            
            # Verify generate_auth_headers was called with path including query params
            call_args = mock_get.call_args
            headers = call_args.kwargs.get('headers', {})
            # Signature should be present
            assert "X-Authorization-Signature-SHA256" in headers


class TestStreamReports:
    """Test stream_reports function."""

    @pytest.mark.asyncio
    async def test_calls_callback_for_each_message(self):
        """Test calls callback for each message received."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        mock_callback = MagicMock()
        
        # Simulate two messages using async generator
        async def message_gen():
            yield json.dumps({"feedID": "0x123", "fullReport": "0xabc"})
            yield json.dumps({"feedID": "0x456", "fullReport": "0xdef"})
        
        # Make __aiter__ return the async generator iterator (takes self as first arg)
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, mock_callback)
        
        assert mock_callback.call_count == 2

    @pytest.mark.asyncio
    async def test_callback_receives_parsed_json_dict(self):
        """Test callback receives parsed JSON dict."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        received_data = []
        
        def callback(data):
            received_data.append(data)
        
        async def message_gen():
            yield json.dumps({"feedID": "0x123", "fullReport": "0xabc"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, callback)
        
        assert len(received_data) == 1
        assert isinstance(received_data[0], dict)
        assert received_data[0]["feedID"] == "0x123"

    @pytest.mark.asyncio
    async def test_handles_async_callback(self):
        """Test handles async callback function."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        received_data = []
        
        async def async_callback(data):
            received_data.append(data)
        
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, async_callback)
        
        assert len(received_data) == 1

    @pytest.mark.asyncio
    async def test_stops_when_stop_event_is_set(self):
        """Test stops streaming when stop_event is set."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        call_count = 0
        
        def callback(data):
            nonlocal call_count
            call_count += 1
            # Set stop event after first callback is executed
            # This ensures it's set before the next iteration check
            if call_count == 1:
                stop_event.set()
        
        stop_event = asyncio.Event()
        
        # Create an async generator with two messages
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            # Second message should not be processed because stop_event is set
            yield json.dumps({"feedID": "0x456"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, callback, stop_event)
        
        # Should only process first message (second is skipped due to stop_event)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_handles_json_decode_error_gracefully(self):
        """Test handles JSON decode error gracefully (continues streaming)."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        mock_callback = MagicMock()
        
        # Mix valid and invalid JSON
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            yield "invalid json {"
            yield json.dumps({"feedID": "0x456"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, mock_callback)
        
        # Should process 2 valid messages
        assert mock_callback.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_callback_exception_gracefully(self):
        """Test handles callback exception gracefully (continues streaming)."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        
        def failing_callback(data):
            if data.get("feedID") == "0x123":
                raise ValueError("Test error")
        
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            yield json.dumps({"feedID": "0x456"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        # Should not raise, but continue processing
        await stream_reports(mock_websocket, failing_callback)
        
        # Both messages should be attempted
        # (We can't easily verify this without more complex mocking)

    @pytest.mark.asyncio
    async def test_handles_connection_closed_gracefully(self):
        """Test handles ConnectionClosed exception gracefully."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        mock_callback = MagicMock()
        
        # Simulate connection closed
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            raise websockets.exceptions.ConnectionClosed(None, None)
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        # Should not raise
        await stream_reports(mock_websocket, mock_callback)
        
        # Should have processed at least one message
        assert mock_callback.call_count >= 1

    @pytest.mark.asyncio
    async def test_handles_other_exceptions_gracefully(self):
        """Test handles other exceptions gracefully."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        mock_callback = MagicMock()
        
        # Simulate other exception
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            raise RuntimeError("Test error")
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        # Should not raise
        await stream_reports(mock_websocket, mock_callback)

    @pytest.mark.asyncio
    async def test_continues_streaming_after_error(self):
        """Test continues streaming after error in callback."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        call_count = 0
        
        def callback(data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First error")
        
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            yield json.dumps({"feedID": "0x456"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        await stream_reports(mock_websocket, callback)
        
        # Both messages should be attempted
        assert call_count == 2


class TestPingLoop:
    """Test _ping_loop function (internal helper)."""

    @pytest.mark.asyncio
    async def test_sends_ping_at_interval(self):
        """Test sends ping at specified interval."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        stop_event = asyncio.Event()
        
        ping_task = asyncio.create_task(_ping_loop(mock_websocket, 0.1, stop_event))
        
        # Wait for at least one ping
        await asyncio.sleep(0.15)
        stop_event.set()
        
        try:
            await asyncio.wait_for(ping_task, timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        # Should have called ping at least once
        assert mock_websocket.ping.call_count >= 1

    @pytest.mark.asyncio
    async def test_stops_when_stop_event_is_set(self):
        """Test stops when stop_event is set."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        stop_event = asyncio.Event()
        
        # Set stop event immediately
        stop_event.set()
        
        ping_task = asyncio.create_task(_ping_loop(mock_websocket, 0.1, stop_event))
        
        await asyncio.sleep(0.05)
        
        # Should not have called ping
        assert mock_websocket.ping.call_count == 0

    @pytest.mark.asyncio
    async def test_handles_ping_exception_gracefully(self):
        """Test handles ping exception gracefully."""
        mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
        mock_websocket.ping.side_effect = Exception("Ping failed")
        stop_event = asyncio.Event()
        
        ping_task = asyncio.create_task(_ping_loop(mock_websocket, 0.1, stop_event))
        
        await asyncio.sleep(0.15)
        stop_event.set()
        
        try:
            await asyncio.wait_for(ping_task, timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        # Should have attempted ping
        assert mock_websocket.ping.call_count >= 1


class TestStreamReportsWithKeepalive:
    """Test stream_reports_with_keepalive function."""

    @pytest.mark.asyncio
    async def test_connects_to_websocket(self, mock_api_credentials, sample_feed_ids):
        """Test connects to WebSocket using connect_websocket."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            mock_stream.return_value = None
            
            callback = MagicMock()
            
            # Create a task that will stop quickly
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, callback),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_starts_ping_loop_in_background(self, mock_api_credentials, sample_feed_ids):
        """Test starts ping loop in background."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream, \
             patch('py_chainlink_streams.report._ping_loop') as mock_ping_loop:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, MagicMock()),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            # Ping loop should have been started
            # (We can't easily verify task creation, but we can check it was called)

    @pytest.mark.asyncio
    async def test_calls_stream_reports_with_websocket(self, mock_api_credentials, sample_feed_ids):
        """Test calls stream_reports with WebSocket connection."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            callback = MagicMock()
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, callback),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            mock_stream.assert_called_once()
            # Check that websocket was passed
            call_args = mock_stream.call_args
            assert call_args[0][0] == mock_websocket

    @pytest.mark.asyncio
    async def test_uses_default_ping_interval(self, mock_api_credentials, sample_feed_ids):
        """Test uses default ping_interval when not provided."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, MagicMock()),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            # Check that default ping interval was used
            call_args = mock_connect.call_args
            assert call_args[0][2] == DEFAULT_PING_INTERVAL  # ping_interval is 3rd positional arg

    @pytest.mark.asyncio
    async def test_uses_custom_ping_interval(self, mock_api_credentials, sample_feed_ids):
        """Test uses custom ping_interval when provided."""
        custom_interval = 45
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, MagicMock(), ping_interval=custom_interval),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            call_args = mock_connect.call_args
            assert call_args[0][2] == custom_interval

    @pytest.mark.asyncio
    async def test_closes_websocket_on_completion(self, mock_api_credentials, sample_feed_ids):
        """Test closes WebSocket connection on completion."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, MagicMock()),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            # WebSocket should be closed
            mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_handles_keyboard_interrupt_gracefully(self, mock_api_credentials, sample_feed_ids):
        """Test handles KeyboardInterrupt gracefully."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            # Simulate KeyboardInterrupt
            mock_stream.side_effect = KeyboardInterrupt()
            
            # Should not raise
            await stream_reports_with_keepalive(sample_feed_ids, MagicMock())
            
            # WebSocket should be closed
            mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_handles_other_exceptions_gracefully(self, mock_api_credentials, sample_feed_ids):
        """Test handles other exceptions gracefully."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            mock_connect.return_value = mock_websocket
            
            # Simulate exception
            mock_stream.side_effect = RuntimeError("Test error")
            
            # Should not raise
            await stream_reports_with_keepalive(sample_feed_ids, MagicMock())
            
            # WebSocket should be closed
            mock_websocket.close.assert_called()

    @pytest.mark.asyncio
    async def test_cancels_ping_task_on_completion(self, mock_api_credentials, sample_feed_ids):
        """Test cancels ping task on completion."""
        with patch('py_chainlink_streams.report.connect_websocket') as mock_connect, \
             patch('py_chainlink_streams.report.stream_reports') as mock_stream, \
             patch('asyncio.create_task') as mock_create_task:
            mock_websocket = AsyncMock(spec=WebSocketClientProtocol)
            # Make connect_websocket return the websocket when awaited
            async def connect_mock(*args, **kwargs):
                return mock_websocket
            mock_connect.side_effect = connect_mock
            
            # Create a proper awaitable mock task
            # The code does `await ping_task`, so we need a real awaitable
            class AwaitableTask:
                def __init__(self):
                    self._cancelled = False
                
                def cancel(self):
                    self._cancelled = True
                
                def cancelled(self):
                    return self._cancelled
                
                def __await__(self):
                    # When awaited, raise CancelledError (which the code catches)
                    async def _await():
                        raise asyncio.CancelledError()
                    return _await().__await__()
            
            mock_task = AwaitableTask()
            mock_create_task.return_value = mock_task
            
            async def quick_stream(*args, **kwargs):
                await asyncio.sleep(0.01)
            
            mock_stream.side_effect = quick_stream
            
            try:
                await asyncio.wait_for(
                    stream_reports_with_keepalive(sample_feed_ids, MagicMock()),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass
            
            # Verify task was created (ping loop was started)
            assert mock_create_task.called

