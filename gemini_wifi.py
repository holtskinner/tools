import json

import macwifi

import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Image,
)

from google.cloud.documentai import (
    DocumentProcessorServiceClient,
    ProcessRequest,
    RawDocument,
)

PROJECT_ID = "PROJECT_ID"
LOCATION = "us-central1"


def connect_to_wifi(ssid: str, password: str):
    """Connects to the specified Wi-Fi network on a macOS device.

    Args:
        ssid (str): The name (SSID) of the Wi-Fi network.
        password (str): The password for the Wi-Fi network.
    """

    try:
        # Attempt connection
        result = macwifi.connect(ssid, password)

        if result:
            print(f"Successfully connected to '{ssid}'")
        else:
            print(f"Failed to connect to '{ssid}'")
    except Exception as e:
        print(f"An error occurred: {e}")


def process_document(image_path: str) -> str:
    PROCESSOR_ID = "a14dae8f043b60bd"

    client = DocumentProcessorServiceClient()
    processor_name = client.processor_path(PROJECT_ID, "us", PROCESSOR_ID)

    with open(image_path, "rb") as f:
        content = f.read()
    request = ProcessRequest(
        raw_document=RawDocument(content=content, mime_type="image/jpeg"),
        name=processor_name,
    )
    response = client.process_document(request)

    return response.document.text


def get_wifi_info(image_path: str) -> tuple:

    # document_text = process_document(image_path)

    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    model = GenerativeModel(
        model_name="gemini-1.5-flash-001",
        generation_config=GenerationConfig(response_mime_type="application/json"),
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
    )

    #     wifi_network_extraction_prompt = """
    # The following text lists a wifi network and password. Output the network (SSID) and password in the following JSON format.

    # {
    #     "ssid": "Wifi Network Name (SSID)",
    #     "password": "Wifi Network Password"
    # }
    # """

    wifi_network_extraction_prompt = """
The following text and image lists a wifi network and password. Output the network (SSID) and password in the following JSON format. The strings are case sensitive, and pay special attention to spaces.

{
    "ssid": "Wifi Network Name (SSID)",
    "password": "Wifi Network Password"
}
"""

    image = Image.load_from_file(image_path)
    # Send to Gemini
    response = model.generate_content([wifi_network_extraction_prompt, image])
    wifi_info = json.loads(response.text)
    print(wifi_info)
    return wifi_info["ssid"], wifi_info["password"]


if __name__ == "__main__":
    ssid, password = get_wifi_info("/Users/holtskinner/Downloads/IMG_6036.jpeg")

    # connect_to_wifi(ssid, password)
