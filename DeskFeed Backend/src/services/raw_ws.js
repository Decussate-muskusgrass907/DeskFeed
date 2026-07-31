const { WebSocketServer } = require('ws');
const jwt = require('jsonwebtoken');
const url = require('url');
const logger = require('./logger');
const { prisma } = require('./database');

function setupRawWebSocket(server, io) {
  const wss = new WebSocketServer({ noServer: true });

  // Bridge Socket.IO events to raw WebSocket viewers
  // (Python agent uses Socket.IO, mobile app uses raw WS — this connects them)
  if (io) {
    io.of('/agent').on('connection', (socket) => {
      socket.on('activity:log', async (data) => {
        const deviceId = socket.deviceId;
        const deviceName = socket.deviceName || 'Unknown';
        broadcastTo(viewerClients(), deviceId, {
          type: 'activity:update',
          deviceId,
          deviceName,
          ...data,
        });
      });
      socket.on('email:alert', async (data) => {
        broadcastTo(viewerClients(), socket.deviceId, {
          type: 'email:alert',
          deviceId: socket.deviceId,
          deviceName: socket.deviceName || 'Unknown',
          ...data,
        });
      });
      socket.on('stream:video', (data) => {
        broadcastTo(viewerClients(), socket.deviceId, { type: 'stream:video', ...data });
      });
      socket.on('stream:audio', (data) => {
        broadcastTo(viewerClients(), socket.deviceId, { type: 'stream:audio', ...data });
      });
    });
  }

  server.on('upgrade', (request, socket, head) => {
    const pathname = url.parse(request.url).pathname;
    if (pathname === '/viewer-ws' || pathname === '/agent-ws') {
      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request, pathname);
      });
    } else {
      socket.destroy();
    }
  });

  wss.on('connection', (ws, request, pathname) => {
    ws._pathname = pathname;

    const authHeader = request.headers['authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      ws.close(4001, 'Auth required');
      return;
    }

    const token = authHeader.split(' ')[1];
    let decoded;
    try {
      decoded = jwt.verify(token, process.env.JWT_SECRET);
    } catch (err) {
      ws.close(4001, 'Invalid token');
      return;
    }

    ws.deviceId = decoded.deviceId;

    if (pathname === '/viewer-ws') {
      logger.info(`Viewer connected: ${decoded.deviceId}`);

      ws.on('message', (raw) => {
        try {
          const data = JSON.parse(raw.toString());
          const type = data.type;
          if (type === 'stream:request' || type === 'stream:stop') {
            logger.info(`Viewer ${decoded.deviceId} -> ${type}`);
            broadcastTo(agentClients(), decoded.deviceId, data);
            if (io) {
              const ns = io.of('/agent');
              logger.info(`Agent namespace sockets: ${ns.sockets.size}`);
              ns.to(`device:${decoded.deviceId}`).emit(type);
              io.of('/agent').emit(type);
              logger.info(`Forwarded ${type} (broadcast + room)`);
            }
          }
        } catch (e) {
          logger.error(`Viewer msg error: ${e.message}`);
        }
      });
    } else if (pathname === '/agent-ws') {
      logger.info(`Agent connected: ${decoded.deviceId}`);

      ws.on('message', async (raw) => {
        try {
          const data = JSON.parse(raw.toString());
          const type = data.type;

          if (type === 'activity:log') {
            await prisma.activityLog.create({
              data: {
                deviceId: decoded.deviceId,
                appName: data.appName || null,
                browserUrl: data.browserUrl || null,
                folderPath: data.folderPath || null,
                windowTitle: data.windowTitle || null,
                timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
              },
            });
            broadcastTo(viewerClients(), decoded.deviceId, { type: 'activity:update', ...data });
          } else if (type === 'email:alert') {
            await prisma.emailAlert.create({
              data: {
                deviceId: decoded.deviceId,
                subject: data.subject,
                sender: data.sender,
                receivedAt: data.timestamp ? new Date(data.timestamp) : new Date(),
              },
            });
            broadcastTo(viewerClients(), decoded.deviceId, { type: 'email:alert', ...data });
          } else if (type === 'stream:video' || type === 'stream:audio') {
            broadcastTo(viewerClients(), decoded.deviceId, { type, ...data });
          }
        } catch (e) {
          logger.error(`Agent msg error: ${e.message}`);
        }
      });
    }

    ws.on('close', () => {
      logger.info(`${pathname} disconnected: ${decoded.deviceId}`);
    });
  });

  function agentClients() {
    return [...wss.clients].filter(c => c.readyState === 1 && c._pathname === '/agent-ws');
  }

  function viewerClients() {
    return [...wss.clients].filter(c => c.readyState === 1 && c._pathname === '/viewer-ws');
  }

  function broadcastTo(clients, deviceId, message) {
    const json = JSON.stringify(message);
    clients.filter(c => c.deviceId === deviceId).forEach(c => c.send(json));
  }

  logger.info('Raw WS ready: /viewer-ws and /agent-ws');
}

module.exports = { setupRawWebSocket };
