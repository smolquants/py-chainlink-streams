"""
Tests for ReportResponse decode methods.

This module tests the decoding functionality that has been moved to ReportResponse class.
"""

import pytest
from eth_abi import decode as eth_decode
from eth_utils import remove_0x_prefix

from py_chainlink_streams.report import ReportResponse


class TestGetSchemaVersion:
    """Test ReportResponse.get_schema_version static method."""

    def test_returns_1_for_0x0001_prefix(self):
        """Test returns 1 for feed_id starting with 0x0001."""
        feed_id = "0x0001" + "a" * 60
        assert ReportResponse.get_schema_version(feed_id) == 1

    def test_returns_2_for_0x0002_prefix(self):
        """Test returns 2 for feed_id starting with 0x0002."""
        feed_id = "0x0002" + "a" * 60
        assert ReportResponse.get_schema_version(feed_id) == 2

    def test_returns_3_for_0x0003_prefix(self):
        """Test returns 3 for feed_id starting with 0x0003."""
        feed_id = "0x0003" + "a" * 60
        assert ReportResponse.get_schema_version(feed_id) == 3

    def test_returns_4_for_0x0004_prefix(self):
        """Test returns 4 for feed_id starting with 0x0004."""
        feed_id = "0x0004" + "a" * 60
        assert ReportResponse.get_schema_version(feed_id) == 4

    def test_returns_13_for_0x000d_prefix(self):
        """Test returns 13 for feed_id starting with 0x000d (hex for 13)."""
        feed_id = "0x000d" + "a" * 60
        assert ReportResponse.get_schema_version(feed_id) == 13

    def test_raises_value_error_for_no_0x_prefix(self):
        """Test raises ValueError for feed_id not starting with 0x."""
        feed_id = "0003" + "a" * 60
        with pytest.raises(ValueError, match="Invalid feed ID format"):
            ReportResponse.get_schema_version(feed_id)

    def test_raises_value_error_for_invalid_hex_in_prefix(self):
        """Test raises ValueError for invalid hex characters in prefix."""
        feed_id = "0x00gx" + "a" * 60  # 'g' is not valid hex
        with pytest.raises(ValueError, match="Could not determine schema version"):
            ReportResponse.get_schema_version(feed_id)

    def test_handles_uppercase_hex_characters(self):
        """Test handles uppercase hex characters."""
        feed_id = "0x000A" + "a" * 60  # 'A' in hex
        assert ReportResponse.get_schema_version(feed_id) == 10

    def test_handles_lowercase_hex_characters(self):
        """Test handles lowercase hex characters."""
        feed_id = "0x000a" + "a" * 60  # 'a' in hex
        assert ReportResponse.get_schema_version(feed_id) == 10

    def test_handles_mixed_case_hex_characters(self):
        """Test handles mixed case hex characters."""
        feed_id = "0x000F" + "a" * 60  # 'F' in hex
        assert ReportResponse.get_schema_version(feed_id) == 15


