import pytest
import json
from unittest.mock import Mock, patch
from app.utils import (open_websocket_connection, queue_prompt, get_image,
                       upload_image, get_history, track_progress, generate_image,
                       generate_image_to_image)

@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['COMFYUI_URL'] = 'http://localhost:8188'
    return app

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

def test_open_websocket_connection(app, mock_websocket):
    with app.app_context():
        ws, server_address, client_id = open_websocket_connection()
        assert ws == mock_websocket
        assert server_address == "http://localhost:8188"
        assert client_id is not None

def test_queue_prompt(app, mock_requests):
    with app.app_context():
        mock_requests.post.return_value.json.return_value = {"prompt_id": "test_id"}
        result = queue_prompt({"test": "prompt"}, "client_id", "server_address")
        assert result == "test_id"

def test_get_image(app, mock_requests):
    with app.app_context():
        mock_requests.get.return_value.content = b"image_data"
        result = get_image("filename", "subfolder", "folder_type", "server_address")
        assert result == b"image_data"

def test_upload_image(app, mock_requests, tmp_path):
    with app.app_context():
        d = tmp_path / "sub"
        d.mkdir()
        p = d / "test.jpg"
        p.write_bytes(b"test image content")

        mock_requests.post.return_value.content = b"upload_response"
        result = upload_image(str(p), "test.jpg", "server_address")
        assert result == b"upload_response"

def test_get_history(app, mock_requests):
    with app.app_context():
        mock_requests.get.return_value.json.return_value = {"history": "data"}
        result = get_history("prompt_id", "server_address")
        assert result == {"history": "data"}

def test_track_progress(mock_websocket):
    mock_websocket.recv.side_effect = [
        json.dumps({"type": "progress", "data": {"value": 5, "max": 10}}),
        json.dumps({"type": "executing", "data": {"node": "1", "prompt_id": "test_id"}}),
        json.dumps({"type": "executing", "data": {"node": None, "prompt_id": "test_id"}})
    ]
    progress_generator = track_progress({"1": {}}, mock_websocket, "test_id")
    progress = list(progress_generator)
    assert len(progress) == 2
    assert "Progress: Step 5 of 10" in progress[0]
    assert "Progress: 1/1 tasks done" in progress[1]

@pytest.mark.parametrize("workflow,positive_prompt,negative_prompt", [
    ('{"3": {"class_type": "KSampler", "inputs": {"positive": ["6"], "negative": ["7"]}}, "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}}, "5": {"class_type": "EmptyLatentImage", "inputs": {}}, "6": {"class_type": "CLIPTextEncode", "inputs": {}}, "7": {"class_type": "CLIPTextEncode", "inputs": {}}}', "test positive", ""),
    ('{"3": {"class_type": "KSampler", "inputs": {"positive": ["6"], "negative": ["7"]}}, "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}}, "5": {"class_type": "EmptyLatentImage", "inputs": {}}, "6": {"class_type": "CLIPTextEncode", "inputs": {}}, "7": {"class_type": "CLIPTextEncode", "inputs": {}}}', "test positive", "test negative"),
])
def test_generate_image(workflow, positive_prompt, negative_prompt, mock_websocket, mock_requests, app):
    with app.app_context():
        mock_websocket.recv.side_effect = [
            json.dumps({"type": "executing", "data": {"node": None, "prompt_id": "test_id"}})
        ]
        mock_requests.post.return_value.json.return_value = {"prompt_id": "test_id"}
        mock_requests.get.return_value.json.return_value = {
            "test_id": {
                "outputs": {
                    "1": {
                        "images": [
                            {"filename": "test.png", "subfolder": "test", "type": "output"}
                        ]
                    }
                }
            }
        }
        mock_requests.get.return_value.content = b"image_data"

        result = generate_image(workflow, positive_prompt, negative_prompt)

        # Check for "Prompt queued" message
        progress = next(result)
        assert "Prompt queued with ID: test_id" in progress

        # Check for progress message
        progress = next(result)
        assert "Progress: 1/1 tasks done" in progress

        # Check for generated images
        images = next(result)
        assert len(images) == 1
        assert images[0]["file_name"] == "test.png"
        assert images[0]["image_data"] == b"image_data"

def test_generate_image_to_image(mock_websocket, mock_requests, tmp_path, app):
    with app.app_context():
        d = tmp_path / "sub"
        d.mkdir()
        p = d / "test.jpg"
        p.write_bytes(b"test image content")

        mock_websocket.recv.side_effect = [
            json.dumps({"type": "executing", "data": {"node": None, "prompt_id": "test_id"}})
        ]
        mock_requests.post.return_value.json.return_value = {"prompt_id": "test_id"}
        mock_requests.get.return_value.json.return_value = {
            "test_id": {
                "outputs": {
                    "1": {
                        "images": [
                            {"filename": "test_output.png", "subfolder": "test", "type": "output"}
                        ]
                    }
                }
            }
        }
        mock_requests.get.return_value.content = b"image_data"

        workflow = '{"3": {"class_type": "KSampler", "inputs": {"positive": ["6"], "negative": ["7"]}}, "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}}, "5": {"class_type": "LoadImage", "inputs": {}}, "6": {"class_type": "CLIPTextEncode", "inputs": {}}, "7": {"class_type": "CLIPTextEncode", "inputs": {}}}'
        result = generate_image_to_image(workflow, str(p), "test positive", "test negative")

        # Check for "Prompt queued" message
        progress = next(result)
        assert "Prompt queued with ID: test_id" in progress

        # Check for progress message
        progress = next(result)
        assert "Progress: 1/1 tasks done" in progress

        # Check for generated images
        images = next(result)
        assert len(images) == 1
        assert images[0]["file_name"] == "test_output.png"
        assert images[0]["image_data"] == b"image_data"