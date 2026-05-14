'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';

export function useSync(onMessage: (event: any) => void) {
  const { status } = useSession();

  useEffect(() => {
    if (status !== 'authenticated') return;

    let eventSource: EventSource;

    const connect = () => {
      eventSource = new EventSource('/api/sync');

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (e) {
          console.error('SSE Parse Error:', e);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE Connection Error:', err);
        eventSource.close();
        // Reconnect after 5 seconds
        setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      if (eventSource) eventSource.close();
    };
  }, [status, onMessage]);
}
