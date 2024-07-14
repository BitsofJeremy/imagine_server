import os
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from app.forms import ImageGenerationForm, ImageToImageForm
from app.utils import generate_image, generate_image_to_image
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/generate', methods=['GET', 'POST'])
def generate():
    form = ImageGenerationForm()
    if form.validate_on_submit():
        workflow_path = os.path.join(current_app.root_path, 'workflows', 'base_workflow.json')
        with open(workflow_path, 'r') as f:
            workflow = f.read()

        try:
            result = generate_image(
                workflow,
                form.positive_prompt.data,
                form.negative_prompt.data
            )
            for progress in result:
                if isinstance(progress, str):
                    # This is a progress update
                    # In a real-time application, you might want to use websockets to send these updates to the client
                    print(progress)
                else:
                    # This is the final result (list of images)
                    if progress:
                        # Save the first image and return its filename
                        filename = secure_filename(f"generated_{form.positive_prompt.data[:10]}.png")
                        filepath = os.path.join(current_app.root_path, 'static', 'generated', filename)
                        with open(filepath, 'wb') as f:
                            f.write(progress[0]['image_data'])
                        return jsonify({'success': True, 'filename': filename})

            return jsonify({'success': False, 'error': 'No image generated'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return render_template('generate.html', form=form)


@main.route('/generate_image_to_image', methods=['GET', 'POST'])
def generate_image_to_image():
    form = ImageToImageForm()
    if form.validate_on_submit():
        workflow_path = os.path.join(current_app.root_path, 'workflows', 'basic_image_to_image.json')
        with open(workflow_path, 'r') as f:
            workflow = f.read()

        input_image = form.input_image.data
        filename = secure_filename(input_image.filename)
        filepath = os.path.join(current_app.root_path, 'static', 'uploads', filename)
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
                    # This is a progress update
                    print(progress)
                else:
                    # This is the final result (list of images)
                    if progress:
                        # Save the first image and return its filename
                        output_filename = secure_filename(f"generated_{form.positive_prompt.data[:10]}.png")
                        output_filepath = os.path.join(current_app.root_path, 'static', 'generated', output_filename)
                        with open(output_filepath, 'wb') as f:
                            f.write(progress[0]['image_data'])
                        return jsonify({'success': True, 'filename': output_filename})

            return jsonify({'success': False, 'error': 'No image generated'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return render_template('generate.html', form=form, image_to_image=True)


@main.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)


@main.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(current_app.root_path, 'static', 'generated', filename), as_attachment=True)