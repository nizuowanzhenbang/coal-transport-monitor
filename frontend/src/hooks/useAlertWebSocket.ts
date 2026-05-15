import { useEffect, useRef, useCallback } from 'react';
import { WsMessage } from '../types';

interface Options {
  token: string | null;
  onNewAlert?: (data: WsMessage & { type: 'new_alert' }) => void;
  enabled?: boolean;
}

/**
 * 连接后端 WebSocket 实时预警推送。
 * 自动重连（指数退避，最长 30 秒），页面 focus 时立即重连。
 */
export function useAlertWebSocket({ token, onNewAlert, enabled = true }: Options) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryDelay = useRef(1000);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmounted = useRef(false);

  const connect = useCallback(() => {
    if (!token || !enabled || unmounted.current) return;

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${protocol}://${location.host}/api/ws/alerts?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      retryDelay.current = 1000;
    };

    ws.onmessage = (ev) => {
      try {
        const msg: WsMessage = JSON.parse(ev.data);
        if (msg.type === 'new_alert' && onNewAlert) {
          onNewAlert(msg as WsMessage & { type: 'new_alert' });
        } else if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
        }
      } catch {
        // ignore non-JSON frames
      }
    };

    ws.onclose = () => {
      if (unmounted.current) return;
      retryTimer.current = setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30000);
        connect();
      }, retryDelay.current);
    };
  }, [token, enabled, onNewAlert]);

  useEffect(() => {
    unmounted.current = false;
    connect();

    const handleFocus = () => {
      if (wsRef.current?.readyState === WebSocket.CLOSED) connect();
    };
    window.addEventListener('focus', handleFocus);

    return () => {
      unmounted.current = true;
      window.removeEventListener('focus', handleFocus);
      if (retryTimer.current) clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
