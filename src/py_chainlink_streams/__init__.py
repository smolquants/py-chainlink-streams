"""
Chainlink Data Streams Python SDK

A lightweight Python client for Chainlink Data Streams API with support for
both HTTP REST API and WebSocket connections, including report decoding.

Based on: https://docs.chain.link/data-streams/reference/data-streams-api/authentication
"""

from py_chainlink_streams.auth import (
    get_api_credentials,
    generate_hmac,
    generate_auth_headers,
)

from py_chainlink_streams.report import (
    ReportResponse,
    ReportPage,
)

from py_chainlink_streams.constants import (
    TESTNET_API_HOST,
    TESTNET_WS_HOST,
    MAINNET_API_HOST,
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)

from py_chainlink_streams.config import ChainlinkConfig
from py_chainlink_streams.client import ChainlinkClient
from py_chainlink_streams.feed import Feed

__version__ = "0.3.2"

__all__ = [
    # Client class and config
    "ChainlinkClient",
    "ChainlinkConfig",
    # Data classes
    "ReportResponse",
    "ReportPage",
    "Feed",
    # Authentication utilities (for advanced use cases)
    "get_api_credentials",
    "generate_hmac",
    "generate_auth_headers",
    # Constants
    "TESTNET_API_HOST",
    "TESTNET_WS_HOST",
    "MAINNET_API_HOST",
    "MAINNET_WS_HOST",
    "DEFAULT_PING_INTERVAL",
    "DEFAULT_PONG_TIMEOUT",
]

