const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
const { prisma } = require('../services/database');
const logger = require('../services/logger');
const { authenticate } = require('../middleware/auth');

const PIN_TTL_MS = 10 * 60 * 1000; // 10 minutes
const MAX_ATTEMPTS = 5;
const RATE_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

const attemptStore = new Map();

function checkRateLimit(key) {
  const now = Date.now();
  const entry = attemptStore.get(key) || { count: 0, resetAt: now + RATE_WINDOW_MS };
  if (entry.resetAt <= now) {
    entry.count = 0;
    entry.resetAt = now + RATE_WINDOW_MS;
  }
  entry.count += 1;
  attemptStore.set(key, entry);
  const remaining = Math.max(0, MAX_ATTEMPTS - entry.count);
  return { allowed: entry.count <= MAX_ATTEMPTS, remaining };
}

function isPinExpired(device) {
  if (!device.pairingPinExpiresAt) return true;
  return Date.now() > new Date(device.pairingPinExpiresAt).getTime();
}

// Laptop Agent: register and get pairing PIN
router.post('/register-device', async (req, res) => {
  try {
    const { name } = req.body;
    if (!name) {
      return res.status(400).json({ error: 'Device name is required' });
    }

    const pairingPin = Math.floor(100000 + Math.random() * 900000).toString();
    const device = await prisma.device.create({
      data: {
        name,
        pairingPin,
        pairingPinExpiresAt: new Date(Date.now() + PIN_TTL_MS),
      },
    });

    logger.info(`Device registered: ${name} (${device.id})`);

    res.json({
      deviceId: device.id,
      pairingPin,
      message: 'Use this PIN to pair within 10 minutes',
    });
  } catch (err) {
    logger.error('Register device failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Laptop Agent: verify pairing and get JWT
router.post('/pair-device', async (req, res) => {
  try {
    const { deviceId, pairingPin } = req.body;
    if (!deviceId || !pairingPin) {
      return res.status(400).json({ error: 'Device ID and PIN required' });
    }

    const device = await prisma.device.findUnique({ where: { id: deviceId } });
    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }

    const rate = checkRateLimit(`pair:${deviceId}`);
    if (!rate.allowed) {
      return res.status(429).json({ error: 'Too many attempts. Try again later.' });
    }

    if (device.isPaired) {
      return res.status(403).json({ error: 'Device is already paired' });
    }

    if (isPinExpired(device)) {
      return res.status(401).json({ error: 'Pairing PIN has expired. Register the device again.' });
    }

    if (device.pairingPin !== pairingPin) {
      return res.status(401).json({ error: 'Invalid pairing PIN' });
    }

    await prisma.device.update({
      where: { id: deviceId },
      data: { isPaired: true },
    });

    const agentToken = jwt.sign(
      { deviceId: device.id, deviceName: device.name, role: 'agent' },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRY || '30d' }
    );

    logger.info(`Device paired: ${device.name}`);

    res.json({ token: agentToken, deviceId: device.id });
  } catch (err) {
    logger.error('Pair device failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Mobile Viewer: login with PIN (no email/password needed for simplicity)
router.post('/viewer-login', async (req, res) => {
  try {
    const { deviceId, pairingPin } = req.body;
    if (!deviceId || !pairingPin) {
      return res.status(400).json({ error: 'Device ID and PIN required' });
    }

    const device = await prisma.device.findUnique({ where: { id: deviceId } });
    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }

    const rate = checkRateLimit(`viewer:${deviceId}`);
    if (!rate.allowed) {
      return res.status(429).json({ error: 'Too many attempts. Try again later.' });
    }

    if (isPinExpired(device)) {
      return res.status(401).json({ error: 'Pairing PIN has expired. Register the device again.' });
    }

    if (device.pairingPin !== pairingPin) {
      return res.status(401).json({ error: 'Invalid pairing PIN' });
    }

    const viewerToken = jwt.sign(
      { deviceId: device.id, userId: uuidv4(), role: 'viewer' },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRY || '30d' }
    );

    res.json({ token: viewerToken, deviceName: device.name });
  } catch (err) {
    logger.error('Viewer login failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Mobile Viewer: register FCM token for push notifications
router.post('/register-fcm', authenticate, async (req, res) => {
  try {
    const { deviceId, fcmToken } = req.body;
    if (!deviceId || !fcmToken) {
      return res.status(400).json({ error: 'Device ID and FCM token required' });
    }
    if (req.user.deviceId !== deviceId) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    await prisma.device.update({
      where: { id: deviceId },
      data: { fcmToken },
    });

    logger.info(`FCM token registered for device ${deviceId}`);
    res.json({ success: true });
  } catch (err) {
    logger.error('FCM registration failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
