const admin = require('firebase-admin');
const path = require('path');
const logger = require('./logger');

let firebaseApp = null;

function initializeFirebase() {
  const serviceAccountPath = process.env.FIREBASE_SERVICE_ACCOUNT_PATH;
  if (!serviceAccountPath) {
    logger.warn('FIREBASE_SERVICE_ACCOUNT_PATH not set — FCM notifications disabled');
    return;
  }

  try {
    const resolvedPath = path.resolve(serviceAccountPath);
    firebaseApp = admin.initializeApp({
      credential: admin.credential.cert(resolvedPath),
    });
    logger.info('Firebase initialized successfully');
  } catch (err) {
    logger.error('Failed to initialize Firebase:', err.message);
  }
}

async function sendPushNotification(fcmToken, payload) {
  if (!firebaseApp) {
    logger.warn('Firebase not initialized — cannot send push');
    return;
  }

  if (!fcmToken) {
    logger.warn('No FCM token provided — skipping push');
    return;
  }

  const message = {
    token: fcmToken,
    notification: {
      title: payload.title || 'Device Alert',
      body: payload.body || '',
    },
    data: payload.data || {},
    android: {
      priority: 'high',
      notification: {
        channelId: 'email_alerts',
        priority: 'high',
        sound: 'default',
      },
    },
  };

  try {
    const response = await admin.messaging().send(message);
    logger.info(`FCM sent successfully: ${response}`);
    return response;
  } catch (err) {
    logger.error('FCM send failed:', err.message);
    throw err;
  }
}

async function sendPushToDevice(deviceId, payload) {
  const { prisma } = require('./database');
  const device = await prisma.device.findUnique({ where: { id: deviceId } });
  if (!device || !device.fcmToken) {
    logger.warn(`No FCM token for device ${deviceId}`);
    return;
  }
  return sendPushNotification(device.fcmToken, payload);
}

module.exports = { initializeFirebase, sendPushNotification, sendPushToDevice };
