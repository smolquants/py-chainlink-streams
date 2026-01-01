"""
Tests for py_chainlink_streams.feed module.

This module tests the Feed class functionality.
"""

import pytest

from py_chainlink_streams.feed import Feed


class TestFeed:
    """Test Feed class."""

    def test_init_with_id_field(self):
        """Test Feed initialization with 'id' field."""
        data = {
            "id": "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8",
            "name": "BTC/USD"
        }
        feed = Feed(data)
        assert feed.id == "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        assert feed.name == "BTC/USD"

    def test_init_with_feedID_field(self):
        """Test Feed initialization with 'feedID' field (alternative)."""
        data = {
            "feedID": "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8",
            "name": "BTC/USD"
        }
        feed = Feed(data)
        assert feed.id == "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        assert feed.name == "BTC/USD"

    def test_init_without_name(self):
        """Test Feed initialization without name field."""
        data = {
            "id": "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        }
        feed = Feed(data)
        assert feed.id == "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        assert feed.name == ""

    def test_to_dict(self):
        """Test to_dict returns original data."""
        data = {
            "id": "0x123",
            "name": "Test Feed",
            "extra": "field"
        }
        feed = Feed(data)
        result = feed.to_dict()
        assert result == data
        assert result["id"] == "0x123"
        assert result["name"] == "Test Feed"
        assert result["extra"] == "field"

    def test_get_schema_version_static_method(self):
        """Test get_schema_version static method."""
        # Test v3 feed
        feed_id = "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        assert Feed.get_schema_version(feed_id) == 3

        # Test v1 feed
        feed_id_v1 = "0x0001" + "a" * 60
        assert Feed.get_schema_version(feed_id_v1) == 1

        # Test v2 feed
        feed_id_v2 = "0x0002" + "a" * 60
        assert Feed.get_schema_version(feed_id_v2) == 2

    def test_get_schema_version_raises_for_invalid_format(self):
        """Test get_schema_version raises ValueError for invalid feed ID format."""
        with pytest.raises(ValueError, match="Invalid feed ID format"):
            Feed.get_schema_version("invalid")

    def test_schema_version_instance_method(self):
        """Test schema_version instance method."""
        data = {
            "id": "0x00039d9e45394f473ab1f050a1b963e6b05351e52d71e507509ada0c95ed75b8"
        }
        feed = Feed(data)
        assert feed.schema_version() == 3

    def test_schema_version_with_different_versions(self):
        """Test schema_version with different schema versions."""
        # v1
        feed_v1 = Feed({"id": "0x0001" + "a" * 60})
        assert feed_v1.schema_version() == 1

        # v2
        feed_v2 = Feed({"id": "0x0002" + "a" * 60})
        assert feed_v2.schema_version() == 2

        # v4
        feed_v4 = Feed({"id": "0x0004" + "a" * 60})
        assert feed_v4.schema_version() == 4

