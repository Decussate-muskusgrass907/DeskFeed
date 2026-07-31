# DeskFeed Agent - Windows Monitoring Client

## Prerequisites
- Windows 10/11
- Python 3.10 or higher
- Outlook (for email alerts, optional)
- Webcam & Microphone (for live streaming, optional)

## Quick Start

### 1. Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
Copy `.env` and edit:
```
SERVER_URL=http://your-server-ip:3000
WS_URL=ws://your-server-ip:3000
DEVICE_NAME=DeskFeed-Agent
```

### 3. Run & Register
```powershell
.\venv\Scripts\python main.py
```
On first run, it will register with the backend and display a **Device ID** and **Pairing PIN**. Save these — you'll need them for the Android app.

### 4. Install as Background Service
Run `install_service.bat` as Administrator to install as a Windows scheduled task (auto-starts on login).

## Modules
| Module | File | Description |
|--------|------|-------------|
| Activity Tracker | `services/activity_tracker.py` | Captures browser URLs, folder paths, active windows every 5s |
| Outlook Watcher | `services/outlook_watcher.py` | Monitors Outlook for new emails and sends instant alerts |
| Stream Server | `services/stream_server.py` | Webcam + microphone streaming via WebSocket |
| Crypto Utils | `services/crypto_utils.py` | AES encryption for payloads |

## Troubleshooting
- **"Outlook not found"**: The agent runs fine without Outlook; email alerts just won't work.
- **"Webcam not found"**: Streaming is optional; errors are non-fatal.
- Ensure your firewall allows outbound connections to the server's port.
