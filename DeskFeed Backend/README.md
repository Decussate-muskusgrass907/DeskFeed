# DeskFeed Backend - Cloud Relay Server

## Prerequisites
- Node.js 18+
- PostgreSQL 14+ (or SQLite via Prisma)
- Firebase Admin SDK account (for push notifications)

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Database
Edit `.env`:
```
DATABASE_URL="postgresql://user:password@localhost:5432/device_monitor"
```

For SQLite (development):
```
DATABASE_URL="file:./dev.db"
```

Edit `prisma/schema.prisma` and change `provider` to `"sqlite"` if using SQLite.

### 3. Run Migrations
```bash
npx prisma generate
npx prisma db push
```

### 4. Firebase Setup (for Push Notifications)
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a project
3. Go to **Project Settings > Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase-service-account.json` in the project root

### 5. Start Server
```bash
npm run dev    # Development with auto-reload
npm start      # Production
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register-device` | Register a laptop agent, returns PIN |
| POST | `/api/auth/pair-device` | Pair device with PIN, returns JWT |
| POST | `/api/auth/viewer-login` | Mobile viewer login with PIN |
| POST | `/api/auth/register-fcm` | Register FCM token for push |
| GET | `/api/devices/:id` | Get device info |
| GET | `/api/devices/:id/logs` | Get activity logs |
| GET | `/api/devices/:id/emails` | Get email alerts |
| GET | `/api/health` | Health check |

## WebSocket Namespaces
- `/agent` - Laptop agents connect here
- `/viewer` - Mobile apps connect here

## Deployment
For production, use a reverse proxy like Nginx and run with `pm2`:
```bash
npm install -g pm2
pm2 start src/index.js --name device-monitor
```
