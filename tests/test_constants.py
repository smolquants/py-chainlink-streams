"""
Tests for py_chainlink_streams.constants module.
"""

import pytest
from py_chainlink_streams.constants import (
    MAINNET_API_HOST,
    MAINNET_WS_HOST,
    TESTNET_API_HOST,
    TESTNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


class TestConstants:
    """Test constants are correctly defined and importable."""

    def test_mainnet_api_host(self):
        """Test MAINNET_API_HOST is correct string."""
        assert MAINNET_API_HOST == "api.dataengine.chain.link"
        assert isinstance(MAINNET_API_HOST, str)

    def test_mainnet_ws_host(self):
        """Test MAINNET_WS_HOST is correct string."""
        assert MAINNET_WS_HOST == "ws.dataengine.chain.link"
        assert isinstance(MAINNET_WS_HOST, str)

    def test_testnet_api_host(self):
        """Test TESTNET_API_HOST is correct string."""
        assert TESTNET_API_HOST == "api.testnet-dataengine.chain.link"
        assert isinstance(TESTNET_API_HOST, str)

    def test_testnet_ws_host(self):
        """Test TESTNET_WS_HOST is correct string."""
        assert TESTNET_WS_HOST == "ws.testnet-dataengine.chain.link"
        assert isinstance(TESTNET_WS_HOST, str)

    def test_default_ping_interval(self):
        """Test DEFAULT_PING_INTERVAL is correct integer."""
        assert DEFAULT_PING_INTERVAL == 30
        assert isinstance(DEFAULT_PING_INTERVAL, int)

    def test_default_pong_timeout(self):
        """Test DEFAULT_PONG_TIMEOUT is correct integer."""
        assert DEFAULT_PONG_TIMEOUT == 60
        assert isinstance(DEFAULT_PONG_TIMEOUT, int)

    def test_all_constants_importable_from_package(self):
        """Test all constants can be imported from main package."""
        from py_chainlink_streams import (
            MAINNET_API_HOST,
            MAINNET_WS_HOST,
            TESTNET_API_HOST,
            TESTNET_WS_HOST,
            DEFAULT_PING_INTERVAL,
            DEFAULT_PONG_TIMEOUT,
        )
        assert all([
            MAINNET_API_HOST,
            MAINNET_WS_HOST,
            TESTNET_API_HOST,
            TESTNET_WS_HOST,
            DEFAULT_PING_INTERVAL,
            DEFAULT_PONG_TIMEOUT,
        ])

