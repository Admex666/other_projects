-- Migration 00008: Enable REPLICA IDENTITY FULL a Realtime UPDATE eseményekhez
-- Supabase postgres_changes Realtime UPDATE-hez szükséges, hogy a kliensek megkapják a payload.new teljes adatát.

ALTER TABLE public.games REPLICA IDENTITY FULL;
ALTER TABLE public.rooms REPLICA IDENTITY FULL;
ALTER TABLE public.tricks REPLICA IDENTITY FULL;
