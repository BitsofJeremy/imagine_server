from flask import Blueprint, render_template, request, jsonify
from app.utils import connect_to_comfyui, generate_image, generate_image_to_image

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        # Handle form submission and image generation
        pass
    return render_template('generate.html')

@main.route('/generate_image_to_image', methods=['GET', 'POST'])
def generate_image_to_image():
    if request.method == 'POST':
        # Handle form submission and image-to-image generation
        pass
    return render_template('generate.html', image_to_image=True)

@main.route('/result')
def result():
    # Display the generated image
    return render_template('result.html')