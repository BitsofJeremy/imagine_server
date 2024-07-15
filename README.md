# Imagine Server

Imagine Server is a user-friendly web application that brings the power of AI image generation to your local network. Built with Flask and integrated with ComfyUI, it offers an easy-to-use interface for creating and transforming images using advanced AI models.

## Features

- **Text-to-Image Generation**: Create unique images from text descriptions.
- **Image-to-Image Transformation**: Modify existing images using text prompts.
- **User-Friendly Interface**: Simple forms for inputting prompts and parameters.
- **Mobile-Ready Design**: Built with Bulma CSS for a responsive layout that works well on tablets and phones.
- **Local Network Deployment**: Run on your home network for fast, private image generation.
- **Customizable Settings**: Adjust parameters like steps, CFG scale, and sampling methods.
- **Multiple AI Models**: Choose from various pre-trained models for different styles and capabilities.
- **Easy Updates**: Simple script for deploying and updating the application.

## Prerequisites

Before you begin, make sure you have the following installed on your Linux system:

- Python 3.7 or higher
- pip (Python package manager)
- git
- Nginx (will be installed by the setup script if not present)

You should also have ComfyUI installed and running on your system.

## Installation

1. Open a terminal on your Linux system.

2. Download the deployment script:
   ```
   curl -O https://raw.githubusercontent.com/BitsofJeremy/imagine_server/main/deploy.sh
   ```

3. Make the script executable:
   ```
   chmod +x deploy.sh
   ```

4. Run the deployment script with sudo:
   ```
   sudo ./deploy.sh
   ```

   This script will:
   - Install necessary dependencies
   - Set up a system user for the application
   - Clone the Imagine Server repository
   - Create a Python virtual environment
   - Install required Python packages
   - Set up the application as a system service
   - Configure Nginx as a reverse proxy

5. After the script finishes, the Imagine Server should be up and running!

## Accessing Imagine Server

Once installed, you can access Imagine Server by opening a web browser and navigating to:

```
http://imagineserver.home.test
```

Note: You may need to add this domain to your computer's hosts file or local DNS server for it to work.

## Usage

1. **Text-to-Image Generation**:
   - Click on "Generate Image" in the navigation menu.
   - Enter a description of the image you want to create in the "Positive Prompt" field.
   - Optionally, enter things you don't want in the image in the "Negative Prompt" field.
   - Adjust other parameters as desired.
   - Click "Generate Image" and wait for your image to be created!

2. **Image-to-Image Transformation**:
   - Click on "Image to Image" in the navigation menu.
   - Upload an existing image.
   - Enter prompts to describe how you want to change the image.
   - Adjust parameters and click "Generate Image" to transform your image.

3. **Viewing and Downloading Images**:
   - After generation, your image will be displayed on the screen.
   - Click the "Download Image" button to save the image to your device.

## Updating Imagine Server

To update Imagine Server to the latest version:

1. Open a terminal and navigate to the directory containing `deploy.sh`.
2. Run the update command:
   ```
   sudo ./deploy.sh --update
   ```

This will pull the latest changes from the repository and restart the service.

## Troubleshooting

- If you can't access the web interface, make sure Nginx and the Imagine Server service are running:
  ```
  sudo systemctl status nginx
  sudo systemctl status imagineserver
  ```
- Check the application logs for errors:
  ```
  sudo journalctl -u imagineserver
  ```
- Make sure ComfyUI is running and accessible at the URL specified in your configuration.

## Contributing

We welcome contributions! If you have suggestions or find bugs, please open an issue on our GitHub repository.

## License

GNU Affero General Public License v3.0. Read more here: [LICENSE](LICENSE)

---

We hope you enjoy using Imagine Server for all your AI image generation needs! If you have any questions or need further assistance, please don't hesitate to reach out or check our documentation.


