"""
Chainlink Data Streams report classes and streaming functionality.

This module provides ReportResponse and ReportPage classes with decoding capabilities,
and internal functions for WebSocket streaming used by ChainlinkClient.
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
import websockets
from websockets.client import WebSocketClientProtocol
from eth_abi import decode
from eth_utils import remove_0x_prefix

from py_chainlink_streams.constants import (
    DEFAULT_PING_INTERVAL,
    DEFAULT_PONG_TIMEOUT,
)


class ReportResponse:
    """
    Report response from Chainlink Data Streams API.
    
    Attributes:
        feed_id: Feed identifier (hex string)
        full_report: Full report data (hex encoded string, starts with "0x")
        valid_from_timestamp: Timestamp when report becomes valid (Unix timestamp)
        observations_timestamp: Timestamp of observations (Unix timestamp)
    """
    
    def __init__(
        self,
        feed_id: str,
        full_report: str,
        valid_from_timestamp: int,
        observations_timestamp: int
    ):
        self.feed_id = feed_id
        self.full_report = full_report
        self.valid_from_timestamp = valid_from_timestamp
        self.observations_timestamp = observations_timestamp
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportResponse":
        """Create ReportResponse from API response dictionary."""
        # Handle nested structure (API wraps in 'report' key)
        if "report" in data:
            report_data = data["report"]
        else:
            report_data = data
        
        return cls(
            feed_id=report_data["feedID"],
            full_report=report_data["fullReport"],
            valid_from_timestamp=report_data["validFromTimestamp"],
            observations_timestamp=report_data["observationsTimestamp"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "feedID": self.feed_id,
            "fullReport": self.full_report,
            "validFromTimestamp": self.valid_from_timestamp,
            "observationsTimestamp": self.observations_timestamp
        }
    
    @staticmethod
    def get_schema_version(feed_id: str) -> int:
        """
        Determine the report schema version from the feed ID prefix.
        
        Schema versions are determined by the first 4 hex characters after '0x':
        - 0x0001 = v1
        - 0x0002 = v2
        - 0x0003 = v3 (Crypto Streams)
        - 0x0004 = v4
        - etc.
        
        Args:
            feed_id: Feed ID hex string (e.g., "0x000359843a543ee2...")
            
        Returns:
            Schema version number (e.g., 3 for v3)
        """
        if not feed_id.startswith('0x'):
            raise ValueError(f"Invalid feed ID format: {feed_id}")
        
        # Extract first 4 hex chars (2 bytes) after '0x'
        prefix = feed_id[2:6]
        try:
            version = int(prefix, 16)
            return version
        except ValueError:
            raise ValueError(f"Could not determine schema version from feed ID: {feed_id}")
    
    @staticmethod
    def _decode_report_structure(full_report_hex: str) -> Dict[str, Any]:
        """
        Decode the outer report structure from hex-encoded fullReport.
        
        Internal method used by decode().
        """
        # Remove '0x' prefix if present
        hex_data = remove_0x_prefix(full_report_hex)
        report_bytes = bytes.fromhex(hex_data)
        
        # Decode the outer structure
        # ABI encoding: (bytes32[3], bytes, bytes32[], bytes32[], bytes32)
        types = ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32']
        decoded = decode(types, report_bytes)
        
        return {
            'reportContext': decoded[0],  # tuple of 3 bytes32
            'reportBlob': decoded[1],      # bytes
            'rawRs': decoded[2],            # list of bytes32
            'rawSs': decoded[3],            # list of bytes32
            'rawVs': decoded[4]             # bytes32
        }
    
    @staticmethod
    def _decode_v3_report_data(report_blob: bytes) -> Dict[str, Any]:
        """
        Decode v3 (Crypto Streams) report data from reportBlob.
        
        Internal method used by decode().
        """
        # V3 schema types (feedId is first field in reportBlob)
        types = [
            'bytes32',  # feedId
            'uint32',   # validFromTimestamp
            'uint32',   # observationsTimestamp
            'uint192',  # nativeFee
            'uint192',  # linkFee
            'uint32',   # expiresAt
            'int192',   # benchmarkPrice
            'int192',   # bid
            'int192',   # ask
        ]
        
        decoded = decode(types, report_blob)
        
        # Convert feedId bytes32 to hex string
        feed_id_hex = '0x' + decoded[0].hex()
        
        return {
            'feedId': feed_id_hex,
            'validFromTimestamp': decoded[1],
            'observationsTimestamp': decoded[2],
            'nativeFee': decoded[3],
            'linkFee': decoded[4],
            'expiresAt': decoded[5],
            'benchmarkPrice': decoded[6],
            'bid': decoded[7],
            'ask': decoded[8],
        }
    
    def decode(self, schema_version: Optional[int] = None) -> Dict[str, Any]:
        """
        Decode the full report from hex format.
        
        This method:
        1. Decodes the outer report structure (reportContext, reportBlob, signatures)
        2. Determines or uses the provided schema version
        3. Decodes the reportBlob based on the schema version
        
        Args:
            schema_version: Optional schema version (if not provided, will be determined from feed_id)
            
        Returns:
            Dictionary containing:
            - reportContext: tuple of 3 bytes32 values
            - reportBlob: bytes (raw blob)
            - rawRs, rawSs, rawVs: signature components
            - data: decoded report data (schema version dependent)
            - schemaVersion: the schema version used
            
        Raises:
            ValueError: If schema version cannot be determined or is unsupported
            Exception: If decoding fails
        """
        # Determine schema version
        if schema_version is None:
            schema_version = self.get_schema_version(self.feed_id)
        
        # Decode outer structure
        report_structure = self._decode_report_structure(self.full_report)
        
        # Decode reportBlob based on schema version
        if schema_version == 3:
            report_data = self._decode_v3_report_data(report_structure['reportBlob'])
        else:
            raise ValueError(f"Schema version {schema_version} is not yet supported. Currently supported: v3")
        
        return {
            **report_structure,
            'data': report_data,
            'schemaVersion': schema_version
        }
    
    @staticmethod
    def convert_fixed_point_to_decimal(value: int, decimals: int = 18) -> float:
        """
        Convert a fixed-point integer value to a decimal float.
        
        Chainlink Data Streams prices are typically stored as fixed-point integers
        with 18 decimal places (wei format, similar to Ethereum).
        
        Args:
            value: Fixed-point integer value
            decimals: Number of decimal places (default: 18)
            
        Returns:
            Decimal float value
        """
        return float(value) / (10 ** decimals)
    
    def get_decoded_prices(self, decimals: int = 18) -> Dict[str, Any]:
        """
        Extract and convert price fields from this report to decimal format.
        
        Args:
            decimals: Number of decimal places for fixed-point conversion (default: 18)
            
        Returns:
            Dictionary with decimal price values and timestamp:
            - observationsTimestamp: int (Unix timestamp)
            - benchmarkPrice: float
            - bid: float
            - ask: float
            - midPrice: float (average of bid and ask)
            
        Raises:
            ValueError: If report is not v3 schema or data is missing
        """
        decoded = self.decode()
        
        if decoded.get('schemaVersion') != 3:
            raise ValueError("get_decoded_prices only supports v3 schema reports")
        
        data = decoded.get('data', {})
        
        observations_timestamp = data.get('observationsTimestamp', 0)
        benchmark_price = self.convert_fixed_point_to_decimal(data.get('benchmarkPrice', 0), decimals)
        bid = self.convert_fixed_point_to_decimal(data.get('bid', 0), decimals)
        ask = self.convert_fixed_point_to_decimal(data.get('ask', 0), decimals)
        mid_price = (bid + ask) / 2.0
        
        return {
            'observationsTimestamp': observations_timestamp,
            'benchmarkPrice': benchmark_price,
            'bid': bid,
            'ask': ask,
            'midPrice': mid_price,
        }


class ReportPage:
    """
    Paginated report response.
    
    Attributes:
        reports: List of ReportResponse objects
        next_page_timestamp: Timestamp to use for next page (0 if no more pages)
    """
    
    def __init__(self, reports: List[ReportResponse], next_page_timestamp: int = 0):
        self.reports = reports
        self.next_page_timestamp = next_page_timestamp

