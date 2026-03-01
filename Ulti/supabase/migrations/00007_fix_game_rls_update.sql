-- Supabase Migration: 00007_fix_game_rls_update.sql
-- Cél: Az UPDATE művelet teljeskörű feloldása a 'games' táblán, hogy a Next.js API route-ok garantáltan tudják frissíteni a játék állapotát (Bid & Play), mivel a szerver eleve validálja a kérést az autentikációs token (user.id) és a játékszabályok alapján, mielőtt az adatbázishoz nyúlna.

DROP POLICY IF EXISTS "Players can update game" ON public.games;

-- A Next.js API Route Supabase kliense authentikáltként (Anon + user token) hívja, adjunk UPDATE jogot az auth usereknek:
CREATE POLICY "Authenticated users can update game" ON public.games FOR UPDATE USING (auth.role() = 'authenticated');
