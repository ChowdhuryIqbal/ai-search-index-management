import requests
import base64
import logging

def analyze_image_with_gpt4v(image_path, gpt4v_endpoint, headers):
    encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode('ascii')

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You can analyze images. You are an expert in understanding diagrams and workflows based on legends found in an image."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this image and describe its contents, including any legends, diagrams, or workflows you can identify."
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(gpt4v_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to make the request. Error: {e}")
        return None
