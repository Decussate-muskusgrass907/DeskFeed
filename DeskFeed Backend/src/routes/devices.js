const express = require('express');
const router = express.Router();
const { prisma } = require('../services/database');
const { authenticate } = require('../middleware/auth');
const logger = require('../services/logger');

function assertOwnership(req, res) {
  if (req.user.deviceId !== req.params.deviceId) {
    res.status(403).json({ error: 'Forbidden' });
    return false;
  }
  return true;
}

// Get device info
router.get('/:deviceId', authenticate, async (req, res) => {
  try {
    if (!assertOwnership(req, res)) return;
    const device = await prisma.device.findUnique({
      where: { id: req.params.deviceId },
      select: {
        id: true,
        name: true,
        isPaired: true,
        lastSeen: true,
      },
    });

    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }

    res.json(device);
  } catch (err) {
    logger.error('Get device failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get activity logs
router.get('/:deviceId/logs', authenticate, async (req, res) => {
  try {
    if (!assertOwnership(req, res)) return;
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const logs = await prisma.activityLog.findMany({
      where: { deviceId: req.params.deviceId },
      orderBy: { timestamp: 'desc' },
      take: limit,
    });

    res.json(logs);
  } catch (err) {
    logger.error('Get logs failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get email alerts
router.get('/:deviceId/emails', authenticate, async (req, res) => {
  try {
    if (!assertOwnership(req, res)) return;
    const limit = Math.min(parseInt(req.query.limit) || 50, 200);
    const alerts = await prisma.emailAlert.findMany({
      where: { deviceId: req.params.deviceId },
      orderBy: { receivedAt: 'desc' },
      take: limit,
    });

    res.json(alerts);
  } catch (err) {
    logger.error('Get emails failed:', err.message);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
