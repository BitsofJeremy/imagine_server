import pytest
from app.forms import ImageGenerationForm, ImageToImageForm
from werkzeug.datastructures import FileStorage

@pytest.fixture
def app():
    from app import create_app
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    return app

def test_image_generation_form_valid(app):
    with app.test_request_context():
        form = ImageGenerationForm(data={
            'positive_prompt': 'test prompt',
            'negative_prompt': 'test negative',
            'steps': 20,
            'cfg': 7.5,
            'sampler_name': 'euler',
            'scheduler': 'normal',
            'denoise': 1,
            'ckpt_name': 'SD15/cyberrealistic_classicV31.safetensors',
            'width': 512,
            'height': 512,
            'batch_size': 1
        })
        assert form.validate() == True, form.errors

def test_image_generation_form_invalid(app):
    with app.test_request_context():
        form = ImageGenerationForm(data={
            'positive_prompt': '',  # This should be required
            'steps': 200,  # This should be out of range
        })
        assert form.validate() == False
        assert 'positive_prompt' in form.errors
        assert 'steps' in form.errors

def test_image_to_image_form_valid(app, tmp_path):
    with app.test_request_context():
        d = tmp_path / "sub"
        d.mkdir()
        p = d / "test.jpg"
        p.write_bytes(b"test image content")

        with open(p, 'rb') as f:
            file = FileStorage(f)
            form = ImageToImageForm(data={
                'positive_prompt': 'test prompt',
                'negative_prompt': 'test negative',
                'seed': '-1',
                'steps': 20,
                'cfg': 7.5,
                'sampler_name': 'euler_ancestral',
                'scheduler': 'karras',
                'denoise': 0.8,
                'ckpt_name': 'SDXL/juggernautXL_version5.safetensors'
            }, files={'input_image': file})
            assert form.validate() == True, form.errors

def test_image_to_image_form_invalid(app):
    with app.test_request_context():
        form = ImageToImageForm(data={
            'positive_prompt': '',  # This should be required
            'seed': 'not a number',  # This should be a number or -1
        })
        assert form.validate() == False
        assert 'positive_prompt' in form.errors
        assert 'input_image' in form.errors  # This should be required
        assert 'seed' in form.errors