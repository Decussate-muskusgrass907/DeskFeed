# 📡 DeskFeed

**Real-time Windows activity monitoring, remote live viewing, and instant email alerts — all accessible from your Android phone.**

DeskFeed is an end-to-end remote monitoring system that runs on your Windows PC and streams live activity to a mobile app. It tracks foreground applications, browser URLs, and file explorer paths; watches Outlook for incoming mail; captures your screen, webcam, and microphone on demand; and delivers it all to your phone over WebSocket — locally on your network or remotely through an ngrok tunnel.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖥️ **Activity Tracking** | Captures foreground app, browser URL, and folder path every 5 seconds |
| 📧 **Email Alerts** | Watches Outlook for new mail and pushes instant FCM notifications |
| 📹 **Live View** | On-demand screen + webcam video and microphone audio streaming |
| 📱 **Android Viewer** | Flutter app with real-time dashboard, stream viewer, and audio playback |
| 🔐 **PIN Pairing** | 6-digit PIN-based device registration and pairing with JWT auth |
| 🌐 **Remote Access** | ngrok tunnel integration for monitoring from anywhere |
| 🖥️ **Controller GUI** | Windows desktop app that manages backend, agent, and tunnel with one click |
| 🛡️ **Encrypted Payloads** | AES encryption utilities for sensitive data in transit |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANDROID PHONE                            │
│                    DeskFeed Mobile (Flutter)                    │
│                        │      ▲                                │
│                WebSocket      │ stream:video / stream:audio     │
│                (raw WS)       │ activity:update / email:alert   │
└────────────────────────▼──────┼─────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                  DESKFEED BACKEND (Node.js)                     │
│        Express REST API  +  Socket.IO / raw WebSocket relay     │
│        JWT auth · Prisma (SQLite/PostgreSQL) · FCM push         │
└───────▲────────────────────────▲────────────────────────────────┘
        │ Socket.IO (/agent)     │ HTTP (register/pair)
┌───────┴─────────┐      ┌───────┴───────────────────────┐
│ DESKFEED AGENT  │      │ DESKFEED CONTROLLER (Windows) │
│ (Python)        │      │ CustomTkinter GUI             │
│ Activity ·      │      │ Start/stop services ·         │
│ Outlook ·       │      │ ngrok tunnel · Pairing info   │
│ Screen/Cam/Mic  │      └───────────────────────────────┘
└─────────────────┘
```

**Components:**

- **Agent** *(Python)* — the monitoring client installed on the Windows PC. Collects activity, watches Outlook, and captures streams. Communicates with the backend over Socket.IO.
- **Backend** *(Node.js)* — central relay server. Authenticates devices with JWT, persists activity/email logs via Prisma, pushes FCM notifications, and bridges messages between the agent (Socket.IO) and the mobile app (raw WebSocket).
- **Controller** *(Python GUI)* — desktop launcher that starts the backend and agent, sets up the ngrok tunnel, shows live service status, and exposes the pairing credentials.
- **Mobile** *(Flutter)* — Android viewer that pairs with a device, shows the live activity dashboard, plays email alerts, and renders the live stream with audio.

---

## 📦 Repository Structure

```
DeskFeed/
├── DeskFeed Agent/        # Python monitoring client (Socket.IO)
│   ├── main.py            # Entry point: register, pair, connect, start modules
│   ├── config.py          # Environment-driven configuration
│   ├── requirements.txt
│   └── services/
│       ├── activity_tracker.py   # Foreground app / URL / folder tracking
│       ├── outlook_watcher.py    # Outlook new-email detection
│       ├── stream_server.py      # Screen (mss) + webcam (OpenCV) + mic (sounddevice)
│       └── crypto_utils.py       # AES payload encryption
│
├── DeskFeed Backend/      # Node.js relay server
│   ├── src/
│   │   ├── index.js              # Server bootstrap
│   │   ├── routes/auth.js        # register-device, pair-device, viewer-login
│   │   ├── routes/devices.js     # Device info, logs, email history
│   │   └── services/
│   │       ├── websocket.js      # Socket.IO /agent + /viewer namespaces
│   │       ├── raw_ws.js         # Raw WS bridge (mobile <-> agent)
│   │       ├── firebase.js       # FCM push notifications
│   │       └── database.js       # Prisma client
│   └── prisma/schema.prisma
│
├── DeskFeed Controller/   # Windows desktop GUI
│   ├── app.py             # CustomTkinter launcher (Dashboard / Pairing / Console)
│   ├── requirements.txt
│   └── build.bat          # PyInstaller build script
│
└── DeskFeed Mobile/       # Flutter Android app
    ├── lib/
    │   ├── main.dart
    │   ├── screens/       # login, dashboard, stream view
    │   ├── services/      # auth, websocket, notifications, config
    │   └── widgets/       # activity & email cards
    └── android/           # Android project
```

---

## 🚀 Getting Started

### 1. Backend — Cloud Relay Server

**Prerequisites:** Node.js 18+, npm, and a database (SQLite works out of the box).

```bash
cd DeskFeed Backend
npm install

# Configure environment
# Edit .env and set JWT_SECRET, DATABASE_URL (SQLite is default)
npx prisma generate
npx prisma db push        # create/update tables
npm start                 # or: npm run dev (auto-reload)
```

The server listens on `http://localhost:3000` (default). Verify with `GET /api/health`.

**Optional — Firebase push notifications:** create a Firebase project, download the service account key, save it as `firebase-service-account.json` in the backend root, and add your Android app config to the mobile project.

