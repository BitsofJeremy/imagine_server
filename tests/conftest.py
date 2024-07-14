import pytest
from app import create_app
from app.utils import open_websocket_connection
from unittest.mock import Mock, patch

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "COMFYUI_URL": "http://localhost:8188"
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_websocket():
    with patch('app.utils.websocket.WebSocket') as mock_ws:
        mock_ws_instance = Mock()
        mock_ws.return_value = mock_ws_instance
        yield mock_ws_instance

@pytest.fixture
def mock_requests():
    with patch('app.utils.requests') as mock_req:
        yield mock_req