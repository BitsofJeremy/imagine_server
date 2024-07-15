import json
import logging
import random
import os
import websocket
import requests
import uuid
from flask import current_app
from urllib.parse import urlencode
from requests_toolbelt import MultipartEncoder

logger = logging.getLogger(__name__)


def open_websocket_connection():
    server_address = current_app.config['COMFYUI_URL']
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws_url = f"ws://{server_address.replace('http://', '')}/ws?clientId={client_id}"
    logger.debug(f"Attempting to connect to WebSocket: {ws_url}")
    try:
        ws.connect(ws_url)
        logger.info(f"WebSocket connection established: {ws_url}")
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket: {e}")
        raise
    return ws, server_address, client_id


def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    url = f"{server_address}/prompt"
    headers = {'Content-Type': 'application/json'}
    logger.debug(f"Queueing prompt: URL={url}, Data={data}")
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"Prompt queued successfully: {response_data}")
        if 'prompt_id' not in response_data:
            logger.error(f"Unexpected response from ComfyUI: {response_data}")
            raise ValueError(f"Unexpected response from ComfyUI: {response_data}")
        return response_data['prompt_id']
    except requests.RequestException as e:
        logger.error(f"Failed to queue prompt: {e}")
        raise


def get_image(filename, subfolder, folder_type, server_address):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url = f"{server_address}/view?{urlencode(params)}"
    logger.debug(f"Fetching image: URL={url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"Image fetched successfully: {filename}")
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch image: {e}")
        raise


def upload_image(input_path, name, server_address, image_type="input", overwrite=False):
    logger.debug(f"Uploading image: {input_path}")
    try:
        with open(input_path, 'rb') as file:
            form = MultipartEncoder({
                'image': (name, file, 'image/png'),
                'type': image_type,
                'overwrite': str(overwrite).lower()
            })
            headers = {'Content-Type': form.content_type}
            url = f"{server_address}/upload/image"
            response = requests.post(url, data=form, headers=headers)
            response.raise_for_status()
            logger.info(f"Image uploaded successfully: {name}")
            return response.content
    except (IOError, requests.RequestException) as e:
        logger.error(f"Failed to upload image: {e}")
        raise


def get_history(prompt_id, server_address):
    url = f"{server_address}/history/{prompt_id}"
    logger.debug(f"Fetching history: URL={url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        history = response.json()
        logger.info(f"History fetched successfully for prompt {prompt_id}")
        logger.debug(f"History content: {history}")
        return history
    except requests.RequestException as e:
        logger.error(f"Failed to fetch history: {e}")
        raise


def track_progress(prompt, ws, prompt_id):
    node_ids = list(prompt.keys())
    finished_nodes = []

    logger.debug(f"Tracking progress for prompt_id: {prompt_id}")
    logger.debug(f"Node IDs in prompt: {node_ids}")

    while True:
        try:
            out = ws.recv()
            logger.debug(f"Received WebSocket message: {out}")
            if isinstance(out, str):
                message = json.loads(out)
                logger.debug(f"Parsed WebSocket message: {message}")
                if message['type'] == 'progress':
                    data = message['data']
                    yield f"Progress: Step {data['value']} of {data['max']}"
                elif message['type'] in ['execution_start', 'execution_cached', 'executing']:
                    data = message['data']
                    if 'node' in data:
                        if data['node'] is not None and data['node'] not in finished_nodes:
                            finished_nodes.append(data['node'])
                            yield f"Progress: {len(finished_nodes)}/{len(node_ids)} tasks done"
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            logger.info(f"Prompt {prompt_id} execution completed")
                            break
                    elif 'nodes' in data:
                        # Handle batch node execution
                        for node in data['nodes']:
                            if node not in finished_nodes:
                                finished_nodes.append(node)
                        yield f"Progress: {len(finished_nodes)}/{len(node_ids)} tasks done"
                        if set(finished_nodes) == set(node_ids) and data['prompt_id'] == prompt_id:
                            logger.info(f"Prompt {prompt_id} execution completed")
                            break
                    else:
                        logger.warning(f"Unexpected message structure: {data}")
                elif message['type'] == 'executed':
                    if 'prompt_id' in message['data'] and message['data']['prompt_id'] == prompt_id:
                        logger.info(f"Prompt {prompt_id} execution completed")
                        break
            else:
                logger.warning(f"Received non-string WebSocket message: {out}")
        except Exception as e:
            logger.error(f"Error during progress tracking: {e}")
            yield f"Error: {str(e)}"


def generate_image(workflow, positive_prompt, negative_prompt='', steps=20, cfg=8, sampler_name='euler',
                   scheduler='normal', denoise=1, ckpt_name='SD15/cyberrealistic_classicV31.safetensors',
                   width=512, height=512, batch_size=1, save_previews=False):
    prompt = json.loads(workflow)
    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}

    # Update node #3 (KSampler)
    k_sampler = next((key for key, value in id_to_class_type.items() if value == 'KSampler'), None)
    if k_sampler is None:
        logger.error("KSampler not found in the workflow")
        raise ValueError("KSampler not found in the workflow")

    prompt[k_sampler]['inputs'].update({
        'seed': random.randint(10 ** 14, 10 ** 15 - 1),
        'steps': steps,
        'cfg': cfg,
        'sampler_name': sampler_name,
        'scheduler': scheduler,
        'denoise': denoise
    })

    # Update node #4 (CheckpointLoaderSimple)
    checkpoint_loader = next((key for key, value in id_to_class_type.items() if value == 'CheckpointLoaderSimple'),
                             None)
    if checkpoint_loader is None:
        logger.error("CheckpointLoaderSimple not found in the workflow")
        raise ValueError("CheckpointLoaderSimple not found in the workflow")

    prompt[checkpoint_loader]['inputs']['ckpt_name'] = ckpt_name

    # Update node #5 (EmptyLatentImage)
    empty_latent = next((key for key, value in id_to_class_type.items() if value == 'EmptyLatentImage'), None)
    if empty_latent is None:
        logger.error("EmptyLatentImage not found in the workflow")
        raise ValueError("EmptyLatentImage not found in the workflow")

    prompt[empty_latent]['inputs'].update({
        'width': width,
        'height': height,
        'batch_size': batch_size
    })

    # Update prompts
    positive_input_id = prompt[k_sampler]['inputs']['positive'][0]
    prompt[positive_input_id]['inputs']['text'] = positive_prompt

    if negative_prompt:
        negative_input_id = prompt[k_sampler]['inputs']['negative'][0]
        prompt[negative_input_id]['inputs']['text'] = negative_prompt

    logger.info(
        f"Generating image with parameters: positive_prompt={positive_prompt}, negative_prompt={negative_prompt}, "
        f"steps={steps}, cfg={cfg}, sampler_name={sampler_name}, scheduler={scheduler}, denoise={denoise}, "
        f"ckpt_name={ckpt_name}, width={width}, height={height}, batch_size={batch_size}")

    image_generator = generate_image_by_prompt(prompt, save_previews)

    images = []
    for item in image_generator:
        if isinstance(item, str):
            yield item
        elif isinstance(item, list):
            images = item

    logger.info(f"Generated {len(images)} images")
    yield images


def generate_image_to_image(workflow, input_path, positive_prompt, negative_prompt='', seed=-1, steps=20, cfg=8,
                            sampler_name='euler_ancestral', scheduler='karras', denoise=0.8,
                            ckpt_name='SDXL/juggernautXL_version5.safetensors', save_previews=False):
    prompt = json.loads(workflow)
    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}

    # Update node #3 (KSampler)
    k_sampler = next((key for key, value in id_to_class_type.items() if value == 'KSampler'), None)
    if k_sampler is None:
        logger.error("KSampler not found in the workflow")
        raise ValueError("KSampler not found in the workflow")

    prompt[k_sampler]['inputs'].update({
        'seed': seed if seed != -1 else random.randint(10 ** 14, 10 ** 15 - 1),
        'steps': steps,
        'cfg': cfg,
        'sampler_name': sampler_name,
        'scheduler': scheduler,
        'denoise': denoise
    })

    # Update node #4 (CheckpointLoaderSimple)
    checkpoint_loader = next((key for key, value in id_to_class_type.items() if value == 'CheckpointLoaderSimple'),
                             None)
    if checkpoint_loader is None:
        logger.error("CheckpointLoaderSimple not found in the workflow")
        raise ValueError("CheckpointLoaderSimple not found in the workflow")

    prompt[checkpoint_loader]['inputs']['ckpt_name'] = ckpt_name

    # Update prompts
    positive_input_id = prompt[k_sampler]['inputs']['positive'][0]
    prompt[positive_input_id]['inputs']['text'] = positive_prompt

    if negative_prompt:
        negative_input_id = prompt[k_sampler]['inputs']['negative'][0]
        prompt[negative_input_id]['inputs']['text'] = negative_prompt

    # Update input image
    image_loader = next((key for key, value in id_to_class_type.items() if value == 'LoadImage'), None)
    if image_loader is None:
        logger.error("LoadImage not found in the workflow")
        raise ValueError("LoadImage not found in the workflow")

    filename = os.path.basename(input_path)
    prompt[image_loader]['inputs']['image'] = filename

    logger.info(f"Generating image-to-image with input: {input_path}, positive prompt: {positive_prompt}, "
                f"negative prompt: {negative_prompt}, seed: {seed}, steps: {steps}, cfg: {cfg}, "
                f"sampler_name: {sampler_name}, scheduler: {scheduler}, denoise: {denoise}, "
                f"ckpt_name: {ckpt_name}")

    image_generator = generate_image_by_prompt_and_image(prompt, input_path, filename, save_previews)

    images = []
    for item in image_generator:
        if isinstance(item, str):
            yield item
        elif isinstance(item, list):
            images = item

    logger.info(f"Generated {len(images)} images")
    yield images