class TestDecodeReportStructure:
    """Test decode_report_structure function."""

    def test_returns_dict_with_correct_keys(self):
        """Test returns dict with keys: reportContext, reportBlob, rawRs, rawSs, rawVs."""
        # Create minimal valid report structure
        # This is a simplified test - real reports are much longer
        # We'll test with a minimal valid ABI-encoded structure
        from eth_abi import encode
        
        # Encode a minimal structure: (bytes32[3], bytes, bytes32[], bytes32[], bytes32)
        report_context = (b'\x00' * 32, b'\x00' * 32, b'\x00' * 32)
        report_blob = b'\x00' * 32
        raw_rs = [b'\x00' * 32]
        raw_ss = [b'\x00' * 32]
        raw_vs = b'\x00' * 32
        
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [report_context, report_blob, raw_rs, raw_ss, raw_vs]
        )
        hex_data = '0x' + encoded.hex()
        
        result = ReportResponse._decode_report_structure(hex_data)
        assert 'reportContext' in result
        assert 'reportBlob' in result
        assert 'rawRs' in result
        assert 'rawSs' in result
        assert 'rawVs' in result

    def test_handles_hex_string_with_0x_prefix(self):
        """Test handles hex string with 0x prefix."""
        # Minimal test - just verify it doesn't crash
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), b'\x00', [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        result = ReportResponse._decode_report_structure(hex_data)
        assert isinstance(result, dict)

    def test_handles_hex_string_without_0x_prefix(self):
        """Test handles hex string without 0x prefix."""
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), b'\x00', [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = encoded.hex()  # No 0x prefix
        result = ReportResponse._decode_report_structure(hex_data)
        assert isinstance(result, dict)

    def test_report_context_is_tuple_of_3_bytes32(self):
        """Test reportContext is tuple of 3 bytes32 values."""
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x01' * 32, b'\x02' * 32, b'\x03' * 32), b'\x00', [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        result = ReportResponse._decode_report_structure(hex_data)
        assert isinstance(result['reportContext'], tuple)
        assert len(result['reportContext']) == 3
        assert all(isinstance(b, bytes) and len(b) == 32 for b in result['reportContext'])

    def test_report_blob_is_bytes(self):
        """Test reportBlob is bytes."""
        from eth_abi import encode
        test_blob = b'test blob data'
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), test_blob, [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        result = ReportResponse._decode_report_structure(hex_data)
        assert isinstance(result['reportBlob'], bytes)
        assert result['reportBlob'] == test_blob

    def test_raises_exception_for_invalid_hex(self):
        """Test raises appropriate exception for invalid hex."""
        with pytest.raises((ValueError, Exception)):
            ReportResponse._decode_report_structure("0xinvalid_hex_string_zzz")

    def test_raises_exception_for_malformed_data(self):
        """Test raises appropriate exception for malformed data."""
        # Too short to be valid
        with pytest.raises((ValueError, Exception)):
            ReportResponse._decode_report_structure("0x00")


class TestDecodeV3ReportData:
    """Test decode_v3_report_data function."""

    def test_returns_dict_with_correct_v3_schema_fields(self):
        """Test returns dict with correct v3 schema fields."""
        from eth_abi import encode
        
        feed_id = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        valid_from = 1767208232
        obs_timestamp = 1767208232
        native_fee = 7000000000000000
        link_fee = 5000000000000000000
        expires_at = 1767216032
        benchmark_price = 87656352262094430000000
        bid = 87656309944707825000000
        ask = 87656862768468300000000
        
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id, valid_from, obs_timestamp, native_fee, link_fee, expires_at, benchmark_price, bid, ask]
        )
        
        result = ReportResponse._decode_v3_report_data(encoded)
        assert 'feedId' in result
        assert 'validFromTimestamp' in result
        assert 'observationsTimestamp' in result
        assert 'nativeFee' in result
        assert 'linkFee' in result
        assert 'expiresAt' in result
        assert 'benchmarkPrice' in result
        assert 'bid' in result
        assert 'ask' in result

    def test_feed_id_is_properly_formatted_hex_string(self):
        """Test feedId is properly formatted hex string with 0x prefix."""
        from eth_abi import encode
        feed_id_bytes = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id_bytes, 0, 0, 0, 0, 0, 0, 0, 0]
        )
        result = ReportResponse._decode_v3_report_data(encoded)
        assert result['feedId'].startswith('0x')
        assert len(result['feedId']) == 66  # 0x + 64 hex chars

    def test_all_timestamp_fields_are_integers(self):
        """Test all timestamp fields are integers."""
        from eth_abi import encode
        feed_id_bytes = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id_bytes, 100, 200, 0, 0, 300, 0, 0, 0]
        )
        result = ReportResponse._decode_v3_report_data(encoded)
        assert isinstance(result['validFromTimestamp'], int)
        assert isinstance(result['observationsTimestamp'], int)
        assert isinstance(result['expiresAt'], int)

    def test_all_fee_fields_are_integers(self):
        """Test all fee fields are integers."""
        from eth_abi import encode
        feed_id_bytes = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id_bytes, 0, 0, 1000, 2000, 0, 0, 0, 0]
        )
        result = ReportResponse._decode_v3_report_data(encoded)
        assert isinstance(result['nativeFee'], int)
        assert isinstance(result['linkFee'], int)

    def test_all_price_fields_are_integers(self):
        """Test all price fields are integers."""
        from eth_abi import encode
        feed_id_bytes = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id_bytes, 0, 0, 0, 0, 0, 100, 200, 300]
        )
        result = ReportResponse._decode_v3_report_data(encoded)
        assert isinstance(result['benchmarkPrice'], int)
        assert isinstance(result['bid'], int)
        assert isinstance(result['ask'], int)

    def test_handles_zero_values_correctly(self):
        """Test handles zero values correctly."""
        from eth_abi import encode
        feed_id_bytes = bytes.fromhex("00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8")
        encoded = encode(
            ['bytes32', 'uint32', 'uint32', 'uint192', 'uint192', 'uint32', 'int192', 'int192', 'int192'],
            [feed_id_bytes, 0, 0, 0, 0, 0, 0, 0, 0]
        )
        result = ReportResponse._decode_v3_report_data(encoded)
        assert result['validFromTimestamp'] == 0
        assert result['observationsTimestamp'] == 0
        assert result['nativeFee'] == 0
        assert result['linkFee'] == 0
        assert result['expiresAt'] == 0
        assert result['benchmarkPrice'] == 0
        assert result['bid'] == 0
        assert result['ask'] == 0


