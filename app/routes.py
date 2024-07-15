import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app, send_file, abort
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
                form.negative_prompt.data,
                steps=form.steps.data,
                cfg=form.cfg.data,
                sampler_name=form.sampler_name.data,
                scheduler=form.scheduler.data,
                denoise=form.denoise.data,
                ckpt_name=form.ckpt_name.data,
                width=form.width.data,
                height=form.height.data,
                batch_size=form.batch_size.data
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

    return render_template('generate.html', form=form, image_to_image=False)


@main.route('/generate_image_to_image', methods=['GET', 'POST'])
def image_to_image_route():
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
            # Convert seed to integer, use -1 if it's not a valid integer
            seed = int(form.seed.data) if form.seed.data.isdigit() else -1
            image_generator = generate_image_to_image(
                workflow,
                filepath,
                form.positive_prompt.data,
                form.negative_prompt.data,
                seed=seed,
                steps=form.steps.data,
                cfg=form.cfg.data,
                sampler_name=form.sampler_name.data,
                scheduler=form.scheduler.data,
                denoise=form.denoise.data,
                ckpt_name=form.ckpt_name.data
            )

            generated_images = None
            for item in image_generator:
                if isinstance(item, str):
                    if item.startswith("Error:"):
                        logger.error(f"Error during image-to-image generation: {item}")
                        return jsonify({'success': False, 'error': item})
                    logger.info(f"Generation progress: {item}")
                    print(item)
                elif isinstance(item, list):
                    generated_images = item

            if generated_images and len(generated_images) > 0:
                output_filename = secure_filename(f"generated_i2i_{form.positive_prompt.data[:10]}.png")
                output_filepath = os.path.join(current_app.root_path, 'static', 'generated', output_filename)
                os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
                with open(output_filepath, 'wb') as f:
                    f.write(generated_images[0]['image_data'])
                logger.info(f"Image-to-image generated successfully: {output_filename}")
                return jsonify({'success': True, 'filename': output_filename})
            else:
                logger.warning("No image data received from generate_image_to_image function")
                return jsonify({'success': False, 'error': 'No image data received'})
        except Exception as e:
            logger.exception("Unexpected error during image-to-image generation")
            return jsonify({'success': False, 'error': str(e)})

    return render_template('generate.html', form=form, image_to_image=True)


@main.route('/saves')
def saves():
    generated_dir = os.path.join(current_app.root_path, 'static', 'generated')
    text_to_image = []
    image_to_image = []

    for filename in os.listdir(generated_dir):
        if filename.startswith('generated_'):
            file_path = os.path.join(generated_dir, filename)
            file_size = os.path.getsize(file_path)
            creation_time = os.path.getctime(file_path)

            file_info = {
                'filename': filename,
                'size': file_size,
                'created': creation_time
            }

            if filename.startswith('generated_i2i_'):
                image_to_image.append(file_info)
            else:
                text_to_image.append(file_info)

    return render_template('saves.html', text_to_image=text_to_image, image_to_image=image_to_image)


@main.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)


@main.route('/download/<filename>')
def download(filename):
    try:
        return send_file(os.path.join(current_app.root_path, 'static', 'generated', filename), as_attachment=True)
    except FileNotFoundError:
        abort(404)


@main.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    file_path = os.path.join(current_app.root_path, 'static', 'generated', filename)
    try:
        os.remove(file_path)
        return jsonify({'success': True, 'message': 'File deleted successfully'})
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
