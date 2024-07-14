# Imagine Server

Imagine Server is a Flask-based web application that integrates with ComfyUI to provide an easy-to-use interface for image generation and image-to-image transformation.

## Features

- Basic image generation using ComfyUI
- Image-to-image transformation
- Mobile-ready design using Bulma CSS
- WebSocket integration with ComfyUI

## Prerequisites

- Python 3.7+
- Nginx
- ComfyUI
- Git

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/imagine-server.git
   cd imagine-server
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up ComfyUI as a service on your Debian Linux machine (see `comfyui.service`)

4. Configure Nginx for both ComfyUI and the Flask application (see `nginx_comfyui.conf` and `nginx_flask.conf`)

5. Set up the Flask application as a service (see `imagineserver.service`)

6. Update the `config.py` file with your settings

## Deployment

1. Make sure you have the `deploy.sh` script in your project root directory and it's executable:
   ```
   chmod +x deploy.sh
   ```

2. Update the configuration variables in `deploy.sh` to match your setup

3. Run the deployment script:
   ```
   ./deploy.sh
   ```

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

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

GNU Affero General Public License v3.0. Read more here: [LICENSE](LICENSE)