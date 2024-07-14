import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from app.forms import ImageGenerationForm, ImageToImageForm
from app.utils import generate_image, generate_image_to_image
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/generate', methods=['GET', 'POST'])
def generate():
    form = ImageGenerationForm()
    if form.validate_on_submit():
        workflow_path = os.path.join(current_app.config['WORKFLOWS_DIR'], 'base_workflow.json')
        try:
            with open(workflow_path, 'r') as f:
                workflow = f.read()
        except FileNotFoundError:
            logger.error(f"Workflow file not found: {workflow_path}")
            return jsonify({'success': False, 'error': f"Workflow file not found: {workflow_path}"})

        try:
            image_generator = generate_image(
                workflow,
                form.positive_prompt.data,
                form.negative_prompt.data
            )

            generated_images = None
            for item in image_generator:
                if isinstance(item, str):
                    if item.startswith("Error:"):
                        logger.error(f"Error during image generation: {item}")
                        return jsonify({'success': False, 'error': item})
                    logger.info(f"Generation progress: {item}")
                    print(item)
                elif isinstance(item, list):
                    generated_images = item

            if generated_images and len(generated_images) > 0:
                filename = secure_filename(f"generated_{form.positive_prompt.data[:10]}.png")
                filepath = os.path.join(current_app.root_path, 'static', 'generated', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(generated_images[0]['image_data'])
                logger.info(f"Image generated successfully: {filename}")
                return jsonify({'success': True, 'filename': filename})
            else:
                logger.warning("No image data received from generate_image function")
                return jsonify({'success': False, 'error': 'No image data received'})
        except Exception as e:
            logger.exception("Unexpected error during image generation")
            return jsonify({'success': False, 'error': str(e)})

    return render_template('generate.html', form=form)


@main.route('/generate_image_to_image', methods=['GET', 'POST'])
def generate_image_to_image():
    form = ImageToImageForm()
    if form.validate_on_submit():
        workflow_path = os.path.join(current_app.config['WORKFLOWS_DIR'], 'basic_image_to_image.json')
        try:
            with open(workflow_path, 'r') as f:
                workflow = f.read()
        except FileNotFoundError:
            logger.error(f"Workflow file not found: {workflow_path}")
            return jsonify({'success': False, 'error': f"Workflow file not found: {workflow_path}"})

        input_image = form.input_image.data
        filename = secure_filename(input_image.filename)
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        input_image.save(filepath)

        try:
            result = generate_image_to_image(
                workflow,
                filepath,
                form.positive_prompt.data,
                form.negative_prompt.data
            )
            for progress in result:
                if isinstance(progress, str):
                    if progress.startswith("Error:"):
                        logger.error(f"Error during image-to-image generation: {progress}")
                        return jsonify({'success': False, 'error': progress})
                    logger.info(f"Generation progress: {progress}")
                    print(progress)
                elif isinstance(progress, list) and progress:
                    output_filename = secure_filename(f"generated_{form.positive_prompt.data[:10]}.png")
                    output_filepath = os.path.join(current_app.root_path, 'static', 'generated', output_filename)
                    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
                    with open(output_filepath, 'wb') as f:
                        f.write(progress[0]['image_data'])
                    logger.info(f"Image-to-image generated successfully: {output_filename}")
                    return jsonify({'success': True, 'filename': output_filename})

            logger.warning("No image generated")
            return jsonify({'success': False, 'error': 'No image generated'})
        except Exception as e:
            logger.exception("Unexpected error during image-to-image generation")
            return jsonify({'success': False, 'error': str(e)})

    return render_template('generate.html', form=form, image_to_image=True)


@main.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)


@main.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(current_app.root_path, 'static', 'generated', filename), as_attachment=True)