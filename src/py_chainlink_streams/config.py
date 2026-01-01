"""
Configuration management for Chainlink Data Streams client.

This module provides the ChainlinkConfig dataclass for centralized configuration
and the ChainlinkClient class for a more object-oriented API.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable

from py_chainlink_streams.constants import (
    MAINNET_API_HOST,
    MAINNET_WS_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


@dataclass
class ChainlinkConfig:
    """
    Configuration for Chainlink Data Streams client.
    
    Attributes:
        api_key: Chainlink Data Streams API key
        api_secret: Chainlink Data Streams API secret
        api_host: REST API host (default: MAINNET_API_HOST)
        ws_host: WebSocket host (default: MAINNET_WS_HOST)
        ping_interval: Seconds between ping messages (default: 30)
        pong_timeout: Seconds to wait for pong before timeout (default: 60)
        timeout: HTTP request timeout in seconds (default: 30)
        logger: Optional logging function (default: None, uses print)
        ws_ha: Enable WebSocket high availability mode (default: False)
        ws_max_reconnect: Maximum WebSocket reconnection attempts (default: 10)
        insecure_skip_verify: Skip TLS certificate verification (default: False)
    """
    api_key: str
    api_secret: str
    api_host: str = MAINNET_API_HOST
    ws_host: str = MAINNET_WS_HOST
    ping_interval: int = DEFAULT_PING_INTERVAL
    pong_timeout: int = DEFAULT_PONG_TIMEOUT
    timeout: int = 30
    logger: Optional[Callable[[str], None]] = None
    ws_ha: bool = False
    ws_max_reconnect: int = 10
    insecure_skip_verify: bool = False
    
    def _log(self, message: str) -> None:
        """Internal logging helper."""
        if self.logger:
            self.logger(message)
        else:
            print(message)

