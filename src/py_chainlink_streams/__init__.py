"""
Chainlink Data Streams Python SDK

A lightweight Python client for Chainlink Data Streams API with support for
both HTTP REST API and WebSocket connections, including report decoding.

Based on: https://docs.chain.link/data-streams/reference/data-streams-api/authentication
"""

from py_chainlink_streams.client import (
    fetch_single_report,
    connect_websocket,
    stream_reports,
    stream_reports_with_keepalive,
    get_api_credentials,
    generate_hmac,
    generate_auth_headers,
)

from py_chainlink_streams.decode import (
    get_schema_version,
    decode_report_structure,
    decode_v3_report_data,
    decode_report,
    decode_report_from_response,
    convert_fixed_point_to_decimal,
    get_decoded_prices,
)

from py_chainlink_streams.constants import (
    TESTNET_API_HOST,
    TESTNET_WS_HOST,
    MAINNET_API_HOST,
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)

__version__ = "0.1.0"

__all__ = [
    # Client functions
    "fetch_single_report",
    "connect_websocket",
    "stream_reports",
    "stream_reports_with_keepalive",
    "get_api_credentials",
    "generate_hmac",
    "generate_auth_headers",
    # Decode functions
    "get_schema_version",
    "decode_report_structure",
    "decode_v3_report_data",
    "decode_report",
    "decode_report_from_response",
    "convert_fixed_point_to_decimal",
    "get_decoded_prices",
    # Constants
    "TESTNET_API_HOST",
    "TESTNET_WS_HOST",
    "MAINNET_API_HOST",
    "MAINNET_WS_HOST",
    "DEFAULT_PING_INTERVAL",
    "DEFAULT_PONG_TIMEOUT",
]

