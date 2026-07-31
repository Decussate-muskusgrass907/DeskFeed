const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
const { prisma } = require('../services/database');
const logger = require('../services/logger');

// Laptop Agent: register and get pairing PIN
router.post('/register-device', async (req, res) => {
  try {
    const { name } = req.body;
    if (!name) {
      return res.status(400).json({ error: 'Device name is required' });
    }

    const pairingPin = Math.floor(100000 + Math.random() * 900000).toString();
    const device = await prisma.device.create({
      data: { name, pairingPin },
    });

    logger.info(`Device registered: ${name} (PIN: ${pairingPin})`);

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
router.post('/register-fcm', async (req, res) => {
  try {
    const { deviceId, fcmToken } = req.body;
    if (!deviceId || !fcmToken) {
      return res.status(400).json({ error: 'Device ID and FCM token required' });
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
