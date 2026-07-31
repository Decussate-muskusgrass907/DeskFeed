const jwt = require('jsonwebtoken');
const logger = require('./logger');
const { prisma } = require('./database');
const { sendPushToDevice } = require('./firebase');

function authenticateSocket(token) {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (err) {
    return null;
  }
}

function setupWebSocketHandlers(io) {
  // Namespace for laptop agents
  const agentNamespace = io.of('/agent');
  // Namespace for mobile viewers
  const viewerNamespace = io.of('/viewer');

  // --- Laptop Agent ---
  agentNamespace.use((socket, next) => {
    const token = socket.handshake.auth.token;
    const decoded = authenticateSocket(token);
    if (!decoded) {
      return next(new Error('Authentication failed'));
    }
    socket.deviceId = decoded.deviceId;
    socket.deviceName = decoded.deviceName || 'Unknown';
    next();
  });

  agentNamespace.on('connection', (socket) => {
    const deviceId = socket.deviceId;
    logger.info(`Agent connected: ${socket.deviceName} (${deviceId})`);

    // Join a room specific to this device
    socket.join(`device:${deviceId}`);

    // Update last seen
    prisma.device.update({
      where: { id: deviceId },
      data: { lastSeen: new Date() },
    }).catch((err) => logger.error('Update lastSeen failed:', err.message));

    // Activity log
    socket.on('activity:log', async (data) => {
      try {
        await prisma.activityLog.create({
          data: {
            deviceId,
            appName: data.appName || null,
            browserUrl: data.browserUrl || null,
            folderPath: data.folderPath || null,
            windowTitle: data.windowTitle || null,
            timestamp: new Date(data.timestamp) || new Date(),
          },
        });

        // Relay to viewers
        io.of('/viewer').to(`device:${deviceId}`).emit('activity:update', {
          deviceId,
          deviceName: socket.deviceName,
          ...data,
        });
      } catch (err) {
        logger.error('Failed to save activity log:', err.message);
      }
    });

    // Email alert
    socket.on('email:alert', async (data) => {
      try {
        await prisma.emailAlert.create({
          data: {
            deviceId,
            subject: data.subject,
            sender: data.sender,
            receivedAt: new Date(data.timestamp) || new Date(),
          },
        });

        const alertPayload = {
          deviceId,
          deviceName: socket.deviceName,
          subject: data.subject,
          sender: data.sender,
          timestamp: data.timestamp || new Date().toISOString(),
        };

        // Push notification via FCM
        const device = await prisma.device.findUnique({ where: { id: deviceId } });
        if (device && device.fcmToken) {
          await sendPushToDevice(deviceId, {
            title: `📧 ${data.subject.substring(0, 80)}`,
            body: `From: ${data.sender}`,
            data: {
              type: 'email_alert',
              ...alertPayload,
            },
          });
        }

        // Also relay to connected viewers
        io.of('/viewer').to(`device:${deviceId}`).emit('email:alert', alertPayload);
      } catch (err) {
        logger.error('Failed to process email alert:', err.message);
      }
    });

    // WebRTC signaling
    socket.on('webrtc:offer', (data) => {
      socket.to(`device:${deviceId}`).emit('webrtc:offer', {
        sdp: data.sdp,
        from: deviceId,
      });
    });

    socket.on('webrtc:answer', (data) => {
      socket.to(`device:${deviceId}`).emit('webrtc:answer', {
        sdp: data.sdp,
        from: deviceId,
      });
    });

    socket.on('webrtc:ice-candidate', (data) => {
      socket.to(`device:${deviceId}`).emit('webrtc:ice-candidate', {
        candidate: data.candidate,
        from: deviceId,
      });
    });

    // Request camera/mic stream
    socket.on('stream:request', () => {
      // This is usually sent from viewer to agent, but we handle it if needed
      io.of('/agent').to(`device:${deviceId}`).emit('stream:request');
    });

    socket.on('stream:stop', () => {
      io.of('/agent').to(`device:${deviceId}`).emit('stream:stop');
    });

    // Handle stream data from agent and relay to viewer
    socket.on('stream:video', (data) => {
      io.of('/viewer').to(`device:${deviceId}`).emit('stream:video', data);
    });

    socket.on('stream:audio', (data) => {
      io.of('/viewer').to(`device:${deviceId}`).emit('stream:audio', data);
    });

    socket.on('disconnect', () => {
      logger.info(`Agent disconnected: ${socket.deviceName} (${deviceId})`);
    });
  });

  // --- Mobile Viewer ---
  viewerNamespace.use((socket, next) => {
    const token = socket.handshake.auth.token;
    const decoded = authenticateSocket(token);
    if (!decoded) {
      return next(new Error('Authentication failed'));
    }
    socket.deviceId = decoded.deviceId;
    socket.userId = decoded.userId;
    next();
  });

  viewerNamespace.on('connection', (socket) => {
    const deviceId = socket.deviceId;
    logger.info(`Viewer connected for device: ${deviceId}`);

    socket.join(`device:${deviceId}`);

    // Request activity history (last 100 entries)
    socket.on('history:activity', async (callback) => {
      try {
        const logs = await prisma.activityLog.findMany({
          where: { deviceId },
          orderBy: { timestamp: 'desc' },
          take: 100,
        });
        callback(logs);
      } catch (err) {
        logger.error('Failed to fetch activity history:', err.message);
        callback([]);
      }
    });

    // Request email history (last 50 entries)
    socket.on('history:emails', async (callback) => {
      try {
        const alerts = await prisma.emailAlert.findMany({
          where: { deviceId },
          orderBy: { receivedAt: 'desc' },
          take: 50,
        });
        callback(alerts);
      } catch (err) {
        logger.error('Failed to fetch email history:', err.message);
        callback([]);
      }
    });

    // Request live stream
    socket.on('stream:request', () => {
      io.of('/agent').to(`device:${deviceId}`).emit('stream:request');
    });

    socket.on('stream:stop', () => {
      io.of('/agent').to(`device:${deviceId}`).emit('stream:stop');
    });

    // WebRTC (viewer acts as initiator)
    socket.on('webrtc:offer', (data) => {
      io.of('/agent').to(`device:${deviceId}`).emit('webrtc:offer', {
        sdp: data.sdp,
        from: 'viewer',
      });
    });

    socket.on('webrtc:answer', (data) => {
      io.of('/agent').to(`device:${deviceId}`).emit('webrtc:answer', {
        sdp: data.sdp,
        from: 'viewer',
      });
    });

    socket.on('webrtc:ice-candidate', (data) => {
      io.of('/agent').to(`device:${deviceId}`).emit('webrtc:ice-candidate', {
        candidate: data.candidate,
        from: 'viewer',
      });
    });

    socket.on('disconnect', () => {
      logger.info(`Viewer disconnected for device: ${deviceId}`);
    });
  });
}

module.exports = { setupWebSocketHandlers };
