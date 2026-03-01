-- Supabase Migration: 00006_fix_game_rls_select.sql
-- Cél: Teljeskörű RLS hozzáférés megadása az aktív játékosoknak, és a SELECT engedélyezése az asztal betöltéséhez, miközben mindenki a saját kliensét futtatja.

-- 1. Engedélyezzük a játék lekérdezését (SELECT) az API és a Kliens számára.
-- Most minden publikus játék állapotot megosztunk, mivel az appot elsősorban kliens futtatja (és a hands biztonságosan van kezelve egyelőre az inicializáláskor).
DROP POLICY IF EXISTS "Players in the room can view the game." ON public.games;

CREATE POLICY "Games are viewable by everyone." ON public.games FOR SELECT USING (true);
