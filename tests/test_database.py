"""Tests for database module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from database.database import create_tables


@pytest.mark.asyncio
async def test_create_tables():
    """Test create_tables function."""
    mock_metadata = MagicMock()
    mock_create_all = AsyncMock()
    mock_metadata.create_all = mock_create_all

    mock_conn = MagicMock()
    mock_conn.run_sync = MagicMock(side_effect=lambda fn, *args: fn(mock_metadata, *args))

    mock_engine = MagicMock()
    mock_engine.begin = MagicMock()
    mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("database.database.engine", mock_engine):
        with patch("database.database.Base.metadata", mock_metadata):
            await create_tables()

    mock_create_all.assert_called_once()


@pytest.mark.asyncio
async def test_create_tables_creates_all_tables():
    """Test that create_tables creates all tables."""
    mock_metadata = MagicMock()
    mock_create_all = AsyncMock()
    mock_metadata.create_all = mock_create_all

    mock_conn = MagicMock()
    mock_conn.run_sync = MagicMock(side_effect=lambda fn, *args: fn(mock_metadata, *args))

    mock_engine = MagicMock()
    mock_engine.begin = MagicMock()
    mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("database.database.engine", mock_engine):
        with patch("database.database.Base.metadata", mock_metadata):
            await create_tables()

    mock_create_all.assert_called_once()
