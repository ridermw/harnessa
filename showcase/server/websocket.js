const { Server } = require('socket.io');

let io = null;

function setupWebSocket(server) {
  io = new Server(server, {
    cors: {
      origin: ['http://localhost:5173', 'http://localhost:3001'],
      methods: ['GET', 'POST'],
    },
  });

  io.on('connection', (socket) => {
    console.log(`Client connected: ${socket.id}`);

    socket.on('disconnect', () => {
      console.log(`Client disconnected: ${socket.id}`);
    });
  });

  return io;
}

function getIO() {
  return io;
}

function broadcast(event, data) {
  if (io) {
    io.emit(event, data);
  }
}

module.exports = { setupWebSocket, getIO, broadcast };
