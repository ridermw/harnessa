import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

let socket = null;

export default function useSocket() {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!socket) {
      const url = window.location.hostname === 'localhost' && window.location.port === '5173'
        ? 'http://localhost:3001'
        : undefined;
      socket = io(url, { transports: ['websocket', 'polling'] });
    }

    function onConnect() {
      setConnected(true);
    }
    function onDisconnect() {
      setConnected(false);
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    if (socket.connected) setConnected(true);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, []);

  return socket;
}
