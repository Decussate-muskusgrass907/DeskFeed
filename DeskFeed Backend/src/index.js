require('dotenv').config();
const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
const logger = require('./services/logger');
const { setupWebSocketHandlers } = require('./services/websocket');
const { setupRawWebSocket } = require('./services/raw_ws');
const { initializeFirebase } = require('./services/firebase');
const { prisma } = require('./services/database');

const app = express();
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST'],
  },
  pingTimeout: 60000,
  pingInterval: 25000,
});

app.use(cors());
app.use(express.json({ limit: '10mb' }));

app.use('/api/auth', require('./routes/auth'));
app.use('/api/devices', require('./routes/devices'));

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

setupWebSocketHandlers(io);
setupRawWebSocket(server, io);

initializeFirebase();

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`);
});

process.on('SIGTERM', async () => {
  await prisma.$disconnect();
  process.exit(0);
});
