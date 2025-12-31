"""
Chainlink Data Streams report decoding functionality.

This module provides functions to decode hex-encoded reports from Chainlink Data Streams
into structured Python dictionaries.
"""

from typing import Dict, Optional, Any
from eth_abi import decode
from eth_utils import remove_0x_prefix


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


def decode_report_structure(full_report_hex: str) -> Dict[str, Any]:
    """
    Decode the outer report structure from hex-encoded fullReport.
    
    The report structure is:
    - reportContext: bytes32[3] (3 * 32 bytes)
    - reportBlob: bytes (variable length, contains the actual data)
    - rawRs: bytes32[] (array of 32-byte signature components)
    - rawSs: bytes32[] (array of 32-byte signature components)
    - rawVs: bytes32 (32-byte signature component)
    
    Args:
        full_report_hex: Hex-encoded full report string (with or without '0x' prefix)
        
    Returns:
        Dictionary with keys: reportContext, reportBlob, rawRs, rawSs, rawVs
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


def decode_v3_report_data(report_blob: bytes) -> Dict[str, Any]:
    """
    Decode v3 (Crypto Streams) report data from reportBlob.
    
    V3 schema structure (based on Chainlink Data Streams v3 schema):
    - feedId: bytes32 (feed identifier)
    - validFromTimestamp: uint32
    - observationsTimestamp: uint32
    - nativeFee: uint192
    - linkFee: uint192
    - expiresAt: uint32
    - benchmarkPrice: int192
    - bid: int192
    - ask: int192
    
    Args:
        report_blob: The reportBlob bytes from decode_report_structure()
        
    Returns:
        Dictionary with decoded v3 report data fields
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


def decode_report(full_report_hex: str, feed_id: Optional[str] = None, schema_version: Optional[int] = None) -> Dict[str, Any]:
    """
    Decode a full Chainlink Data Streams report from hex format.
    
    This function:
    1. Decodes the outer report structure (reportContext, reportBlob, signatures)
    2. Determines or uses the provided schema version
    3. Decodes the reportBlob based on the schema version
    
    Args:
        full_report_hex: Hex-encoded full report string
        feed_id: Optional feed ID to determine schema version automatically
        schema_version: Optional schema version (if not provided and feed_id is provided, will be determined from feed_id)
        
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
        if feed_id is None:
            raise ValueError("Either feed_id or schema_version must be provided")
        schema_version = get_schema_version(feed_id)
    
    # Decode outer structure
    report_structure = decode_report_structure(full_report_hex)
    
    # Decode reportBlob based on schema version
    if schema_version == 3:
        report_data = decode_v3_report_data(report_structure['reportBlob'])
    else:
        raise ValueError(f"Schema version {schema_version} is not yet supported. Currently supported: v3")
    
    return {
        **report_structure,
        'data': report_data,
        'schemaVersion': schema_version
    }


def decode_report_from_response(report_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to decode a report from the API response format.
    
    Args:
        report_response: Dictionary from API response with keys:
                        - feedID
                        - validFromTimestamp
                        - observationsTimestamp
                        - fullReport
                        
    Returns:
        Decoded report dictionary (same format as decode_report)
    """
    feed_id = report_response.get('feedID')
    full_report = report_response.get('fullReport')
    
    if not feed_id or not full_report:
        raise ValueError("report_response must contain 'feedID' and 'fullReport' keys")
    
    return decode_report(full_report, feed_id=feed_id)


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


def get_decoded_prices(decoded_report: Dict[str, Any], decimals: int = 18) -> Dict[str, Any]:
    """
    Extract and convert price fields from a decoded v3 report to decimal format.
    
    Args:
        decoded_report: Decoded report dictionary from decode_report()
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
    if decoded_report.get('schemaVersion') != 3:
        raise ValueError("get_decoded_prices only supports v3 schema reports")
    
    data = decoded_report.get('data', {})
    
    observations_timestamp = data.get('observationsTimestamp', 0)
    benchmark_price = convert_fixed_point_to_decimal(data.get('benchmarkPrice', 0), decimals)
    bid = convert_fixed_point_to_decimal(data.get('bid', 0), decimals)
    ask = convert_fixed_point_to_decimal(data.get('ask', 0), decimals)
    mid_price = (bid + ask) / 2.0
    
    return {
        'observationsTimestamp': observations_timestamp,
        'benchmarkPrice': benchmark_price,
        'bid': bid,
        'ask': ask,
        'midPrice': mid_price,
    }