### 2. Agent — Windows Monitoring Client

**Prerequisites:** Windows 10/11, Python 3.10+.

```bash
cd DeskFeed Agent
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env` to point at your backend:

```ini
SERVER_URL=http://your-server-ip:3000
WS_URL=ws://your-server-ip:3000
```

Run the agent:

```powershell
.\venv\Scripts\python main.py
```

On first run, the agent registers with the backend and prints a **Device ID** and **Pairing PIN** — keep these for the mobile app. It also writes them to the shared `credentials.json` so the Controller can display them.

To run as a Windows background service, run `install_service.bat` as Administrator.

### 3. Mobile — Android Viewer

**Prerequisites:** Flutter SDK 3.16+, Android Studio.

```bash
cd DeskFeed Mobile
flutter pub get
```

1. Add your Firebase config: place `google-services.json` in `android/app/`.
2. Point the app at your server in `lib/services/auth_service.dart` and `lib/services/websocket_service.dart`:
   ```dart
   static const String _baseUrl = 'http://YOUR_SERVER_IP:3000';
   static const String _wsUrl = 'ws://YOUR_SERVER_IP:3000';
   ```
3. Run or build:
   ```bash
   flutter run
   flutter build apk --release    # -> build/app/outputs/flutter-apk/app-release.apk
   ```

### 4. Controller — Windows Desktop GUI *(optional convenience)*

**Prerequisites:** Python 3.10+, an ngrok account (for remote tunnel).

```bash
cd DeskFeed Controller
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The Controller provides three tabs:

- **Dashboard** — one-click start/stop for the backend and agent, ngrok tunnel setup, and live service status (green/red cards).
- **Pairing Info** — auto-detects the device credentials and shows the **Server URL**, **Device ID**, and **Pairing PIN** to enter in the mobile app.
- **Console** — streams logs from the managed processes.

To build a standalone EXE, run `build.bat` (requires PyInstaller).

---

## 📱 Pairing Flow

1. **Start** the backend, then the agent (via Controller or manually).
2. The agent registers with the server and receives a **Device ID** + **Pairing PIN**.
3. In the mobile app, enter the **Server URL** (`http://<host>:3000` or your ngrok URL), **Device ID**, and **Pairing PIN**.
4. The app logs in as a viewer and opens a WebSocket — the dashboard fills with live activity and email alerts.
5. Open **Live View** and press **Start Stream** to receive screen/webcam video and microphone audio.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register-device` | Register an agent; returns `deviceId` + `pairingPin` |
| POST | `/api/auth/pair-device` | Pair a device with its PIN; returns a JWT |
| POST | `/api/auth/viewer-login` | Mobile viewer login with PIN; returns a JWT |
| POST | `/api/auth/register-fcm` | Register a device's FCM push token |
| GET | `/api/devices/:id` | Get device info & status |
| GET | `/api/devices/:id/logs` | Get activity log history |
| GET | `/api/devices/:id/emails` | Get email alert history |
| GET | `/api/health` | Health check |

**WebSocket channels:**

- `/agent` *(Socket.IO)* — laptop agents connect and emit `activity:log`, `email:alert`, `stream:video`, `stream:audio`.
- `/viewer` *(Socket.IO)* — mobile viewers subscribe to a device room.
- `/viewer-ws`, `/agent-ws` *(raw WebSocket)* — used by the Flutter app; the backend bridges raw WS ↔ Socket.IO.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent | Python · python-socketio · mss · OpenCV · sounddevice · pywin32 |
| Backend | Node.js · Express · Socket.IO · ws · Prisma · JSON Web Tokens |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Controller | Python · CustomTkinter · PyInstaller |
| Mobile | Flutter · flutter_sound · firebase_messaging |
| Remote access | ngrok |

---

## 🔒 Security Notes

- **Never commit** `.env`, `credentials.json`, `config.json` (ngrok token), or `firebase-service-account.json` — all are in `.gitignore`.
- Change the default `JWT_SECRET` in the backend `.env` before deploying.
- Run the backend behind HTTPS in production (reverse proxy or ngrok).
- The agent's audio/video streaming is on-demand only — the stream stops when the viewer disconnects or sends `stream:stop`.
- Set a random `CRYPTO_SECRET` in the agent's `.env` — it is used to derive the AES encryption key.
- Pairing PINs expire after **10 minutes**, and repeated failed PIN attempts are **rate-limited** (5 per 5 minutes).
- Device data endpoints verify that the caller owns the device (JWT `deviceId` must match the URL).
- Stream requests are forwarded only to the paired agent's room, never broadcast to all agents.

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| Agent won't connect | Backend must be running first. Check `SERVER_URL`/`WS_URL` in agent `.env`. |
| Mobile can't reach server | Same Wi-Fi network, or use the ngrok tunnel URL. Allow port 3000 through the firewall. |
| Live View black / no audio | Ensure webcam/mic permissions are granted to the agent (Windows privacy settings) and the viewer app. |
| Push notifications missing | Verify `google-services.json` in the mobile project and the FCM token registration. |
| `stream:request` sent but no video | Confirm the agent is running and its Socket.IO connection is alive (`/agent` namespace). |
| Backend slow to start | `npm start` compiles TypeScript; wait a few seconds before testing `/api/health`. |

---

## 👤 Author

**Mohammad Liaquat Ali** — developer and maintainer of DeskFeed.

[GitHub](https://github.com/malik-cat) · [Project Repository](https://github.com/malik-cat/DeskFeed)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Copyright © 2026 Mohammad Liaquat Ali.
