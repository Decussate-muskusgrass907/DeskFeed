import threading, json, base64, time, io
import numpy as np
try:
    import cv2; HAS_CAM = True
except ImportError:
    HAS_CAM = False
try:
    import sounddevice as sd; HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
try:
    from mss import mss; HAS_SCREEN = True
except ImportError:
    HAS_SCREEN = False
from .logger import setup_logger
logger = setup_logger()

class StreamServer:
    def __init__(self, sio, quality=40, max_fps=8, resize_width=960):
        self.sio = sio
        self.quality = quality
        self.frame_interval = 1.0 / max_fps
        self.resize_width = resize_width
        self.running = False
        self.camera = None
        self.screen_cap = None
        self.threads = []

    def start(self):
        self.running = True
        logger.info("Starting stream (screen + mic)...")
        if HAS_SCREEN:
            t = threading.Thread(target=self._screen_loop, daemon=True)
            t.start(); self.threads.append(t)
            logger.info("Screen capture started")
        if HAS_CAM:
            try:
                self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 10)
                if self.camera.isOpened():
                    t = threading.Thread(target=self._video_loop, daemon=True)
                    t.start(); self.threads.append(t)
                    logger.info("Webcam started")
                else:
                    logger.warning("No webcam")
            except Exception as e:
                logger.error(f"Cam error: {e}")
        if HAS_AUDIO:
            try:
                t = threading.Thread(target=self._audio_loop, daemon=True)
                t.start(); self.threads.append(t)
                logger.info("Mic started")
            except Exception as e:
                logger.error(f"Mic error: {e}")
        # Don't join — threads are daemon; joining blocks the caller (Socket.IO event thread)

    def stop(self):
        self.running = False
        if HAS_CAM and self.camera:
            self.camera.release()
        logger.info("Stream stopped")

    def _screen_loop(self):
        with mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                t0 = time.time()
                try:
                    img = sct.grab(monitor)
                    frame = np.frombuffer(img.rgb, dtype=np.uint8).reshape(img.height, img.width, 3)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    h, w = frame.shape[:2]
                    if w > self.resize_width:
                        ratio = self.resize_width / w
                        frame = cv2.resize(frame, (self.resize_width, int(h * ratio)),
                                           interpolation=cv2.INTER_LINEAR)
                    _, buf = cv2.imencode('.jpg', frame,
                                          [cv2.IMWRITE_JPEG_QUALITY, self.quality])
                    self.sio.emit('stream:video', {
                        'source': 'screen',
                        'data': base64.b64encode(buf).decode('utf-8'),
                        'ts': time.time(),
                    }, namespace='/agent')
                except Exception as e:
                    logger.error(f"Screen error: {e}")
                elapsed = time.time() - t0
                if elapsed < self.frame_interval:
                    time.sleep(self.frame_interval - elapsed)

    def _video_loop(self):
        while self.running and self.camera and self.camera.isOpened():
            t0 = time.time()
            ret, frame = self.camera.read()
            if not ret:
                time.sleep(0.05); continue
            h, w = frame.shape[:2]
            if w > self.resize_width:
                ratio = self.resize_width / w
                frame = cv2.resize(frame, (self.resize_width, int(h * ratio)),
                                   interpolation=cv2.INTER_LINEAR)
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            try:
                self.sio.emit('stream:video', {
                    'source': 'webcam',
                    'data': base64.b64encode(buf).decode('utf-8'),
                    'ts': time.time(),
                }, namespace='/agent')
            except Exception:
                break
            elapsed = time.time() - t0
            if elapsed < self.frame_interval:
                time.sleep(self.frame_interval - elapsed)

    def _audio_loop(self):
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16',
                            blocksize=1024) as stream:
            while self.running:
                try:
                    data, _ = stream.read(1024)
                    self.sio.emit('stream:audio', {
                        'data': base64.b64encode(data).decode('utf-8'),
                        'ts': time.time(),
                        'sampleRate': 16000,
                        'channels': 1,
                    }, namespace='/agent')
                except Exception as e:
                    logger.error(f"Audio error: {e}")
                    time.sleep(0.1)