def generate_image_by_prompt(prompt, save_previews=False):
    ws, server_address, client_id = open_websocket_connection()
    try:
        prompt_id = queue_prompt(prompt, client_id, server_address)
        yield f"Prompt queued with ID: {prompt_id}"

        for progress in track_progress(prompt, ws, prompt_id):
            yield progress

        history = get_history(prompt_id, server_address)
        if prompt_id not in history:
            logger.error(f"No history found for prompt ID: {prompt_id}")
            yield f"Error: No history found for prompt ID: {prompt_id}"
            yield []
            return

        images = get_images_from_history(history[prompt_id], server_address, save_previews)
        if not images:
            logger.warning(f"No images generated for prompt ID: {prompt_id}")
            yield "Warning: No images were generated"
        yield images
    except Exception as e:
        logger.error(f"Error in generate_image_by_prompt: {e}")
        yield f"Error: {str(e)}"
        yield []
    finally:
        ws.close()


def generate_image_by_prompt_and_image(prompt, input_path, filename, save_previews=False):
    ws, server_address, client_id = open_websocket_connection()
    try:
        upload_image(input_path, filename, server_address)
        prompt_id = queue_prompt(prompt, client_id, server_address)
        yield f"Prompt queued with ID: {prompt_id}"

        for progress in track_progress(prompt, ws, prompt_id):
            yield progress

        history = get_history(prompt_id, server_address)
        if prompt_id not in history:
            logger.error(f"No history found for prompt ID: {prompt_id}")
            yield f"Error: No history found for prompt ID: {prompt_id}"
            yield []
            return

        images = get_images_from_history(history[prompt_id], server_address, save_previews)
        if not images:
            logger.warning(f"No images generated for prompt ID: {prompt_id}")
            yield "Warning: No images were generated"
        yield images
    except Exception as e:
        logger.error(f"Error in generate_image_by_prompt_and_image: {e}")
        yield f"Error: {str(e)}"
        yield []
    finally:
        ws.close()


def get_images_from_history(history, server_address, allow_preview=False):
    output_images = []
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            for image in node_output['images']:
                if (allow_preview and image['type'] == 'temp') or image['type'] == 'output':
                    image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                    output_images.append({
                        'image_data': image_data,
                        'file_name': image['filename'],
                        'type': image['type']
                    })
    logger.info(f"Retrieved {len(output_images)} images from history")
    return output_images