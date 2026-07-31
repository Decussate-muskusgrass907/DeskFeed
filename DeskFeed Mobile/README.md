# DeskFeed Mobile - Android Viewer

## Prerequisites
- Flutter SDK 3.16+
- Android Studio
- Firebase project (for FCM push notifications)

## Setup

### 1. Firebase Configuration
1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Add an **Android app** to the project
3. Package name: `com.deskfeed.mobile`
4. Download `google-services.json` and place it in:
   `android/app/google-services.json`
5. Enable **Firebase Cloud Messaging** in the console

### 2. Configure Server
Edit `lib/services/auth_service.dart` and `lib/services/websocket_service.dart`:
```dart
static const String _baseUrl = 'http://YOUR_SERVER_IP:3000';
static const String _wsUrl = 'ws://YOUR_SERVER_IP:3000';
```

### 3. Android Permissions
Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
```

### 4. Run
```bash
flutter pub get
flutter run
```

### 5. Build APK
```bash
flutter build apk --release
```
APK will be at `build/app/outputs/flutter-apk/app-release.apk`

## Features
- **Dashboard**: Real-time activity feed with browser URLs, folder paths, app names
- **Live View**: Webcam stream from laptop (toggle start/stop)
- **Push Alerts**: Instant FCM notifications for Outlook emails
- **Pairing**: 6-digit PIN-based secure device pairing

## Troubleshooting
- **WebSocket won't connect**: Ensure the server IP is reachable from the phone (same network or public IP)
- **No push notifications**: Verify FCM token registration in server logs
- **No video stream**: Check that the laptop agent is running and has webcam access
