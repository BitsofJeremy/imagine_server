# Imagine Server

Imagine Server is a Flask-based web application that integrates with ComfyUI to provide an easy-to-use interface for image generation and image-to-image transformation.

## Features

- Basic image generation using ComfyUI
- Image-to-image transformation
- Mobile-ready design using Bulma CSS
- WebSocket integration with ComfyUI

## Setup

1. Clone the repository
2. Install the required packages: `pip install -r requirements.txt`
3. Set up ComfyUI as a service on your Debian Linux machine
4. Configure Nginx for both ComfyUI and the Flask application
5. Run the Flask application: `python run.py`

## Usage

1. Navigate to the home page
2. Choose between basic image generation or image-to-image transformation
3. Fill in the required fields and submit the form
4. View and download the generated image

## Development

- The main application logic is in `app/routes.py`
- ComfyUI integration functions are in `app/utils.py`
- Templates are stored in `app/templates/`
- Static files (CSS, JS, images) are in `app/static/`

## Deployment

Use the `deploy.sh` script to automate the deployment process.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

GNU Affero General Public License v3.0. Read more here: [LICENSE](LICENSE)