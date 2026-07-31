import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:3000')
WS_URL = os.getenv('WS_URL', 'ws://localhost:3000')
DEVICE_NAME = os.getenv('DEVICE_NAME', 'My-Work-Laptop')
DEVICE_ID = os.getenv('DEVICE_ID', '')
AUTH_TOKEN = os.getenv('AUTH_TOKEN', '')
ACTIVITY_INTERVAL = int(os.getenv('ACTIVITY_INTERVAL', '5'))

ENABLE_WEBCAM = os.getenv('ENABLE_WEBCAM', 'true').lower() == 'true'
ENABLE_MICROPHONE = os.getenv('ENABLE_MICROPHONE', 'true').lower() == 'true'
ENABLE_OUTLOOK = os.getenv('ENABLE_OUTLOOK', 'true').lower() == 'true'
ENABLE_BROWSER_TRACKING = os.getenv('ENABLE_BROWSER_TRACKING', 'true').lower() == 'true'
ENABLE_FILE_EXPLORER = os.getenv('ENABLE_FILE_EXPLORER', 'true').lower() == 'true'
