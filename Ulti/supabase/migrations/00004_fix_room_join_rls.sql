-- Supabase Migration: 00004_fix_room_join_rls.sql
-- Cél: Lehetővé tenni, hogy a 'waiting' státuszú szobákhoz új játékos is csatlakozhasson (frissíthesse a player2 vagy player3 mezőt).

-- Töröljük a túlságosan szigorú szabályt
DROP POLICY IF EXISTS "Players in the room can update it." ON public.rooms;

-- Új szabály: A szoba tagjai BÁRMIT módosíthatnak, VAGY bárki csatlakozhat (módosíthatja) a szobát, ha az még 'waiting' állapotban van.
CREATE POLICY "Players can update or join rooms" ON public.rooms FOR UPDATE USING (
    auth.uid() = player1_id OR 
    auth.uid() = player2_id OR 
    auth.uid() = player3_id OR 
    status = 'waiting'
);
