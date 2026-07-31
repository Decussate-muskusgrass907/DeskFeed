import sys
import time
import signal
import threading
import json
import requests
import socketio
from pathlib import Path
from datetime import datetime
from config import (
    SERVER_URL, WS_URL, DEVICE_NAME, DEVICE_ID, AUTH_TOKEN,
    ACTIVITY_INTERVAL, ENABLE_WEBCAM, ENABLE_MICROPHONE,
    ENABLE_OUTLOOK, ENABLE_BROWSER_TRACKING, ENABLE_FILE_EXPLORER
)
from services.activity_tracker import ActivityTracker
from services.outlook_watcher import OutlookWatcher
from services.stream_server import StreamServer
from services.crypto_utils import encrypt_payload
from services.logger import setup_logger

logger = setup_logger()

class LaptopAgent:
    def __init__(self):
        self.device_id = DEVICE_ID
        self.auth_token = AUTH_TOKEN
        self.pairing_pin = None
        self.sio = None
        self.connected = False
        self.running = True
        self.stream_server = None

        self.activity_tracker = ActivityTracker() if ENABLE_BROWSER_TRACKING or ENABLE_FILE_EXPLORER else None
        self.outlook_watcher = OutlookWatcher() if ENABLE_OUTLOOK else None

    def register_device(self):
        logger.info("Registering device with server...")
        last_err = None
        for attempt in range(5):
            try:
                resp = requests.post(
                    f"{SERVER_URL}/api/auth/register-device",
                    json={"name": DEVICE_NAME},
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.device_id = data['deviceId']
                    self.pairing_pin = data['pairingPin']
                    logger.info(f"Device registered! ID: {self.device_id}")
                    logger.info(f"===== PAIRING PIN: {self.pairing_pin} =====")
                    logger.info("Use this PIN in the mobile app to pair.")
                    creds_path = Path(__file__).resolve().parent.parent / "DeskFeed Controller" / "credentials.json"
                    try:
                        creds_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(creds_path, "w") as f:
                            json.dump({"deviceId": self.device_id, "pairingPin": self.pairing_pin}, f)
                    except Exception:
                        pass
                    return True
                else:
                    logger.error(f"Registration failed: {resp.text}")
                    return False
            except Exception as e:
                last_err = e
                logger.warning(f"Registration attempt {attempt + 1}/5 failed: {e}")
                time.sleep(4)
        logger.error(f"Registration failed after 5 attempts: {last_err}")
        return False

    def pair_device(self):
        logger.info("Pairing device...")
        try:
            resp = requests.post(
                f"{SERVER_URL}/api/auth/pair-device",
                json={"deviceId": self.device_id, "pairingPin": self.pairing_pin},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data['token']
                logger.info("Device paired successfully!")
                return True
            else:
                logger.error(f"Pairing failed: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Pairing error: {e}")
            return False

    def connect_socketio(self):
        self.sio = socketio.Client()

        @self.sio.on('connect', namespace='/agent')
        def on_connect():
            logger.info("Socket.IO connected to /agent")
            self.connected = True

        @self.sio.on('disconnect', namespace='/agent')
        def on_disconnect():
            logger.info("Socket.IO disconnected from /agent")
            self.connected = False
            if self.running:
                logger.info("Reconnecting in 5 seconds...")
                time.sleep(5)
                self.connect_socketio()

        @self.sio.on('stream:request', namespace='/agent')
        def on_stream_request(data=None):
            logger.info("Stream request received")
            self.start_streaming()

        @self.sio.on('stream:stop', namespace='/agent')
        def on_stream_stop(data=None):
            logger.info("Stream stop received")
            self.stop_streaming()

        try:
            self.sio.connect(
                SERVER_URL,
                auth={'token': self.auth_token},
                namespaces=['/agent'],
                wait_timeout=15
            )
        except Exception as e:
            logger.error(f"Socket.IO connection error: {e}")

    def start_streaming(self):
        if not self.stream_server:
            self.stream_server = StreamServer(self.sio)
        threading.Thread(target=self.stream_server.start, daemon=True).start()

    def stop_streaming(self):
        if self.stream_server:
            self.stream_server.stop()

    def send_activity(self):
        if not self.connected or not self.activity_tracker:
            return
        activity = self.activity_tracker.get_current_activity()
        if activity:
            try:
                self.sio.emit('activity:log', activity, namespace='/agent')
            except Exception as e:
                logger.error(f"Send activity error: {e}")

    def start_activity_loop(self):
        def loop():
            while self.running:
                self.send_activity()
                time.sleep(ACTIVITY_INTERVAL)
        threading.Thread(target=loop, daemon=True).start()

    def start_outlook_watcher(self):
        if not self.outlook_watcher:
            return
        def watch():
            while self.running:
                alert = self.outlook_watcher.check_for_new_email()
                if alert and self.connected:
                    try:
                        self.sio.emit('email:alert', alert, namespace='/agent')
                        logger.info(f"Email alert sent: {alert['subject']}")
                    except Exception as e:
                        logger.error(f"Send email alert error: {e}")
                time.sleep(3)
        threading.Thread(target=watch, daemon=True).start()

    def run(self):
        logger.info(f"Starting DeskFeed Agent: {DEVICE_NAME}")

        if not self.device_id:
            if not self.register_device():
                logger.error("Failed to register. Exiting.")
                return
            if not self.pair_device():
                logger.error("Failed to pair. Exiting.")
                return

        self.connect_socketio()
        time.sleep(2)

        if not self.connected:
            logger.warning("Socket.IO not connected, continuing anyway...")

        self.start_activity_loop()
        self.start_outlook_watcher()

        signal.signal(signal.SIGTERM, lambda *_: setattr(self, 'running', False))

        logger.info("Agent is running. Press Ctrl+C to stop.")
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            logger.info("Shutting down...")
            self.running = False
            self.stop_streaming()
            if self.sio and self.sio.connected:
                self.sio.disconnect()

if __name__ == '__main__':
    agent = LaptopAgent()
    agent.run()
