"""
Tests for py_chainlink_streams.auth module.
"""

import os
import time
import pytest

from py_chainlink_streams.auth import (
    get_api_credentials,
    generate_hmac,
    generate_auth_headers,
)


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
        """Test raises ValueError when both env vars are missing."""
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_raises_when_empty_string(self, monkeypatch):
        """Test raises ValueError when env vars are empty strings."""
        monkeypatch.setenv("CHAINLINK_STREAMS_API_KEY", "")
        monkeypatch.setenv("CHAINLINK_STREAMS_API_SECRET", "")
        with pytest.raises(ValueError, match="API credentials not set"):
            get_api_credentials()

    def test_returns_correct_values_from_environment(self, monkeypatch):
        """Test returns correct values from environment variables."""
        monkeypatch.setenv("CHAINLINK_STREAMS_API_KEY", "env-key")
        monkeypatch.setenv("CHAINLINK_STREAMS_API_SECRET", "env-secret")
        api_key, api_secret = get_api_credentials()
        assert api_key == "env-key"
        assert api_secret == "env-secret"


class TestGenerateHMAC:
    """Test generate_hmac function."""

    def test_returns_tuple_of_signature_and_timestamp(self):
        """Test returns tuple of (signature, timestamp)."""
        sig, ts = generate_hmac("GET", "/test", b"", "key", "secret")
        assert isinstance(sig, str)
        assert isinstance(ts, int)

    def test_signature_is_64_char_hex_string(self):
        """Test signature is 64 character hex string."""
        sig, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        assert len(sig) == 64
        assert all(c in '0123456789abcdef' for c in sig)

    def test_timestamp_is_integer_milliseconds(self):
        """Test timestamp is integer in milliseconds."""
        _, ts = generate_hmac("GET", "/test", b"", "key", "secret")
        assert isinstance(ts, int)
        # Should be roughly current time in milliseconds
        current_ms = int(time.time() * 1000)
        assert abs(ts - current_ms) < 1000  # Within 1 second

    def test_same_inputs_produce_same_signature(self):
        """Test same inputs produce same signature (if timestamp is same)."""
        # Mock time to get consistent timestamps
        from unittest.mock import patch
        with patch('py_chainlink_streams.auth.time.time', return_value=1000.0):
            sig1, ts1 = generate_hmac("GET", "/test", b"", "key", "secret")
            sig2, ts2 = generate_hmac("GET", "/test", b"", "key", "secret")
            assert sig1 == sig2
            assert ts1 == ts2

    def test_different_timestamps_produce_different_signatures(self):
        """Test different timestamps produce different signatures."""
        from unittest.mock import patch
        with patch('py_chainlink_streams.auth.time.time', return_value=1000.0):
            sig1, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        with patch('py_chainlink_streams.auth.time.time', return_value=2000.0):
            sig2, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        assert sig1 != sig2

    def test_different_paths_produce_different_signatures(self):
        """Test different paths produce different signatures."""
        sig1, _ = generate_hmac("GET", "/path1", b"", "key", "secret")
        sig2, _ = generate_hmac("GET", "/path2", b"", "key", "secret")
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
        sig, _ = generate_hmac("GET", "/test", b"", "key", "secret")
        assert len(sig) == 64

    def test_non_empty_body_produces_valid_signature(self):
        """Test non-empty body produces valid signature."""
        sig, _ = generate_hmac("POST", "/test", b"test body", "key", "secret")
        assert len(sig) == 64

    def test_handles_special_characters_in_path(self):
        """Test handles special characters in path."""
        sig, _ = generate_hmac("GET", "/test?param=value&other=123", b"", "key", "secret")
        assert len(sig) == 64

    def test_handles_query_parameters_in_path(self):
        """Test handles query parameters in path."""
        sig, _ = generate_hmac("GET", "/api/v1/reports?feedID=0x123", b"", "key", "secret")
        assert len(sig) == 64


class TestGenerateAuthHeaders:
    """Test generate_auth_headers function."""

    def test_returns_dict_with_correct_keys(self):
        """Test returns dict with correct header keys."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        assert "Authorization" in headers
        assert "X-Authorization-Timestamp" in headers
        assert "X-Authorization-Signature-SHA256" in headers

    def test_authorization_header_equals_api_key(self):
        """Test Authorization header equals API key."""
        headers = generate_auth_headers("GET", "/test", "test-key", "secret")
        assert headers["Authorization"] == "test-key"

    def test_timestamp_header_is_string_representation_of_int(self):
        """Test timestamp header is string representation of int."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        timestamp_str = headers["X-Authorization-Timestamp"]
        # Should be able to convert to int
        timestamp_int = int(timestamp_str)
        assert isinstance(timestamp_int, int)

    def test_signature_header_is_64_char_hex_string(self):
        """Test signature header is 64 character hex string."""
        headers = generate_auth_headers("GET", "/test", "key", "secret")
        signature = headers["X-Authorization-Signature-SHA256"]
        assert len(signature) == 64
        assert all(c in '0123456789abcdef' for c in signature)

    def test_default_body_parameter_works(self):
        """Test default body parameter works."""
        headers1 = generate_auth_headers("GET", "/test", "key", "secret")
        headers2 = generate_auth_headers("GET", "/test", "key", "secret", b"")
        # Signatures should be the same
        assert headers1["X-Authorization-Signature-SHA256"] == headers2["X-Authorization-Signature-SHA256"]

    def test_custom_body_parameter_works(self):
        """Test custom body parameter works."""
        headers = generate_auth_headers("POST", "/test", "key", "secret", b"test body")
        assert "X-Authorization-Signature-SHA256" in headers
        assert len(headers["X-Authorization-Signature-SHA256"]) == 64

