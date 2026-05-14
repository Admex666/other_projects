import { getServerSession } from 'next-auth';
import { authOptions } from '../auth/[...nextauth]/route';
import { syncEmitter } from '@/lib/sync-emitter';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  const session = await getServerSession(authOptions);
  if (!session || !(session.user as any).id) {
    return new Response('Unauthorized', { status: 401 });
  }

  const userId = (session.user as any).id;

  const responseStream = new TransformStream();
  const writer = responseStream.writable.getWriter();
  const encoder = new TextEncoder();

  // Keep-alive interval
  const keepAlive = setInterval(async () => {
    try {
      await writer.write(encoder.encode(': keep-alive\n\n'));
    } catch (e) {
      clearInterval(keepAlive);
    }
  }, 30000);

  // Listener for events
  const onSync = async (eventData: any) => {
    // Only send if the event is relevant to this user
    // (e.g., they are an owner of the pocket or party in the debt)
    if (eventData.userIds.includes(userId)) {
      try {
        await writer.write(encoder.encode(`data: ${JSON.stringify(eventData)}\n\n`));
      } catch (e) {
        syncEmitter.off('sync', onSync);
      }
    }
  };

  syncEmitter.on('sync', onSync);

  // Clean up on close
  req.signal.addEventListener('abort', () => {
    clearInterval(keepAlive);
    syncEmitter.off('sync', onSync);
    writer.close();
  });

  return new Response(responseStream.readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
    },
  });
}
