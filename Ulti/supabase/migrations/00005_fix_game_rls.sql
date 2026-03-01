-- Supabase Migration: 00005_fix_game_rls.sql
-- Cél: Lehetővé tenni a szobagazdának a játék inicializálását (INSERT) és a játékosoknak a módosításokat (UPDATE).

-- 1. Engedélyezzük a beszúrást a szobagazdának
CREATE POLICY "Host can insert game" ON public.games FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.rooms r 
        WHERE r.id = room_id AND auth.uid() = r.player1_id
    )
);

-- 2. Engedélyezzük a módosítást a játékosoknak
CREATE POLICY "Players can update game" ON public.games FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM public.rooms r 
        WHERE r.id = games.room_id AND (
            auth.uid() = r.player1_id OR 
            auth.uid() = r.player2_id OR 
            auth.uid() = r.player3_id
        )
    )
);
