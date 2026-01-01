"""
Tests for py_chainlink_streams.report module.

This module tests internal functions used by ChainlinkClient:
- stream_reports: Internal function for processing WebSocket messages
- _ping_loop: Internal function for WebSocket keepalive
"""

import asyncio
import json
import pytest
from unittest.mock import MagicMock
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.report import (
    stream_reports,
    _ping_loop,
)


class TestStreamReports:
    """Test stream_reports function (internal)."""

    @pytest.mark.asyncio
    async def test_calls_callback_for_each_message(self):
        """Test calls callback for each message received."""
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
        
        def failing_callback(data):
            if data.get("feedID") == "0x123":
                raise ValueError("Test error")
        
        async def message_gen():
            yield json.dumps({"feedID": "0x123"})
            yield json.dumps({"feedID": "0x456"})
        
        mock_websocket.__aiter__ = lambda self: message_gen()
        
        # Should not raise, but continue processing
        await stream_reports(mock_websocket, failing_callback)

    @pytest.mark.asyncio
    async def test_handles_connection_closed_gracefully(self):
        """Test handles ConnectionClosed exception gracefully."""
        mock_websocket = MagicMock(spec=WebSocketClientProtocol)
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

class TestPingLoop:
    """Test _ping_loop function (internal helper)."""

    @pytest.mark.asyncio
    async def test_sends_ping_at_interval(self):
        """Test sends ping at specified interval."""
        mock_websocket = MagicMock()
        mock_websocket.ping = MagicMock()
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
        mock_websocket = MagicMock()
        mock_websocket.ping = MagicMock()
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
        mock_websocket = MagicMock()
        mock_websocket.ping = MagicMock(side_effect=Exception("Ping failed"))
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
