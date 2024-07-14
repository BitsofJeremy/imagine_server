import websocket
import json
import requests
import uuid
import random
from flask import current_app
from urllib.parse import urlencode
from requests_toolbelt import MultipartEncoder

def open_websocket_connection():
    server_address = current_app.config['COMFYUI_URL'].replace('http://', '')
    client_id = str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
    return ws, server_address, client_id

def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    url = f"{current_app.config['COMFYUI_URL']}/prompt"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=data, headers=headers)
    return response.json()

def get_image(filename, subfolder, folder_type, server_address):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url = f"{current_app.config['COMFYUI_URL']}/view?{urlencode(params)}"
    response = requests.get(url)
    return response.content

def upload_image(input_path, name, server_address, image_type="input", overwrite=False):
    with open(input_path, 'rb') as file:
        form = MultipartEncoder({
            'image': (name, file, 'image/png'),
            'type': image_type,
            'overwrite': str(overwrite).lower()
        })
        headers = {'Content-Type': form.content_type}
        url = f"{current_app.config['COMFYUI_URL']}/upload/image"
        response = requests.post(url, data=form, headers=headers)
    return response.content

def get_history(prompt_id, server_address):
    url = f"{current_app.config['COMFYUI_URL']}/history/{prompt_id}"
    response = requests.get(url)
    return response.json()

def track_progress(prompt, ws, prompt_id):
    node_ids = list(prompt.keys())
    finished_nodes = []

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'progress':
                data = message['data']
                yield f"Progress: Step {data['value']} of {data['max']}"
            elif message['type'] in ['execution_cached', 'executing']:
                data = message['data']
                if data['node'] not in finished_nodes:
                    finished_nodes.append(data['node'])
                    yield f"Progress: {len(finished_nodes)}/{len(node_ids)} tasks done"
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

def generate_image(workflow, positive_prompt, negative_prompt='', save_previews=False):
    prompt = json.loads(workflow)
    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
    k_sampler = next(key for key, value in id_to_class_type.items() if value == 'KSampler')
    prompt[k_sampler]['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
    positive_input_id = prompt[k_sampler]['inputs']['positive'][0]
    prompt[positive_input_id]['inputs']['text'] = positive_prompt

    if negative_prompt:
        negative_input_id = prompt[k_sampler]['inputs']['negative'][0]
        prompt[negative_input_id]['inputs']['text'] = negative_prompt

    return generate_image_by_prompt(prompt, save_previews)

def generate_image_to_image(workflow, input_path, positive_prompt, negative_prompt='', save_previews=False):
    prompt = json.loads(workflow)
    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
    k_sampler = next(key for key, value in id_to_class_type.items() if value == 'KSampler')
    prompt[k_sampler]['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
    positive_input_id = prompt[k_sampler]['inputs']['positive'][0]
    prompt[positive_input_id]['inputs']['text'] = positive_prompt

    if negative_prompt:
        negative_input_id = prompt[k_sampler]['inputs']['negative'][0]
        prompt[negative_input_id]['inputs']['text'] = negative_prompt

    image_loader = next(key for key, value in id_to_class_type.items() if value == 'LoadImage')
    filename = input_path.split('/')[-1]
    prompt[image_loader]['inputs']['image'] = filename

    return generate_image_by_prompt_and_image(prompt, input_path, filename, save_previews)

def generate_image_by_prompt(prompt, save_previews=False):
    ws, server_address, client_id = open_websocket_connection()
    try:
        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
        for progress in track_progress(prompt, ws, prompt_id):
            yield progress
        history = get_history(prompt_id, server_address)[prompt_id]
        images = get_images_from_history(history, server_address, save_previews)
        return images
    finally:
        ws.close()

def generate_image_by_prompt_and_image(prompt, input_path, filename, save_previews=False):
    ws, server_address, client_id = open_websocket_connection()
    try:
        upload_image(input_path, filename, server_address)
        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
        for progress in track_progress(prompt, ws, prompt_id):
            yield progress
        history = get_history(prompt_id, server_address)[prompt_id]
        images = get_images_from_history(history, server_address, save_previews)
        return images
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
    return output_images