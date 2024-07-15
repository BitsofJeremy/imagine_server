import pytest
from flask import url_for
from unittest.mock import patch, Mock
import io

def test_index(client, app):
    with app.test_request_context():
        response = client.get(url_for('main.index'))
        assert response.status_code == 200
        assert b"Welcome to Imagine Server" in response.data

def test_generate_get(client, app):
    with app.test_request_context():
        response = client.get(url_for('main.generate'))
        assert response.status_code == 200
        assert b"Generate Image" in response.data

@patch('app.routes.generate_image')
def test_generate_post(mock_generate_image, client, app):
    mock_generate_image.return_value = iter([
        "Prompt queued with ID: test_id",
        "Progress: 1/1 tasks done",
        [{"image_data": b"test_image_data", "file_name": "test.png", "type": "output"}]
    ])

    with app.test_request_context():
        data = {
            'positive_prompt': 'test positive prompt',
            'negative_prompt': 'test negative prompt',
            'steps': 20,
            'cfg': 7.5,
            'sampler_name': 'euler',
            'scheduler': 'normal',
            'denoise': 1,
            'ckpt_name': 'SD15/cyberrealistic_classicV31.safetensors',
            'width': 512,
            'height': 512,
            'batch_size': 1
        }
        response = client.post(url_for('main.generate'), data=data)
        assert response.status_code == 200
        assert response.json['success'] == True
        assert 'filename' in response.json

def test_generate_image_to_image_get(client, app):
    with app.test_request_context():
        response = client.get(url_for('main.image_to_image_route'))
        assert response.status_code == 200
        assert b"Image to Image" in response.data

@patch('app.routes.generate_image_to_image')
def test_generate_image_to_image_post(mock_generate_image_to_image, client, app):
    mock_generate_image_to_image.return_value = iter([
        "Prompt queued with ID: test_id",
        "Progress: 1/1 tasks done",
        [{"image_data": b"test_image_data", "file_name": "test.png", "type": "output"}]
    ])

    with app.test_request_context():
        data = {
            'input_image': (io.BytesIO(b"abcdef"), 'test.jpg'),
            'positive_prompt': 'test positive prompt',
            'negative_prompt': 'test negative prompt',
            'seed': '-1',
            'steps': 20,
            'cfg': 7.5,
            'sampler_name': 'euler_ancestral',
            'scheduler': 'karras',
            'denoise': 0.8,
            'ckpt_name': 'SDXL/juggernautXL_version5.safetensors'
        }
        response = client.post(url_for('main.image_to_image_route'), data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert response.json['success'] == True
        assert 'filename' in response.json

def test_result(client, app):
    with app.test_request_context():
        response = client.get(url_for('main.result', filename='test.png'))
        assert response.status_code == 200
        assert b"Generated Image" in response.data

@patch('app.routes.send_file')
def test_download(mock_send_file, client, app):
    mock_send_file.return_value = 'mocked file'
    with app.test_request_context():
        response = client.get(url_for('main.download', filename='test.png'))
        assert response.status_code == 200
        mock_send_file.assert_called_once()