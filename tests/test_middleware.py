"""Tests for middlewares module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from middlewares.middleware import DataBaseSessionMiddleware


@pytest.fixture
def mock_handler():
    """Create a mock handler."""
    return AsyncMock()


@pytest.fixture
def mock_event():
    """Create a mock event."""
    return MagicMock()


@pytest.mark.asyncio
async def test_middleware_call(mock_handler, mock_event):
    """Test middleware __call__ method."""
    middleware = DataBaseSessionMiddleware()
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    data = {}

    with patch("middlewares.middleware.AsyncSessionLocal", return_value=mock_session):
        result = await middleware(mock_handler, mock_event, data)

    mock_handler.assert_called_once_with(mock_event, data)
    assert "session" in data
    assert data["session"] == mock_session


@pytest.mark.asyncio
async def test_middleware_call_passes_result(mock_handler, mock_event):
    """Test middleware passes handler result."""
    middleware = DataBaseSessionMiddleware()
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    expected_result = {"status": "ok"}
    mock_handler.return_value = expected_result

    data = {}

    with patch("middlewares.middleware.AsyncSessionLocal", return_value=mock_session):
        result = await middleware(mock_handler, mock_event, data)

    assert result == expected_result


@pytest.mark.asyncio
async def test_middleware_session_cleanup(mock_handler, mock_event):
    """Test middleware cleans up session properly."""
    middleware = DataBaseSessionMiddleware()
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    data = {}

    with patch("middlewares.middleware.AsyncSessionLocal", return_value=mock_session):
        await middleware(mock_handler, mock_event, data)

    mock_session.__aexit__.assert_called()
