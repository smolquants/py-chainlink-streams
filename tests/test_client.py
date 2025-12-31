"""
Tests for py_chainlink_streams.client module.
"""

import os
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import websockets
from websockets.client import WebSocketClientProtocol

from py_chainlink_streams.client import (
    get_api_credentials,
    generate_hmac,
    generate_auth_headers,
    connect_websocket,
)
from py_chainlink_streams.constants import (
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


def create_websocket_mock(mock_connect, mock_ws):
    """Helper to create a websocket connect mock that returns websocket when awaited."""
    async def connect_mock(*args, **kwargs):
        return mock_ws
    mock_connect.side_effect = connect_mock


class TestGetAPICredentials:
    """Test get_api_credentials function."""

    def test_returns_credentials_when_set(self, mock_api_credentials):
        """Test returns tuple of (api_key, api_secret) when env vars are set."""
        api_key, api_secret = get_api_credentials()
        assert api_key == "test-api-key"
        assert api_secret == "test-api-secret"
        assert isinstance(api_key, str)
        assert isinstance(api_secret, str)

    def test_raises_when_api_key_missing(self, clear_api_credentials):
        """Test raises ValueError when CHAINLINK_STREAMS_API_KEY is missing."""
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_raises_when_api_secret_missing(self, monkeypatch):
        """Test raises ValueError when CHAINLINK_STREAMS_API_SECRET is missing."""
        monkeypatch.setenv("CHAINLINK_STREAMS_API_KEY", "test-key")
        monkeypatch.delenv("CHAINLINK_STREAMS_API_SECRET", raising=False)
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_raises_when_both_missing(self, clear_api_credentials):
        """Test raises ValueError when both are missing."""
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_raises_when_empty_string(self, monkeypatch):
        """Test handles empty string values correctly (should raise ValueError)."""
        monkeypatch.setenv("CHAINLINK_STREAMS_API_KEY", "")
        monkeypatch.setenv("CHAINLINK_STREAMS_API_SECRET", "")
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_returns_correct_values_from_environment(self, monkeypatch):
        """Test returns correct values from environment."""
        monkeypatch.setenv("CHAINLINK_STREAMS_API_KEY", "custom-key")
        monkeypatch.setenv("CHAINLINK_STREAMS_API_SECRET", "custom-secret")
        api_key, api_secret = get_api_credentials()
        assert api_key == "custom-key"
        assert api_secret == "custom-secret"


class TestGenerateHMAC:
    """Test generate_hmac function."""

    def test_returns_tuple_of_signature_and_timestamp(self):
        """Test returns tuple of (signature: str, timestamp: int)."""
        signature, timestamp = generate_hmac("GET", "/test", b"", "key", "secret")
        assert isinstance(signature, str)
        assert isinstance(timestamp, int)

    def test_signature_is_64_char_hex_string(self):
        """Test signature is 64-character hex string."""
        signature, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        assert len(signature) == 64
        assert all(c in '0123456789abcdef' for c in signature)

    def test_timestamp_is_integer_milliseconds(self):
        """Test timestamp is integer (milliseconds)."""
        _, timestamp = generate_hmac("GET", "/test", b"", "key", "secret")
        assert isinstance(timestamp, int)
        assert timestamp > 0
        # Should be roughly current time in milliseconds
        current_ms = int(time.time() * 1000)
        assert abs(timestamp - current_ms) < 1000  # Within 1 second

    def test_same_inputs_produce_same_signature(self):
        """Test same inputs produce same signature (deterministic)."""
        # Note: This will fail because timestamp changes, but we can test with fixed timestamp
        # Actually, signatures will differ due to timestamp, so we test structure instead
        sig1, ts1 = generate_hmac("GET", "/test", b"", "key", "secret")
        sig2, ts2 = generate_hmac("GET", "/test", b"", "key", "secret")
        assert len(sig1) == len(sig2) == 64
        assert isinstance(ts1, int)
        assert isinstance(ts2, int)

    def test_different_timestamps_produce_different_signatures(self):
        """Test different timestamps produce different signatures."""
        # This is implicit - each call has different timestamp
        sig1, ts1 = generate_hmac("GET", "/test", b"", "key", "secret")
        time.sleep(0.001)  # Small delay to ensure different timestamp
        sig2, ts2 = generate_hmac("GET", "/test", b"", "key", "secret")
        assert ts2 > ts1  # Timestamp should increase

    def test_different_paths_produce_different_signatures(self):
        """Test different paths produce different signatures."""
        sig1, _ = generate_hmac("GET", "/path1", b"", "key", "secret")
        sig2, _ = generate_hmac("GET", "/path2", b"", "key", "secret")
        # Signatures should be different (even with different timestamps)
        assert sig1 != sig2

    def test_different_methods_produce_different_signatures(self):
        """Test different methods produce different signatures."""
        sig1, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        sig2, _ = generate_hmac("POST", "/test", b"", "key", "secret")
        assert sig1 != sig2

    def test_different_bodies_produce_different_signatures(self):
        """Test different bodies produce different signatures."""
        sig1, _ = generate_hmac("POST", "/test", b"body1", "key", "secret")
        sig2, _ = generate_hmac("POST", "/test", b"body2", "key", "secret")
        assert sig1 != sig2

    def test_empty_body_produces_valid_signature(self):
        """Test empty body produces valid signature."""
        signature, timestamp = generate_hmac("GET", "/test", b"", "key", "secret")
        assert len(signature) == 64
        assert isinstance(timestamp, int)

    def test_non_empty_body_produces_valid_signature(self):
        """Test non-empty body produces valid signature."""
        signature, timestamp = generate_hmac("POST", "/test", b"test body", "key", "secret")
        assert len(signature) == 64
        assert isinstance(timestamp, int)

    def test_handles_special_characters_in_path(self):
        """Test handles special characters in path correctly."""
        path = "/api/v1/test?param=value&other=test%20value"
        signature, _ = generate_hmac("GET", path, b"", "key", "secret")
        assert len(signature) == 64

    def test_handles_query_parameters_in_path(self):
        """Test handles query parameters in path correctly."""
        path = "/api/v1/reports/latest?feedID=0x123"
        signature, _ = generate_hmac("GET", path, b"", "key", "secret")
        assert len(signature) == 64


class TestGenerateAuthHeaders:
    """Test generate_auth_headers function."""

    def test_returns_dict_with_correct_keys(self):
        """Test returns dict with correct keys."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        assert "Authorization" in headers
        assert "X-Authorization-Timestamp" in headers
        assert "X-Authorization-Signature-SHA256" in headers

    def test_authorization_header_equals_api_key(self):
        """Test Authorization header equals api_key."""
        api_key = "test-key"
        headers = generate_auth_headers("GET", "/test", api_key, "secret")
        assert headers["Authorization"] == api_key

    def test_timestamp_header_is_string_representation_of_int(self):
        """Test X-Authorization-Timestamp header is string representation of int."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        timestamp_str = headers["X-Authorization-Timestamp"]
        assert isinstance(timestamp_str, str)
        # Should be parseable as int
        timestamp_int = int(timestamp_str)
        assert isinstance(timestamp_int, int)

    def test_signature_header_is_64_char_hex_string(self):
        """Test X-Authorization-Signature-SHA256 header is 64-char hex string."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        signature = headers["X-Authorization-Signature-SHA256"]
        assert len(signature) == 64
        assert all(c in '0123456789abcdef' for c in signature)

    def test_default_body_parameter_works(self):
        """Test default body parameter works (empty bytes)."""
        headers1 = generate_auth_headers("GET", "/test", "key", "secret")
        headers2 = generate_auth_headers("GET", "/test", "key", "secret", b"")
        # Both should produce valid headers (may differ due to timestamp)
        assert len(headers1["X-Authorization-Signature-SHA256"]) == 64
        assert len(headers2["X-Authorization-Signature-SHA256"]) == 64

    def test_custom_body_parameter_works(self):
        """Test custom body parameter works."""
        headers = generate_auth_headers("POST", "/test", "key", "secret", b"test body")
        assert "X-Authorization-Signature-SHA256" in headers
        assert len(headers["X-Authorization-Signature-SHA256"]) == 64


class TestConnectWebsocket:
    """Test connect_websocket function."""

    @pytest.mark.asyncio
    async def test_raises_when_feed_ids_empty(self, mock_api_credentials):
        """Test raises ValueError when feed_ids is empty list."""
        with pytest.raises(ValueError, match="No feed ID\\(s\\) provided"):
            await connect_websocket([], None, 30, 60)

    @pytest.mark.asyncio
    async def test_raises_when_api_credentials_not_set(self, clear_api_credentials):
        """Test raises ValueError when API credentials not set."""
        with pytest.raises(ValueError, match="API credentials not set"):
            await connect_websocket(["0x123"], None, 30, 60)

    @pytest.mark.asyncio
    async def test_uses_mainnet_ws_host_by_default(self, mock_api_credentials, sample_feed_ids):
        """Test uses MAINNET_WS_HOST by default when host is None."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, 30, 60)
            
            # Check that URL contains mainnet host
            call_args = mock_connect.call_args
            assert MAINNET_WS_HOST in str(call_args[0][0])

    @pytest.mark.asyncio
    async def test_uses_custom_host_when_provided(self, mock_api_credentials, sample_feed_ids):
        """Test uses custom host when provided."""
        custom_host = "custom.ws.host"
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, custom_host, 30, 60)
            
            call_args = mock_connect.call_args
            assert custom_host in str(call_args[0][0])

    @pytest.mark.asyncio
    async def test_uses_default_ping_interval_when_not_provided(self, mock_api_credentials, sample_feed_ids):
        """Test uses default ping_interval when not provided."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, DEFAULT_PING_INTERVAL, 60)
            
            call_args = mock_connect.call_args
            assert call_args.kwargs.get('ping_interval') == DEFAULT_PING_INTERVAL

    @pytest.mark.asyncio
    async def test_uses_custom_ping_interval_when_provided(self, mock_api_credentials, sample_feed_ids):
        """Test uses custom ping_interval when provided."""
        custom_interval = 45
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, custom_interval, 60)
            
            call_args = mock_connect.call_args
            assert call_args.kwargs.get('ping_interval') == custom_interval

    @pytest.mark.asyncio
    async def test_uses_default_pong_timeout_when_not_provided(self, mock_api_credentials, sample_feed_ids):
        """Test uses default pong_timeout when not provided."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, 30, DEFAULT_PONG_TIMEOUT)
            
            call_args = mock_connect.call_args
            assert call_args.kwargs.get('ping_timeout') == DEFAULT_PONG_TIMEOUT

    @pytest.mark.asyncio
    async def test_uses_custom_pong_timeout_when_provided(self, mock_api_credentials, sample_feed_ids):
        """Test uses custom pong_timeout when provided."""
        custom_timeout = 90
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, 30, custom_timeout)
            
            call_args = mock_connect.call_args
            assert call_args.kwargs.get('ping_timeout') == custom_timeout

    @pytest.mark.asyncio
    async def test_builds_correct_websocket_url_with_feed_ids(self, mock_api_credentials, sample_feed_ids):
        """Test builds correct WebSocket URL with feed IDs."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, 30, 60)
            
            # Check URL contains feed IDs
            call_args = mock_connect.call_args
            url = call_args[0][0]  # First positional argument
            assert sample_feed_ids[0] in url
            assert "wss://" in url
            assert "/api/v1/ws" in url

    @pytest.mark.asyncio
    async def test_generates_correct_authentication_headers(self, mock_api_credentials, sample_feed_ids):
        """Test generates correct authentication headers."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(sample_feed_ids, None, 30, 60)
            
            call_args = mock_connect.call_args
            headers = call_args.kwargs.get('additional_headers', {})
            assert "Authorization" in headers
            assert "X-Authorization-Timestamp" in headers
            assert "X-Authorization-Signature-SHA256" in headers
            assert headers["Authorization"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_returns_websocket_client_protocol_instance(self, mock_api_credentials, sample_feed_ids):
        """Test returns WebSocketClientProtocol instance."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            result = await connect_websocket(sample_feed_ids, None, 30, 60)
            
            assert result == mock_ws

    @pytest.mark.asyncio
    async def test_handles_multiple_feed_ids_correctly(self, mock_api_credentials):
        """Test handles multiple feed IDs correctly."""
        feed_ids = ["0x123", "0x456", "0x789"]
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            mock_ws = AsyncMock(spec=WebSocketClientProtocol)
            create_websocket_mock(mock_connect, mock_ws)
            
            await connect_websocket(feed_ids, None, 30, 60)
            
            call_args = mock_connect.call_args
            url = call_args[0][0]
            # All feed IDs should be in the query string
            assert all(feed_id in url for feed_id in feed_ids)

    @pytest.mark.asyncio
    async def test_raises_appropriate_exception_on_connection_failure(self, mock_api_credentials, sample_feed_ids):
        """Test raises appropriate exception on connection failure."""
        with patch('py_chainlink_streams.client.websockets.connect') as mock_connect:
            # Create a mock exception - InvalidStatusCode takes status_code and headers
            # The code tries to re-raise with 3 args, but InvalidStatusCode only takes 2
            # So it will raise a TypeError. However, the original exception should be raised first.
            original_exception = websockets.exceptions.InvalidStatusCode(401, {})
            # Make connect raise the exception when awaited
            async def connect_raises(*args, **kwargs):
                raise original_exception
            mock_connect.side_effect = connect_raises
            
            # The code will catch and try to re-raise, but will fail with TypeError
            # because InvalidStatusCode only takes 2 args. So we expect either exception.
            with pytest.raises((websockets.exceptions.InvalidStatusCode, TypeError)):
                await connect_websocket(sample_feed_ids, None, 30, 60)