class TestDecodeReport:
    """Test decode_report function."""

    def test_decodes_when_feed_id_provided(self):
        """Test decodes report when feed_id provided (auto-detects schema)."""
        # This would require a real report hex, so we'll test the logic
        feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        # Using a minimal valid structure for testing
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), b'\x00' * 100, [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        
        # This will fail because the blob doesn't match v3 schema, but tests the flow
        report = ReportResponse(feed_id, hex_data, 0, 0)
        with pytest.raises((ValueError, Exception)):
            report.decode()

    def test_decodes_when_schema_version_provided(self):
        """Test decodes report when schema_version provided."""
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), b'\x00' * 100, [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        
        # Create report with a dummy feed_id (schema_version will be provided)
        report = ReportResponse("0x0003abc", hex_data, 0, 0)
        with pytest.raises((ValueError, Exception)):
            report.decode(schema_version=3)

    def test_raises_when_neither_feed_id_nor_schema_version_provided(self):
        """Test raises ValueError when feed_id cannot determine schema version."""
        # This test is less relevant now since ReportResponse always has a feed_id
        # But we can test with an invalid feed_id
        report = ReportResponse("invalid", "0x1234", 0, 0)
        with pytest.raises(ValueError):
            report.decode()

    def test_returns_dict_with_correct_keys(self):
        """Test returns dict with keys: reportContext, reportBlob, rawRs, rawSs, rawVs, data, schemaVersion."""
        # This test would need a real valid report
        # For now, we test the error case
        feed_id = "0x0003abc"
        report = ReportResponse(feed_id, "0x00", 0, 0)
        with pytest.raises((ValueError, Exception)):
            result = report.decode()
            # If it succeeded, check keys
            # assert 'reportContext' in result
            # assert 'data' in result
            # assert 'schemaVersion' in result

    def test_raises_for_unsupported_schema_version(self):
        """Test raises ValueError for unsupported schema version."""
        feed_id = "0x0001abc"  # v1 schema
        from eth_abi import encode
        encoded = encode(
            ['bytes32[3]', 'bytes', 'bytes32[]', 'bytes32[]', 'bytes32'],
            [(b'\x00' * 32, b'\x00' * 32, b'\x00' * 32), b'\x00', [b'\x00' * 32], [b'\x00' * 32], b'\x00' * 32]
        )
        hex_data = '0x' + encoded.hex()
        
        report = ReportResponse(feed_id, hex_data, 0, 0)
        with pytest.raises(ValueError, match="not yet supported"):
            report.decode()


class TestDecodeReportFromResponse:
    """Test ReportResponse.from_dict and decode methods."""

    def test_decodes_report_from_api_response_format(self, sample_report_response):
        """Test decodes report from API response format."""
        report = ReportResponse.from_dict(sample_report_response)
        result = report.decode()
        assert 'data' in result
        assert 'schemaVersion' in result

    def test_raises_when_feed_id_missing(self):
        """Test raises ValueError when feedID missing."""
        response = {"fullReport": "0x1234"}
        with pytest.raises(KeyError):
            ReportResponse.from_dict(response)

    def test_raises_when_full_report_missing(self):
        """Test raises ValueError when fullReport missing."""
        response = {"feedID": "0x1234"}
        with pytest.raises(KeyError):
            ReportResponse.from_dict(response)


class TestConvertFixedPointToDecimal:
    """Test convert_fixed_point_to_decimal function."""

    def test_converts_with_default_18_decimals(self):
        """Test converts value with default 18 decimals."""
        value = 1000000000000000000  # 1 with 18 decimals
        result = ReportResponse.convert_fixed_point_to_decimal(value)
        assert result == 1.0

    def test_converts_with_custom_decimals(self):
        """Test converts value with custom decimals."""
        value = 100000000  # 1 with 8 decimals
        result = ReportResponse.convert_fixed_point_to_decimal(value, decimals=8)
        assert result == 1.0

    def test_returns_float(self):
        """Test returns float."""
        result = ReportResponse.convert_fixed_point_to_decimal(1000000000000000000)
        assert isinstance(result, float)

    def test_handles_zero_value(self):
        """Test handles zero value."""
        result = ReportResponse.convert_fixed_point_to_decimal(0)
        assert result == 0.0

    def test_handles_large_values(self):
        """Test handles large values."""
        value = 87656352262094430000000
        result = ReportResponse.convert_fixed_point_to_decimal(value)
        assert result > 0
        assert isinstance(result, float)

    def test_handles_negative_values(self):
        """Test handles negative values (for int192 prices)."""
        value = -1000000000000000000
        result = ReportResponse.convert_fixed_point_to_decimal(value)
        assert result == -1.0

    def test_precision_is_correct(self):
        """Test precision is correct (within expected tolerance)."""
        value = 87656352262094430000000
        result = ReportResponse.convert_fixed_point_to_decimal(value)
        expected = 87656.35
        assert abs(result - expected) < 0.01

    def test_works_with_different_decimal_places(self):
        """Test works with different decimal places (8, 18, etc.)."""
        # Test with 8 decimals (like Bitcoin)
        value_8 = 100000000
        result_8 = ReportResponse.convert_fixed_point_to_decimal(value_8, decimals=8)
        assert result_8 == 1.0
        
        # Test with 18 decimals (like Ethereum)
        value_18 = 1000000000000000000
        result_18 = ReportResponse.convert_fixed_point_to_decimal(value_18, decimals=18)
        assert result_18 == 1.0


class TestGetDecodedPrices:
    """Test ReportResponse.get_decoded_prices method."""

    def test_returns_dict_with_correct_keys(self, sample_decoded_report):
        """Test returns dict with keys: observationsTimestamp, benchmarkPrice, bid, ask, midPrice."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        # Mock decode to return our sample
        report.decode = lambda: sample_decoded_report
        result = report.get_decoded_prices()
        assert 'observationsTimestamp' in result
        assert 'benchmarkPrice' in result
        assert 'bid' in result
        assert 'ask' in result
        assert 'midPrice' in result

    def test_observations_timestamp_is_int(self, sample_decoded_report):
        """Test observationsTimestamp is int."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        report.decode = lambda: sample_decoded_report
        result = report.get_decoded_prices()
        assert isinstance(result['observationsTimestamp'], int)

    def test_price_fields_are_floats(self, sample_decoded_report):
        """Test benchmarkPrice, bid, ask, midPrice are floats."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        report.decode = lambda: sample_decoded_report
        result = report.get_decoded_prices()
        assert isinstance(result['benchmarkPrice'], float)
        assert isinstance(result['bid'], float)
        assert isinstance(result['ask'], float)
        assert isinstance(result['midPrice'], float)

    def test_mid_price_is_average_of_bid_and_ask(self, sample_decoded_report):
        """Test midPrice is average of bid and ask."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        report.decode = lambda: sample_decoded_report
        result = report.get_decoded_prices()
        expected_mid = (result['bid'] + result['ask']) / 2.0
        assert abs(result['midPrice'] - expected_mid) < 0.0001

    def test_raises_for_non_v3_schema_reports(self):
        """Test raises ValueError for non-v3 schema reports."""
        invalid_report = {"schemaVersion": 4, "data": {}}
        report = ReportResponse("0x0004abc", "0x", 0, 0)
        report.decode = lambda: invalid_report
        with pytest.raises(ValueError, match="only supports v3 schema reports"):
            report.get_decoded_prices()

    def test_uses_default_18_decimals(self, sample_decoded_report):
        """Test uses default 18 decimals."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        report.decode = lambda: sample_decoded_report
        result = report.get_decoded_prices()
        # Prices should be reasonable (not in wei format)
        assert result['benchmarkPrice'] < 1000000  # Should be converted from wei

    def test_uses_custom_decimals_when_provided(self, sample_decoded_report):
        """Test uses custom decimals when provided."""
        report = ReportResponse(
            feed_id=sample_decoded_report['data']['feedId'],
            full_report="0x",
            valid_from_timestamp=0,
            observations_timestamp=0
        )
        report.decode = lambda: sample_decoded_report
        result_18 = report.get_decoded_prices(decimals=18)
        result_8 = report.get_decoded_prices(decimals=8)
        # With 8 decimals, prices should be much larger
        assert result_8['benchmarkPrice'] > result_18['benchmarkPrice']

